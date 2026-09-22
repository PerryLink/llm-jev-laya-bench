# Tier-3a: re-run the Jev arm (P27 family). Paid API calls (TypeSafe Jev), ~$0.002 total.
# Order matters: P27c and P27 feed P27b and P27e.
$ErrorActionPreference = "Continue"
Set-Location D:\Projects\llm-jev-laya-bench
$PY = "D:\Projects\llm-jev-laya-fambly-does-not-exist"   # placeholder, replaced below
$PY = "D:\Projects\laya-family\.venv-laya\Scripts\python.exe"

$jobs = @(
  @{ name = "P27c"; script = "src\instrument\p27c_latency_sweep.py" },
  @{ name = "P27";  script = "src\instrument\p27_jev_live.py" },
  @{ name = "P27b"; script = "src\instrument\p27b_plugin_crossval.py" },
  @{ name = "P27d"; script = "src\instrument\p27d_primitive_fields.py" },
  @{ name = "P27e"; script = "src\instrument\p27e_summary.py" }
)

foreach ($j in $jobs) {
  Write-Output ("=" * 78)
  Write-Output ("### {0}  <- {1}" -f $j.name, $j.script)
  Write-Output ("=" * 78)
  $log = "rerun\log-$($j.name).txt"
  $t0 = Get-Date
  & $PY $j.script *> $log
  $rc = $LASTEXITCODE
  $dt = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
  Write-Output ("  exit={0}  {1}s  log={2}" -f $rc, $dt, $log)
  Get-Content $log -Tail 12 | ForEach-Object { "    | $_" }
}
Write-Output "P27 FAMILY DONE"
