# Re-run the Tier-2 local (Laya-sidecar / mock) batteries, in place.
# Each artifact's published bytes are archived to results/_superseded first.
# $0 API spend; all calls go to the local sidecar on 127.0.0.1:8787 or to the mock provider.
$ErrorActionPreference = "Continue"
Set-Location D:\Projects\llm-jev-laya-bench

$jobs = @(
  @{ name = "P5";   art = "P5-certificate-verification.json";                 script = "src\items\p5_certificate_verification.py" },
  @{ name = "P5b";  art = "P5b-classifier-templates.json";                    script = "src\items\p5b_classifier_templates.py" },
  @{ name = "P5c";  art = "P5c-marker-vs-integration.json";                   script = "src\items\p5c_marker_vs_integration.py" },
  @{ name = "P6";   art = "P6-hierarchical-sharding.json";                    script = "src\items\p6_hierarchical_sharding.py" },
  @{ name = "P6b";  art = "P6b-hierarchical-sharding-opaque-keys.json";       script = "src\items\p6b_hierarchical_sharding_opaque.py" },
  @{ name = "P7";   art = "P7-banking77-hierarchical-sharding.json";          script = "src\items\p7_banking77_sharding.py" },
  @{ name = "P8";   art = "P8-low-cardinality.json";                          script = "src\items\p8_low_cardinality.py" },
  @{ name = "P9";   art = "P9-template-validation-n32.json";                  script = "src\items\p9_template_validation.py" },
  @{ name = "P9b";  art = "P9b-template-validation-separated-n48.json";       script = "src\items\p9b_template_validation_separated.py" },
  @{ name = "P1";   art = "P1-rank-vs-choice.json";                           script = "src\items\p1_rank_vs_choice.py" },
  @{ name = "P10";  art = "P10-plausibility-pruning-paired.json";             script = "src\items\p10_plausibility_pruning.py" },
  @{ name = "P20";  art = "P20-language-misrouting.json";                     script = "src\items\p20_language_misrouting.py" },
  @{ name = "P2";   art = "P2-mock-pipeline-rehearsal.json";                  script = "src\harness\evaluate.py" }
)

foreach ($j in $jobs) {
  Write-Output ("=" * 78)
  Write-Output ("### {0}  <- {1}" -f $j.name, $j.script)
  Write-Output ("=" * 78)
  python rerun\archive_before_rerun.py $j.art | Out-Null
  $log = "rerun\log-$($j.name).txt"
  $t0 = Get-Date
  python $j.script *> $log
  $rc = $LASTEXITCODE
  $dt = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
  Write-Output ("  exit={0}  {1}s  log={2}" -f $rc, $dt, $log)
  Get-Content $log -Tail 6 | ForEach-Object { "    | $_" }
}
Write-Output "ALL LOCAL BATTERIES DONE"
