param([switch]$CollectCsv)

Write-Host "[bench] Creating background disk traffic" -ForegroundColor Yellow
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) "lrc-bench"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
$filePath = Join-Path $tempDir "disk_load.bin"

$sizeMB = 64
$buffer = New-Object byte[] (1024 * 1024)
$rand = [System.Random]::new()
$stream = [System.IO.File]::Open($filePath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
try {
    for ($i = 0; $i -lt $sizeMB; $i++) {
        $rand.NextBytes($buffer)
        $stream.Write($buffer, 0, $buffer.Length)
    }
    $stream.Flush()
    $stream.Seek(0, [System.IO.SeekOrigin]::Begin) | Out-Null
    $null = $stream.Read($buffer, 0, $buffer.Length)
} finally {
    $stream.Dispose()
}

Remove-Item -Force -Path $filePath -ErrorAction SilentlyContinue
Remove-Item -Force -Recurse -Path $tempDir -ErrorAction SilentlyContinue

if ($CollectCsv) {
    Write-Output "size_mb=$sizeMB"
}
