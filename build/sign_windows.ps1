<#
  sign_windows.ps1 — firma PyQuest.exe en Windows.
  sign_windows.ps1 — sign PyQuest.exe on Windows.

  Uso / Usage (PowerShell, desde la raíz del proyecto):
      powershell -ExecutionPolicy Bypass -File build\sign_windows.ps1

  Crea un certificado AUTOFIRMADO (gratis) si no existe y firma el ejecutable.
  OJO: un certificado autofirmado solo es de confianza en ESTE equipo (o en
  equipos donde lo importes). Para distribuir sin avisos de SmartScreen necesitas
  un certificado de una CA reconocida (ver SIGNING.md).
#>

param(
    [string]$Exe = "dist\PyQuest\PyQuest.exe",
    # Nombre del editor que aparecerá en la firma digital.
    # Los acentos se construyen por código para no depender de la codificación del .ps1.
    [string]$Subject = "CN=Alex Garc$([char]0xED)a Gonz$([char]0xE1)lez",
    [string]$Timestamp = "http://timestamp.digicert.com"
)

if (-not (Test-Path $Exe)) {
    Write-Error "No se encuentra $Exe. Compila primero con build\build_windows.bat"
    exit 1
}

# 1) Reutiliza un certificado de firma de código existente o crea uno autofirmado
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
        Where-Object { $_.Subject -eq $Subject } | Select-Object -First 1
if (-not $cert) {
    Write-Host "Creando certificado autofirmado ($Subject)..."
    $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject $Subject `
        -CertStoreLocation Cert:\CurrentUser\My -KeyUsage DigitalSignature `
        -FriendlyName "PyQuest Code Signing" -NotAfter (Get-Date).AddYears(5)
}

# 2) Firma el ejecutable (con sello de tiempo para que la firma siga válida tras caducar el cert)
$sig = Set-AuthenticodeSignature -FilePath $Exe -Certificate $cert `
    -TimestampServer $Timestamp -HashAlgorithm SHA256
Write-Host "Estado de la firma: $($sig.Status)"

# 3) (Opcional) Para que ESTE equipo confíe en la firma sin avisos, importa el
#    certificado en 'Trusted Root' y 'Trusted Publishers' (requiere admin):
#
#    $pub = "$env:TEMP\pyquest_pub.cer"
#    Export-Certificate -Cert $cert -FilePath $pub | Out-Null
#    Import-Certificate -FilePath $pub -CertStoreLocation Cert:\LocalMachine\Root
#    Import-Certificate -FilePath $pub -CertStoreLocation Cert:\LocalMachine\TrustedPublisher
