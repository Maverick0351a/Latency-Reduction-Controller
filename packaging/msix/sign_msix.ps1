param(
  [string]$Msix = "LRC-App.msix",
  [string]$Pfx  = "dev_signing.pfx",
  [string]$Subject = "CN=WorldDataDev",
  [string]$Password = "Passw0rd!"
)

$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject $Subject `
  -KeyUsage DigitalSignature -CertStoreLocation Cert:\CurrentUser\My
Export-PfxCertificate -Cert $cert -FilePath $Pfx -Password (ConvertTo-SecureString -String $Password -Force -AsPlainText) | Out-Null

& signtool sign /fd SHA256 /f $Pfx /p $Password $Msix
Write-Host "Signed $Msix with dev PFX."
