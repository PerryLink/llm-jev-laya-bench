"""The model host: one warm model, serialised, with everything Laya leaves out.

This is the component that makes the difference between a script and a service.
It owns exactly one :class:`laya.Router` for the life of the process, and it
supplies the five things Laya does not:

**Warmth.** ``Router`` with ``preload`` keeps every checkpoint resident. The
alternative is Laya's default, ``max_loaded=1``, where alternating languages
rebuilds a model on every request - measured upstream at a 7.4 s median reload on
CPU and 10.3 s on a T4.

**Serialisation.** Laya is not thread-safe. ``Agent.system_one`` reassigns
``self.device`` and ``self.dtype`` and calls ``self.model.to(...)`` when it hits
an OOM, and it mutates ``self.cfg`` reads on every call. Concurrent calls can
therefore race a device move against a forward pass. A lock is not optional
politeness here; it is correctness. The default is one forward pass at a time.

**Preflight.** Every request is planned and validated before it reaches the
model, so a caller is told what would be truncated and which question is too
large, rather than receiving a confident answer about a fragment.

**Device honesty.** Laya catches a CUDA OOM and permanently demotes itself to
CPU in fp32, printing to stdout, with no flag set anywhere. This class watches
for that and reports it, so a client is never silently served answers an order of
magnitude slower than the ones it benchmarked.

**Structured failure.** A bare ``KeyError`` from Laya becomes a
:class:`~laya_mcp.errors.LayaMcpError` with a code, the offending question id,
and a hint.

**Lifecycle.** ``stop()`` releases the model and empties the CUDA cache, which
``Router.unload`` does not do. Issue #52 upstream is a long-running MLX sidecar
that grew to 21.7 GB; a service that cannot be recycled cleanly is a service that
eventually has to be killed.
"""

from __future__ import annotations

import gc
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from .calibration import CalibrationEntry, CalibrationStore, apply_temperature
from .capability import (
    Capability,
    find_model_root,
    normalise_checkpoint,
    read_capability,
)
from .errors import (
    CapacityError,
    DeviceDegradedError,
    InvalidQuestionError,
    LayaMcpError,
    OutOfMemoryError,
    StateTruncatedError,
    UnknownModelError,
    translate,
)
from .planning import BudgetPlan, plan_questions, script_caveat
from .protocol import (
    NEUTRAL_LABELS,
    Answer,
    AskRequest,
    AskResponse,
    Question,
    RoutingInfo,
    Usage,
    noul_as_choice,
    noul_has_option_text,
)
from .validate import validate_questions

log = logging.getLogger("laya_mcp.worker")

#: Where a fitted calibration store lives by default, under the user's config dir.
DEFAULT_CALIBRATION_FILENAME = "calibration.json"

#: Where checkpoints are snapshotted when a local root is not supplied. Kept
#: beside the user's cache rather than inside the package, because a checkpoint is
#: around 650 MB and the package may be installed into a read-only prefix.
DEFAULT_MODEL_DIRNAME = "laya-mcp-models"


def _band(probability: float) -> str:
    """Place a ``noul`` probability in a band.

    The boundaries are the ones the ecosystem's own self-consistency guidance
    uses: ``no`` below 0.30, ``uncertain`` from 0.30 through 0.70 inclusive,
    ``yes`` above 0.70. Both boundaries belong to ``uncertain``, because a
    probability sitting exactly on a threshold is the case the band exists to
    describe as unclear.

    This is reported *alongside* the raw probability, never instead of it: a
    calibrated probability is not a decision, and 0.51 rendered as a settled
    ``true`` invites a caller to branch on a coin toss.
    """
    if probability < 0.30:
        return "no"
    if probability > 0.70:
        return "yes"
    return "uncertain"


#: Whether the left-truncation patch has been applied in this process. The rebind
#: is process-wide, so applying it twice would wrap the wrapper.
_LEFT_TRUNCATION_PATCHED = False


def _enable_left_truncation() -> None:
    """Make Laya keep the tail of an oversized state instead of its head.

    ``build_sequence`` already takes ``truncate_left`` and already implements it
    (``st[-room:] if truncate_left else st[:room]``). Nothing needs writing. The
    problem is that it cannot be asked for: ``Agent.system_one`` calls

        build_sequence(self.tok, state, q, max_len, head_max_len)

    and stops, so the flag never leaves its default. Upstream PR #112 notices the
    same thing from the other side, describing the bug it fixes as affecting "only
    direct callers" - because through ``Agent`` there are no direct callers.

    So this rebinds the name ``laya.agent`` imported. Three properties matter and
    all three are deliberate:

    * the *original* function still does all the work, so a fix landing upstream is
      picked up unchanged and this keeps working whether or not #112 merges;
    * only the one argument a caller cannot supply is injected - an explicit
      positional ``truncate_left`` still wins, so this cannot silently override a
      caller that did find a way to pass it;
    * it is process-wide and applied once, which is correct here because a sidecar
      hosts exactly one configuration, and is why this is a sidecar flag rather
      than something a request may toggle.
    """
    global _LEFT_TRUNCATION_PATCHED
    if _LEFT_TRUNCATION_PATCHED:
        return

    from laya import agent as laya_agent

    original = laya_agent.build_sequence

    def build_sequence(*args: Any, **kwargs: Any) -> Any:
        # Position 7 is `truncate_left` in
        # `build_sequence(tok, state, q, max_len, head_max_len, option_order, truncate_left)`.
        if len(args) < 7:
            kwargs["truncate_left"] = True
        return original(*args, **kwargs)

    laya_agent.build_sequence = build_sequence
    _LEFT_TRUNCATION_PATCHED = True
    log.info(
        "truncate_left is on: an oversized state keeps its tail. `build_sequence` is "
        "rebound in laya.agent because `Agent.system_one` does not forward the flag."
    )


@dataclass
class WorkerConfig:
    """How to host the model.

    Defaults are chosen to be safe rather than fast, and each one is a decision
    recorded here rather than buried in a call site.
    """

    model: str = "english"
    also: tuple[str, ...] = ()
    device: Optional[str] = None
    model_root: Optional[str] = None
    max_len: Optional[int] = None
    head_max_len: Optional[int] = None
    calibration_path: Optional[str] = None
    #: Forward passes allowed at once. 1 is the only value Laya is safe with; the
    #: knob exists because a deployment with several GPUs and one process per GPU
    #: may legitimately want otherwise, and because it makes the constraint visible.
    concurrency: int = 1
    #: When true, a request whose state would be truncated is refused rather than
    #: answered. Off by default: answering and reporting is more useful than
    #: refusing, and the report is what makes the answer interpretable.
    strict: bool = False
    preload: bool = True
    #: Carry every noul as a two-option choice under neutral labels. On by default
    #: because the alternative is measured: as a noul, this checkpoint answers
    #: "false" to 40/40 items in both languages and scores exactly chance, while
    #: the same questions carried this way score 1.000 and 0.975.
    #:
    #: It is a workaround for a defect in the checkpoint, not a preference, so it
    #: is a knob: turn it off to see the raw primitive, or once upstream fixes it.
    noul_as_choice: bool = True
    #: Keep the state's *tail* when it does not fit, instead of its head.
    #:
    #: Laya truncates the state from the front (``st[:room]`` in ``build_sequence``),
    #: so the default loses the end of a long document - which for a contract, a log
    #: thread, or an email chain with the correction appended at the bottom is often
    #: exactly where the answer is. Measured on one 16 958-character state, a decoy
    #: code at the front and a correction at the back, same question both times:
    #: keeping the front scores the noul at **0.0706** ("no") because the model reads
    #: the decoy, and keeping the tail scores it **0.8341** ("yes") because it reads
    #: the correction. Which end survives is not a detail of the implementation; it
    #: decides the answer.
    #:
    #: Enabling it needs a small, deliberate patch, because the parameter cannot be
    #: reached from the public API at all: ``build_sequence`` accepts
    #: ``truncate_left``, and ``Agent.system_one`` calls it without forwarding it.
    #: See :func:`_enable_left_truncation`.
    truncate_left: bool = False


class LayaWorker:
    """Owns the model. One instance per process."""

    def __init__(self, config: Optional[WorkerConfig] = None) -> None:
        self.config = config or WorkerConfig()
        self._router: Any = None
        self._lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._loaded = False
        self._load_error: Optional[str] = None
        self._capabilities: dict[str, Capability] = {}
        self._degraded = False
        self._requested_device = self.config.device
        self._calibration = CalibrationStore(self.config.calibration_path)
        self._calls = 0
        self._failures = 0
        self._started_at: Optional[float] = None
        self._last_latency_ms = 0.0

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        """Load the model. Idempotent.

        Raises :class:`~laya_mcp.errors.ModelUnavailableError` if it cannot, so a
        supervisor learns at startup rather than on the first request.
        """
        with self._state_lock:
            if self._loaded:
                return
            if self._load_error is not None:
                raise translate(RuntimeError(self._load_error))
            try:
                self._load()
            except LayaMcpError:
                raise
            except Exception as exc:  # noqa: BLE001
                self._load_error = str(exc)
                raise translate(exc)
            self._loaded = True
            self._started_at = time.time()

    def _load(self) -> None:
        import laya  # imported here so `doctor` never pays for torch

        if self.config.truncate_left:
            _enable_left_truncation()

        wanted = [self.config.model, *self.config.also]
        normalised: list[str] = []
        for name in wanted:
            try:
                normalised.append(normalise_checkpoint(name))
            except KeyError as exc:
                raise UnknownModelError(
                    f"unknown checkpoint {name!r}",
                    hint="known checkpoints are english, multilingual and typed-decisions",
                    cause=exc,
                ) from exc

        # Deduplicate but keep order, so `--model english --also english` is not
        # an error and does not load twice.
        seen: list[str] = []
        for name in normalised:
            if name not in seen:
                seen.append(name)

        if self.config.model_root:
            # A local root bypasses the Hub entirely. Agent accepts either a repo
            # id or a directory, so passing the path is the whole change - but the
            # subfolder must then be resolved by us, because Agent joins it itself
            # and would double it.
            root = find_model_root(self.config.model_root)
            router = self._build_local_router(laya, root, seen)
        else:
            kwargs: dict[str, Any] = {}
            if self.config.device:
                kwargs["device"] = self.config.device
            router = laya.Router(preload=bool(self.config.preload), **kwargs)
            try:
                router.preload(seen)
            except Exception as exc:  # noqa: BLE001
                raise translate(exc) from exc

        self._router = router

        # Apply the token-budget overrides to every loaded agent. These are read
        # fresh on every `system_one` call, so setting them once at startup is
        # enough and setting them per request would be wasted work.
        for name in seen:
            try:
                agent = router.load(name)
            except Exception as exc:  # noqa: BLE001
                raise translate(exc) from exc
            self._apply_overrides(agent)
            self._capabilities[name] = self._describe(name, agent)

    def _build_local_router(self, laya_module: Any, root: str, names: Sequence[str]) -> Any:
        """A router whose checkpoints all come from one local directory."""
        import os

        models: dict[str, Any] = {}
        for name in names:
            if name == "english":
                models[name] = (root, None)
            else:
                subfolder = os.path.join(root, name)
                if not os.path.isdir(subfolder):
                    raise UnknownModelError(
                        f"checkpoint {name!r} is not present under {root!r}",
                        hint=f"expected a directory named {name!r} beside rl_agent_config.json",
                    )
                models[name] = (root, name)
        router = laya_module.Router(models=models, device=self.config.device)
        return router

    def _apply_overrides(self, agent: Any) -> None:
        """Set the token budgets and note whether the device was demoted.

        Laya falls back to CPU on an OOM during placement and prints a warning to
        stdout. There is no flag, so the only way to know is to compare the
        device it ended on against the one that was asked for.
        """
        if self.config.max_len is not None:
            agent.cfg["max_len"] = int(self.config.max_len)
        if self.config.head_max_len is not None:
            agent.cfg["head_max_len"] = int(self.config.head_max_len)

        actual = str(getattr(agent, "device", "unknown"))
        if self.config.device and actual != self.config.device:
            if actual.startswith("cpu") and not self.config.device.startswith("cpu"):
                self._degraded = True
                log.warning(
                    "Laya placed the model on %s although %s was requested. Inference will be "
                    "roughly 10-15x slower. On an RTX 50-series card this usually means the "
                    "PyTorch wheel was built without sm_120 support.",
                    actual,
                    self.config.device,
                )

    def _describe(self, name: str, agent: Any) -> Capability:
        cfg = getattr(agent, "cfg", {}) or {}
        # Build a throwaway capability from the agent's live config, which is what
        # matters after an override - the file on disk may now disagree with it.
        from .capability import KNOWN_CHECKPOINTS

        repo, subfolder = KNOWN_CHECKPOINTS.get(name, ("?", None))
        return Capability(
            checkpoint=name,
            repo=repo,
            subfolder=subfolder,
            encoder=cfg.get("encoder"),
            device=str(getattr(agent, "device", "unknown")),
            requested_device=self.config.device,
            degraded=self._degraded,
            max_len=int(cfg.get("max_len", 512)),
            head_max_len=int(cfg.get("head_max_len", 192)),
            head_layers=cfg.get("head_layers"),
            temperature=tuple(float(t) for t in cfg.get("temperature", [1.0, 1.0, 1.0])),
            fitted_temperature_buckets=len(cfg.get("temperature_by_options") or {}),
            amp_dtype=cfg.get("amp_dtype"),
        )

    def stop(self) -> None:
        """Release the model and reclaim accelerator memory.

        ``Router.unload`` drops its references but does not empty the CUDA
        allocator cache, so a restart in-process would inherit a fragmented
        allocator. Issue #52 upstream is the same class of problem at 21.7 GB.
        """
        with self._state_lock:
            router = self._router
            self._router = None
            self._loaded = False
        if router is not None:
            try:
                router.unload()
            except Exception:  # noqa: BLE001 - a failed unload must not block shutdown
                log.debug("router.unload raised during shutdown", exc_info=True)
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001
            pass
        log.info("model released")

    # -- introspection -------------------------------------------------------

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def capabilities(self) -> Mapping[str, Capability]:
        return dict(self._capabilities)

    def health(self) -> dict[str, Any]:
        """A health report that distinguishes "up" from "useful".

        A server that has loaded a model it cannot run is not healthy, and a
        server that silently demoted itself to CPU is not healthy either - it will
        answer, and it will be wrong about how fast.
        """
        payload: dict[str, Any] = {
            "loaded": self._loaded,
            "degraded": self._degraded,
            "calls": self._calls,
            "failures": self._failures,
            "last_latency_ms": round(self._last_latency_ms, 2),
            # Which end of an oversized state survives. A client that reads
            # `truncated` needs this to interpret it, and it is a property of the
            # server rather than of any one answer.
            "truncate_left": self.config.truncate_left,
        }
        if self._started_at is not None:
            payload["uptime_s"] = round(time.time() - self._started_at, 1)
        if self._load_error:
            payload["load_error"] = self._load_error
        payload["checkpoints"] = {
            name: {
                "device": cap.device,
                "max_len": cap.max_len,
                "head_max_len": cap.head_max_len,
                "fitted_temperature_buckets": cap.fitted_temperature_buckets,
            }
            for name, cap in self._capabilities.items()
        }
        if self._calibration.load_error:
            payload["calibration_load_error"] = self._calibration.load_error
        return payload

    def capability_for(self, checkpoint: str) -> Optional[Capability]:
        return self._capabilities.get(checkpoint)

    def _capability_for(self, name: str) -> Capability:
        """The capability of the checkpoint that will actually answer.

        Resolving an explicit ``lang`` can select a checkpoint this host was never
        configured to preload - ``--model english`` plus ``lang="zh"`` means
        ``multilingual`` - and every downstream number comes from the capability:
        the token budget, the script caveat, the device. Falling back to whichever
        checkpoint happened to be loaded is how a ``multilingual`` answer was
        planned against the English checkpoint's 512-token head budget and handed
        a warning saying English could not read the text it had just read.
        """
        capability = self._capabilities.get(name)
        if capability is not None:
            return capability

        agent = self._router.load(name)
        self._apply_overrides(agent)
        capability = self._describe(name, agent)
        self._capabilities[name] = capability
        return capability

    # -- inference -----------------------------------------------------------

    def ask(self, request: AskRequest) -> AskResponse:
        """Run one batch. The whole public surface of the model host."""
        self.start()

        # Validation and planning happen before the lock: they are pure and a bad
        # request should not queue behind a good one.
        validate_questions(request.questions)
        checkpoint = self._resolve_checkpoint(request)
        capability = self._capability_for(checkpoint)

        plan: BudgetPlan = plan_questions(
            capability,
            request.state,
            request.questions,
            truncate_left=self.config.truncate_left,
        )
        plan.warnings = (*plan.warnings, *self._request_warnings(request, capability))
        if (request.strict or self.config.strict) and not plan.fits:
            raise StateTruncatedError(
                "the state does not fit this checkpoint's token budget",
                hint=plan.recommendation or "shorten the state or raise max_len at startup",
                details=plan.truncation_report() or {},
            )

        if self.config.concurrency <= 1:
            with self._lock:
                return self._run(request, checkpoint, capability, plan)

        # A bounded semaphore keeps a burst from queueing without limit; past the
        # ceiling a caller is told to retry rather than left hanging.
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            raise CapacityError(
                "a forward pass is already running and this host is configured for one at a time",
                hint="raise --concurrency only if you know Laya is not sharing device state here",
            )
        try:
            return self._run(request, checkpoint, capability, plan)
        finally:
            self._lock.release()

    def plan(self, request: AskRequest) -> dict[str, Any]:
        """What :meth:`ask` would do to the state, without a forward pass.

        The same ``plan_questions`` call :meth:`ask` makes, over the same
        capability and the same request, so the two cannot report different
        numbers. Exposed on its own because "will this be cut?" is a question a
        caller should be able to ask for free: a cold host pays a model *load*
        here - loading weights is not inferring with them - and then computes
        nothing at all.
        """
        self.start()
        validate_questions(request.questions)
        checkpoint = self._resolve_checkpoint(request)
        capability = self._capability_for(checkpoint)

        plan: BudgetPlan = plan_questions(
            capability,
            request.state,
            request.questions,
            truncate_left=self.config.truncate_left,
        )
        plan.warnings = (*plan.warnings, *self._request_warnings(request, capability))
        return plan.to_dict()

    def _request_warnings(
        self, request: AskRequest, capability: Capability
    ) -> tuple[str, ...]:
        """Warnings about a request this checkpoint cannot actually serve.

        Both conditions used to pass in silence, which is the one thing this
        package exists not to do.
        """
        warnings: list[str] = []
        bare = sorted(
            qid
            for qid, question in request.questions.items()
            if question.type == "noul" and not noul_has_option_text(question)
        )
        if bare:
            warnings.append(
                f"noul question(s) {', '.join(bare)} have no criteria. This checkpoint renders a "
                "noul's options as the fixed pair `false: ...` / `true: ...` and then answers the "
                "first of them whatever the state says - measured at 40/40 'false' over forty "
                "balanced items, in both English and Chinese. Supply criteria, as "
                '`boundary: {"true": ..., "false": ...}`, so the question can be carried as a '
                "choice with real options; or ask it as a choice or a score instead."
            )
        caveat = script_caveat(capability, request.state, request.questions)
        if caveat:
            warnings.append(caveat)
        return tuple(warnings)

    def _resolve_checkpoint(self, request: AskRequest) -> str:
        """Which checkpoint will answer.

        Precedence: an explicit ``model``, then an explicit ``lang``, then the only
        loaded checkpoint, then the configured default.

        The ``lang`` branch asks the router rather than re-deriving its rule. That
        rule is one line - anything that is not English means ``multilingual`` -
        and copying it here is exactly how two implementations drift apart.
        Asking it also repairs what ``lang`` used to do: naming a language took
        the explicit path in :meth:`_run`, which bypasses the router, so
        ``lang="zh"`` was answered by the English checkpoint with nothing in the
        response to say so. The router is the only component that reads ``lang``.
        """
        if request.model:
            try:
                return normalise_checkpoint(request.model)
            except KeyError as exc:
                raise UnknownModelError(
                    f"unknown checkpoint {request.model!r}",
                    hint="known checkpoints are english, multilingual and typed-decisions",
                    cause=exc,
                ) from exc
        if request.lang:
            decision = self._router.route(
                request.state,
                {qid: q.to_laya() for qid, q in request.questions.items()},
                lang=request.lang,
            )
            routed = decision.get("model") if isinstance(decision, Mapping) else None
            if routed:
                return str(routed)
        if len(self._capabilities) == 1:
            return next(iter(self._capabilities))
        return self.config.model

    def _run(
        self,
        request: AskRequest,
        checkpoint: str,
        capability: Capability,
        plan: BudgetPlan,
    ) -> AskResponse:
        started = time.perf_counter()
        self._calls += 1

        questions, carried_nouls = self._to_laya_questions(request.questions)
        routing: Optional[RoutingInfo] = None

        try:
            if self.config.model_root or request.model or request.task:
                # An explicit choice bypasses the router's own reasoning; call the
                # agent directly so the caller gets exactly what it asked for.
                log.debug("_run: loading agent %r from the local router", checkpoint)
                agent = self._router.load(checkpoint)
                log.debug("_run: agent loaded, calling system_one")
                kwargs = {}
                if request.task:
                    kwargs["task"] = request.task
                if request.lang:
                    kwargs["lang"] = request.lang
                raw = agent.system_one(request.state, questions)
                log.debug("_run: system_one returned")
                routing = RoutingInfo(
                    model=checkpoint, lang=request.lang, reason="explicit model selection"
                )
            else:
                log.debug("_run: routing via the router's own predict")
                raw = self._router.predict(
                    request.state, questions, **self._route_kwargs(request)
                )
                routing = self._routing_from(raw, checkpoint)
        except LayaMcpError:
            self._failures += 1
            raise
        except Exception as exc:  # noqa: BLE001
            self._failures += 1
            translated = translate(exc)
            if isinstance(translated, OutOfMemoryError):
                # Laya may have already demoted itself; either way the caller
                # should know the host is now in a worse state than it was.
                self._degraded = True
            raise translated from exc

        latency_ms = (time.perf_counter() - started) * 1000
        self._last_latency_ms = latency_ms

        answers = self._normalise_answers(
            raw, request.questions, checkpoint, capability, carried_nouls
        )
        truncated = plan.truncation_report()

        warnings: list[str] = list(plan.warnings)
        if self._degraded:
            warnings.append(
                "this host is running on CPU because Laya demoted itself after a device error; "
                "expect roughly 10-15x the latency you measured on the accelerator"
            )

        return AskResponse(
            answers=answers,
            model=checkpoint,
            routing=routing,
            usage=Usage(
                input_tokens=int((raw.get("usage") or {}).get("input_tokens", 0)),
                output_tokens=int((raw.get("usage") or {}).get("output_tokens", 0)),
                questions=len(questions),
            ),
            latency_ms=latency_ms,
            truncated=truncated,
            budget=plan.to_dict(),
            device=str(capability.device),
            degraded=self._degraded,
            warnings=tuple(warnings),
        )

    def _route_kwargs(self, request: AskRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if request.task:
            kwargs["task"] = request.task
        if request.lang:
            kwargs["lang"] = request.lang
        return kwargs

    def _routing_from(self, raw: Mapping[str, Any], fallback: str) -> RoutingInfo:
        """Read Laya's routing metadata into our own shape.

        Laya's dict has five keys, not the three the README shows: ``model``,
        ``repo``, ``reason``, ``detection`` and ``workflow``. ``model`` here is
        the checkpoint *name*, whereas the ``model`` field inside the answers
        payload is the constant string ``laya-rl-agent``, which names nothing.
        Both facts are why this is translated rather than forwarded.
        """
        routing = raw.get("routing")
        if not isinstance(routing, Mapping):
            return RoutingInfo(model=fallback)
        return RoutingInfo(
            model=str(routing.get("model", fallback)),
            repo=routing.get("repo"),
            reason=routing.get("reason"),
            detection=routing.get("detection"),
            workflow=routing.get("workflow"),
        )

    def _to_laya_questions(
        self, questions: Mapping[str, Question]
    ) -> tuple[dict[str, dict[str, Any]], set[str]]:
        """Render the batch for Laya, and say which nouls were carried as choices.

        Returns the rendered questions and the ids whose *answer* has to be read
        back out of a choice distribution. The two must travel together: a noul
        sent as a choice comes back with ``choice``/``probabilities`` and no
        ``noul`` field at all, so a caller that forgot the second half would
        report every one of them as unanswered.
        """
        rendered: dict[str, dict[str, Any]] = {}
        carried: set[str] = set()
        for question_id, question in questions.items():
            if (
                self.config.noul_as_choice
                and question.type == "noul"
                and noul_has_option_text(question)
            ):
                rendered[question_id] = noul_as_choice(question)
                carried.add(question_id)
            else:
                rendered[question_id] = question.to_laya()
        return rendered, carried

    def _normalise_answers(
        self,
        raw: Mapping[str, Any],
        questions: Mapping[str, Question],
        checkpoint: str,
        capability: Capability,
        carried_nouls: Optional[set[str]] = None,
    ) -> Mapping[str, Answer]:
        """Turn Laya's per-primitive answer dicts into one shape.

        The three primitives return genuinely different structures - a noul has no
        distribution at all, a score reports string-keyed indices - and flattening
        them into one type is what lets the MCP tools and the sidecar share a
        response schema. A field Laya did not return stays ``None`` rather than
        being filled with a plausible default.
        """
        raw_answers = raw.get("answers") or {}
        entry: Optional[CalibrationEntry] = self._calibration.get(checkpoint)
        out: dict[str, Answer] = {}

        for question_id, question in questions.items():
            payload = raw_answers.get(question_id)
            if not isinstance(payload, Mapping):
                # Laya returned nothing for a question we asked. Report it as an
                # answer with no value rather than inventing one.
                out[question_id] = Answer(question_id=question_id, type=question.type)
                continue

            action = payload.get("action") or {}
            act_probability = action.get("act_probability") if isinstance(action, Mapping) else None
            answer = Answer(
                question_id=question_id,
                type=question.type,
                confidence=_as_float(payload.get("confidence")),
                act_probability=_as_float(act_probability),
            )

            if question.type == "noul":
                if carried_nouls and question_id in carried_nouls:
                    # Asked as a two-option choice under neutral labels, so
                    # P(true) is the probability of the first label - see
                    # `protocol.noul_as_choice` for why it was asked that way.
                    probabilities = _as_float_map(payload.get("probabilities")) or {}
                    probability = probabilities.get(NEUTRAL_LABELS[0])
                    # Keep the distribution. A noul is the one primitive whose
                    # answer is a single number, and dropping the distribution
                    # here would make the calibration step below skip every noul
                    # in silence - it only fires on an answer that has one.
                    answer.probabilities = probabilities or None
                else:
                    probability = _as_float(payload.get("noul"))
                answer.noul = probability
                if probability is not None:
                    answer.band = _band(probability)
            elif question.type == "choice":
                answer.choice = payload.get("choice")
                answer.probabilities = _as_float_map(payload.get("probabilities"))
            else:
                answer.score = _as_float(payload.get("score"))
                legend = payload.get("legend")
                if isinstance(legend, Mapping):
                    answer.legend = {str(k): str(v) for k, v in legend.items()}
                answer.probabilities = _as_float_map(payload.get("probabilities"))

            # Apply a fitted calibration on top of whatever the checkpoint shipped.
            # Only the distribution is rescaled; the reported `confidence` is
            # recomputed from the rescaled distribution so the two cannot disagree.
            if entry is not None and not entry.is_identity() and answer.probabilities:
                temperature = entry.temperature_for(question.type, len(answer.probabilities))
                if abs(temperature - 1.0) > 1e-9:
                    rescaled = _rescale(answer, temperature)
                    answer.probabilities = rescaled
                    if question.type == "noul":
                        # A carried noul's answer is a number read off this
                        # distribution, so rescaling without re-reading it would
                        # leave `noul` and `probabilities` contradicting each
                        # other inside one response.
                        reread = rescaled.get(NEUTRAL_LABELS[0])
                        if reread is not None:
                            answer.noul = reread
                            answer.band = _band(reread)

            out[question_id] = answer

        return out


def _as_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_float_map(value: Any) -> Optional[dict[str, float]]:
    if not isinstance(value, Mapping):
        return None
    out: dict[str, float] = {}
    for key, raw in value.items():
        number = _as_float(raw)
        if number is not None:
            out[str(key)] = number
    return out or None


def _rescale(answer: Answer, temperature: float) -> dict[str, float]:
    """Apply a temperature to an answer's distribution, keeping its top label.

    A calibration changes probabilities, not the argmax - temperature scaling is
    monotone, so the ranking is preserved by construction. Recomputing the
    selected label anyway would be busywork, so this returns the new distribution
    and stops.
    """
    probabilities = answer.probabilities or {}
    keys = list(probabilities.keys())
    scaled = apply_temperature([probabilities[k] for k in keys], temperature)
    return {k: round(v, 6) for k, v in zip(keys, scaled)}
