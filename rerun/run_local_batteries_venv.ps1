# Re-run the Tier-2 local batteries that need `tokenizers` (protocol-correct budget
# accounting), using the interpreter bench_env.py already names for exactly this job:
# LAYA_VENV_PYTHON. The first pass used the bare `python` on PATH, which lacks
# `tokenizers`, so every sidecar call that counts tokens raised SidecarError.
$ErrorActionPreference = "Continue"
Set-Location D:\Projects\llm-jev-laya-bench
$PY = "D:\Projects\laya-family\.venv-laya\Scripts\python.exe"

$jobs = @(
  @{ name = "P5";   art = "P5-certificate-verification.json";            script = "src\items\p5_certificate_verification.py" },
  @{ name = "P5b";  art = "P5b-classifier-templates.json";               script = "src\items\p5b_classifier_templates.py" },
  @{ name = "P5c";  art = "P5c-marker-vs-integration.json";              script = "src\items\p5c_marker_vs_integration.py" },
  @{ name = "P6";   art = "P6-hierarchical-sharding.json";               script = "src\items\p6_hierarchical_sharding.py" },
  @{ name = "P6b";  art = "P6b-hierarchical-sharding-opaque-keys.json";  script = "src\items\p6b_hierarchical_sharding_opaque.py" },
  @{ name = "P9";   art = "P9-template-validation-n32.json";             script = "src\items\p9_template_validation.py" },
  @{ name = "P9b";  art = "P9b-template-validation-separated-n48.json";  script = "src\items\p9b_template_validation_separated.py" },
  @{ name = "P1";   art = "P1-rank-vs-choice.json";                      script = "src\items\p1_rank_vs_choice.py" },
  @{ name = "P2";   art = "P2-mock-pipeline-rehearsal.json";             script = "src\harness\evaluate.py" }
)

foreach ($j in $jobs) {
  Write-Output ("=" * 78)
  Write-Output ("### {0}  <- {1}   (venv python)" -f $j.name, $j.script)
  Write-Output ("=" * 78)
  $log = "rerun\log-venv-$($j.name).txt"
  $t0 = Get-Date
  & $PY $j.script *> $log
  $rc = $LASTEXITCODE
  $dt = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
  Write-Output ("  exit={0}  {1}s  log={2}" -f $rc, $dt, $log)
  Get-Content $log -Tail 5 | ForEach-Object { "    | $_" }
}
Write-Output "ALL VENV BATTERIES DONE"
