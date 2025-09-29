param([switch]$CollectCsv)

Write-Host "[bench] Simulating foreground CPU burst" -ForegroundColor Cyan
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$target = 5
for ($i = 0; $i -lt $target; $i++) {
    1..500000 | ForEach-Object { [math]::Sqrt($_) } | Out-Null
    Start-Sleep -Milliseconds 100
}
$sw.Stop()

if ($CollectCsv) {
    Write-Output "duration_ms=$($sw.ElapsedMilliseconds)"
}
