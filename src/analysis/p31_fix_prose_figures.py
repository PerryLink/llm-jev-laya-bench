"""One-off prose corrections for the stale P27 figures (round 5)."""

# Paths resolve through bench_env, which locates the repository root by walking
# up from this file and honours environment overrides (LAYA_ROOT, DSH_CREDENTIALS,
# ...). Run `python bench_env.py` to print what was resolved. The aliased imports
# keep this block independent of whatever this module imported above, so it can
# sit at any top-level position.
import sys as _sys
from pathlib import Path as _Path

_p = _Path(__file__).resolve()
while not (_p / "bench_env.py").exists():
    if _p.parent == _p:
        raise RuntimeError(f"bench_env.py not found above {__file__}")
    _p = _p.parent
ROOT = _p
_sys.path.insert(0, str(ROOT))


from pathlib import Path


D = "$"
SUBS_REPORT = [
    (f"> **本轮支出：{D}0.0021**",
     f"> **本轮支出：{D}0.00228**（第五轮更正：原印 {D}0.0021，漏计 `P27b-plugin-crossval.json` 的 7 次插件调用 "
     f"{D}0.000102018；合计 {D}0.002280516 = P27 {D}0.001242822 + P27b {D}0.000102018 + P27c "
     f"{D}0.000890820 + P27d {D}0.000044856。由 `p27e_summary.py` 从四个产物汇总，见 "
     f"`results\\P27-summary.json` 的 `spend_usd_by_artifact`）"),
    ("### 2.5 插件的 `latencyMs` 自报约为独立墙钟的 **2.02 倍**",
     "### 2.5 插件的 `latencyMs` 自报约为**尺寸匹配**墙钟的 **1.94 倍**（第五轮更正）"),
    ("| 本客户端墙钟 | 20 | **915 ms** | 1,001 | 848 | 1,802 |",
     "| 本客户端墙钟（**本产物重跑后**） | 20 | **1,192 ms** | 1,551 | 847 | **4,019** |\n"
     "| ↑ 同一脚本**上一次**运行（本报告原印的那组） | 20 | 915 ms | 1,001 | 848 | 1,802 |"),
    ("| **Jev**（openrouter） | **938.6 ms**（mean 1,093 / min 848 / max 2,172） | **35** | **墙钟（本客户端）** |",
     "| **Jev**（openrouter） | **1,073.4 ms**（mean 1,407 / min 847 / max 4,019） | **35** | "
     "**墙钟（本客户端）**；⚠️ **单次抽样**——同一脚本两次运行 p50 相差 30%、max 相差 123%，故论文报**区间** **0.9–1.2 s** |"),
    ("| 1 | Jev p50 **1,380 ms**（插件自报，n=13，且其汇总均值算术上不可能） | **938.6 ms（墙钟，n=35）**；并披露插件自报约为墙钟 2.02 倍 |",
     "| 1 | Jev p50 **1,380 ms**（插件自报，n=13，且其汇总均值算术上不可能） | **1,073.4 ms（墙钟，n=35）**；"
     "并披露插件自报约为**尺寸匹配**墙钟 **1.94 倍**（不匹配时 1.55 倍） |"),
    ("**本文把它记为一条待验证的旗标，不是结论。** 旁证：直接路线的**最大值**（1,802 ms）仍**低于**插件自报的**中位数**（1,851 ms）。",
     "**本文把它记为一条待验证的旗标，不是结论。** 且该旗标现**更强**：直接路线重跑后的**最大值**为 **4,019 ms**，"
     "**高于**插件自报的中位数（1,851 ms）——即「插件比直连慢」这一读法在重跑后**不再成立**，"
     "1.94 倍只对**尺寸匹配**的那一类状态成立。"),
]

SUBS_AUDIT = [
    ("| **J-4** | 插件自报 `latencyMs`（n=7，p50 **1,851**）≈ 独立墙钟（n=20，p50 **915**）的 **2.02 倍** | 又一处自报字段与独立测量不符；**但两组非同批采集，记为旗标而非结论** |",
     "| **J-4** | 插件自报 `latencyMs`（n=7，p50 **1,851**）≈ **尺寸匹配**独立墙钟（126 字符类，n=5，p50 **956**）的 **1.94 倍**；对不匹配的当前 n=20 运行（p50 **1,192**）则读作 **1.55 倍** | "
     "又一处自报字段与独立测量不符；**但两组非同批采集，且比值取决于状态是否匹配，记为旗标而非结论** |"),
    ("| Jev p50 **1,380 ms**（插件自报 n=13） | **938.6 ms**（独立墙钟 **n=35**，mean 1,093 / max 2,172） |",
     "| Jev p50 **1,380 ms**（插件自报 n=13） | **1,073.4 ms**（独立墙钟 **n=35**，mean 1,407 / max 4,019；**单次抽样，两次运行 p50 差 30%**） |"),
    ("| 延迟阶梯 **37 倍** | **约 25 倍**（938.6/37.4）；并逐列标注测量点（Laya 墙钟 / LLM 自报 / Jev 墙钟） |",
     "| 延迟阶梯 **37 倍** | **约 25–29 倍**（37.4 ms / 671 ms / **0.9–1.2 s**）；**三者均为客户端墙钟**（非 provider 自报），但状态规模与传输不同，故为阶梯而非同类比较 |"),
    (f"**支出：{D}0.0021**（累计四轮 {D}0.0139，预算 {D}0.50）。",
     f"**支出：{D}0.00228**（第五轮更正：原印 {D}0.0021，漏计 P27b 的 7 次插件调用 "
     f"{D}0.000102018；合计 {D}0.002280516。累计四轮 {D}0.0139，预算 {D}0.50）。"),
]


def apply(path: Path, subs: list) -> None:
    t = path.read_text(encoding="utf-8")
    print(f"===== {path.relative_to(ROOT)}")
    for a, b in subs:
        if a not in t:
            print(f"  MISS: {a[:80]}")
            continue
        t = t.replace(a, b)
        print(f"  ok  : {a[:80]}")
    path.write_text(t, encoding="utf-8")


apply(ROOT / "probes" / "P27-jev-live-report.md", SUBS_REPORT)
apply(ROOT / "protocol" / "AUDIT-FINDINGS.md", SUBS_AUDIT)
print("\ndone")
