"""Established-connection ownership for :8787 -- who is really talking to clients."""
from __future__ import annotations

import subprocess

ps = (
    "Write-Output '--- listeners ---'; "
    "Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue | "
    "Select-Object State,LocalAddress,LocalPort,RemotePort,OwningProcess | Format-Table -AutoSize | Out-String -Width 160; "
    "Write-Output '--- all conns, with process name ---'; "
    "Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue | ForEach-Object { "
    "$p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
    "\"$($_.State) local=$($_.LocalAddress):$($_.LocalPort) remote=$($_.RemoteAddress):$($_.RemotePort) pid=$($_.OwningProcess) name=$($p.ProcessName)\" }"
)
out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                     capture_output=True, text=True)
print(out.stdout)
print(out.stderr[:500])
