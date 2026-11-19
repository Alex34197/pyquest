# Firma de código / Code signing

Firmar el ejecutable evita los avisos de seguridad del sistema ("app dañada" en
macOS, "editor desconocido" / SmartScreen en Windows). PyQuest ya queda **firmada
de forma ad-hoc en macOS** por el script de build (gratis, válida para ejecutarla
en tu propio Mac). Para **distribuir a otras personas** necesitas certificados
propios; aquí está el procedimiento.

> **Importante / honest note:** una firma de confianza real requiere certificados
> de pago: una **cuenta Apple Developer** (99 $/año) para macOS y un **certificado
> Authenticode** de una CA reconocida para Windows. No se pueden incluir en el
> proyecto: son credenciales personales. Abajo tienes los comandos listos para
> usar con los tuyos.

---

## macOS

**Firma ad-hoc (gratis, ya aplicada por `build/build_macos.sh`):**
```bash
codesign --deep --force --options runtime -s - dist/PyQuest.app
```
Permite abrir la app en tu Mac (quizá con clic derecho → Abrir la primera vez).

**Firma para distribución (Developer ID + notarización):**
```bash
# 1) Firmar con tu Developer ID Application
DEV_ID="Developer ID Application: Tu Nombre (TEAMID)"
codesign --deep --force --options runtime --timestamp -s "$DEV_ID" dist/PyQuest.app

# 2) Empaquetar y notarizar (Apple revisa la app)
ditto -c -k --keepParent dist/PyQuest.app PyQuest.zip
xcrun notarytool submit PyQuest.zip --keychain-profile "AC_PASSWORD" --wait

# 3) "Grapar" el ticket de notarización a la app
xcrun stapler staple dist/PyQuest.app
```
Configura `AC_PASSWORD` una vez con:
`xcrun notarytool store-credentials AC_PASSWORD --apple-id TU_EMAIL --team-id TEAMID`.

---

## Windows (Authenticode)

> Los **metadatos** del .exe (Nombre de producto, Versión, Copyright…) ya se
> incrustan automáticamente desde `version_info.txt` al compilar. Lo que sigue es
> solo la **firma digital**.

Hay dos caminos:

**A) Firma rápida con certificado autofirmado (gratis) — incluida**

```powershell
powershell -ExecutionPolicy Bypass -File build\sign_windows.ps1
```

Esto crea un certificado de firma de código autofirmado y firma `dist\PyQuest\PyQuest.exe`.
Tras esto, la pestaña **Firmas digitales** ya mostrará una firma. **Pero** Windows la
verá como "editor desconocido" en *otros* equipos (SmartScreen), porque el certificado
no procede de una CA reconocida. Sirve para tu equipo y para aprender el flujo. Si
quieres que **tu** equipo confíe sin avisos, importa el certificado en *Trusted Root* y
*Trusted Publishers* (pasos comentados al final del script, requieren admin).

**B) Firma real para distribuir (de pago)**

Necesitas un certificado de firma de código de una CA reconocida (DigiCert, Sectigo…).
Desde 2023, los certificados **OV/EV** exigen que la clave privada viva en un **token
hardware o HSM** (ya no basta un `.pfx` suelto para OV). Con tu certificado:

```bat
signtool sign /fd SHA256 /f "miCertificado.pfx" /p "TU_PASSWORD" ^
  /tr http://timestamp.digicert.com /td SHA256 "dist\PyQuest\PyQuest.exe"
```

Solo un certificado **EV** elimina el aviso de SmartScreen desde la primera descarga;
con **OV** la reputación se va ganando con el número de instalaciones.

---

## Linux

Linux no tiene un concepto de "firma del ejecutable" como Windows/macOS. Opciones
habituales para dar confianza:

- Firmar el `.tar.gz` con **GPG**: `gpg --detach-sign --armor PyQuest-linux.tar.gz`
  y publicar la firma `.asc` junto al archivo y tu clave pública.
- Empaquetar como **AppImage** y firmarlo, o distribuir vía **Flatpak/Snap**
  (que gestionan firmas en sus repositorios).

---

## En CI (GitHub Actions)

El workflow ya hace la **firma ad-hoc** en macOS. Para firma real:

1. Guarda el certificado y las contraseñas como **Secrets** del repositorio.
2. En el job de macOS, importa el `.p12` al llavero y firma con tu Developer ID;
   en Windows, recupera el `.pfx` del secret y ejecuta `signtool`.

La estructura de pasos está comentada en `.github/workflows/build.yml`.
