# Tier-3: re-run the paid LLM arm. Sequential, cheapest first, P19 (n=1100) LAST and
# only if the recorded spend so far leaves room under the $0.10 ceiling.
# Every artifact is archived to results/_superseded/<name>.pre-rerun before it is rewritten.
$ErrorActionPreference = "Continue"
Set-Location D:\Projects\llm-jev-laya-bench
$PY = "D:\Projects\laya-family\.venv-laya\Scripts\python.exe"

function Run-One($tag, $script, $arglist, $artifact) {
  Write-Output ("=" * 78)
  Write-Output ("### {0}  <- {1} {2}" -f $tag, $script, ($arglist -join " "))
  Write-Output ("=" * 78)
  if ($artifact) { python rerun\archive_before_rerun.py $artifact | Out-Null }
  $log = "rerun\log-$tag.txt"
  $t0 = Get-Date
  if ($arglist) { & $PY $script @arglist *> $log } else { & $PY $script *> $log }
  $rc = $LASTEXITCODE
  $dt = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
  Write-Output ("  exit={0}  {1}s  log={2}" -f $rc, $dt, $log)
  Get-Content $log -Tail 4 | ForEach-Object { "    | $_" }
}

Run-One "P21"  "src\items\p21_thinking_mode_cost.py" @() "P21-thinking-mode-cost.json"
Run-One "P23"  "src\items\p23_llm_logprobs.py"       @() "P23-llm-logprobs.json"
Run-One "P14"  "src\items\p14_llm_arm.py"            @() "P14-llm-arm-full.json"
Run-One "P15"  "src\items\p15_complementarity_strong_regime.py" @() "P15-complementarity-strong-regime.json"
Run-One "P15b-r1" "src\items\p15_complementarity_strong_regime.py" @("P15b-rep-r1.json","0.0","r1") "P15b-rep-r1.json"
Run-One "P15b-r2" "src\items\p15_complementarity_strong_regime.py" @("P15b-rep-r2.json","0.0","r2") "P15b-rep-r2.json"
Run-One "P15b-r3" "src\items\p15_complementarity_strong_regime.py" @("P15b-rep-r3.json","0.0","r3") "P15b-rep-r3.json"
Run-One "P22"  "src\items\p22_chain_audit.py"        @() "P22-chain-audit.json"
Run-One "P22b-r1" "src\items\p22_chain_audit.py"     @("P22b-fixed-r1.json","0.0","r1") "P22b-fixed-r1.json"
Run-One "P22b-r2" "src\items\p22_chain_audit.py"     @("P22b-fixed-r2.json","0.0","r2") "P22b-fixed-r2.json"
Run-One "P22b-r3" "src\items\p22_chain_audit.py"     @("P22b-fixed-r3.json","0.0","r3") "P22b-fixed-r3.json"
Run-One "P24"  "src\items\p24_reduced_horizon.py"    @() "P24-reduced-horizon.json"
Write-Output "LLM PHASE A DONE"
