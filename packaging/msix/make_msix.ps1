param(
  [string]$BuildDir = "dist\lrc-win",
  [string]$Out = "LRC-App.msix"
)

$staging = "packaging\msix\staging"
Remove-Item -Recurse -Force $staging -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $staging | Out-Null
New-Item -ItemType Directory -Force "$staging\lrc-win" | Out-Null
Copy-Item -Recurse -Force "$BuildDir\*" "$staging\lrc-win\"
Copy-Item -Recurse -Force "packaging\msix\Assets" "$staging\Assets"
Copy-Item -Force "packaging\msix\AppxManifest.xml" "$staging\AppxManifest.xml"

& makeappx pack /d $staging /p $Out
Write-Host "Created $Out"
