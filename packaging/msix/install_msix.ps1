param(
  [string]$Msix = "LRC-App.msix",
  [string]$Pfx = "dev_signing.pfx",
  [string]$Password = "Passw0rd!"
)

$pwd = ConvertTo-SecureString -String $Password -Force -AsPlainText
Import-PfxCertificate -FilePath $Pfx Cert:\CurrentUser\TrustedPeople -Password $pwd | Out-Null
Add-AppxPackage -Path $Msix
