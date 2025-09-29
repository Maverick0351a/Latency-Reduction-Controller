param([switch]$CollectCsv)

Write-Host "[bench] Generating background network chatter" -ForegroundColor Green
$hosts = @("onedot.com", "cloudflare.com", "microsoft.com")
$results = @()
foreach ($host in $hosts) {
    try {
        $ping = Test-NetConnection -ComputerName $host -WarningAction SilentlyContinue -InformationLevel Quiet
        $results += [PSCustomObject]@{Host=$host;Reachable=([bool]$ping)}
    } catch {
        $results += [PSCustomObject]@{Host=$host;Reachable=$false}
    }
}

if ($CollectCsv) {
    $summary = $results | Where-Object { $_.Reachable } | Measure-Object | Select-Object -ExpandProperty Count
    Write-Output "reachable_hosts=$summary"
}
