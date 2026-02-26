# Twilio IVR - Django Project (Global Environment)

Este es un mini proyecto en Django diseñado para simular una central telefónica IVR utilizando Twilio Voice.
Está configurado nativamente sobre tu entorno de Python Global y responde generando respuestas TwiML.

El proyecto está diseñado pensando en una futura conversión a multiempresa (B2B SaaS) utilizando variables de entorno para evitar configuración quemada (hardcode).

## Requisitos Previos

- Python 3.10+
- Django, twilio, python-dotenv
- Cuenta de Twilio activa (con saldo y un número de teléfono).

## Instalación y Ejecución

Al trabajar sin entorno virtual, las dependencias ya deben estar instaladas globalmente en tu PC.

1. **Configurar el entorno**:
   Asegúrate de que el archivo `.env` en la raíz contenga tus datos (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `PHONE_VENTAS`, `PHONE_SOPORTE`, `PHONE_ADMINISTRACION`).

2. **Aplicar migraciones**:
   ```bash
   python manage.py migrate
   ```

3. **Ejecutar el servidor de desarrollo**:
   ```bash
   python manage.py runserver
   ```
   El servidor estará corriendo localmente en `http://127.0.0.1:8000/`.

## Conexión Externa para Twilio (Webhook)

Twilio necesita una URL pública. Puedes usar [ngrok](https://ngrok.com/), `localtunnel`, o subir tu proyecto a la nube (Render, Railway, etc.).

### Si usas Ngrok
Abre otra terminal y ejecuta:
```bash
ngrok http 8000
```
*Atención: Las cuentas gratuitas de ngrok generan una pantalla de advertencia anti-abuso. Si Twilio falla con un mensaje de "Application error", usa `ngrok http 8000 --host-header="localhost:8000"` o usa TwiML Bins provisionalmente.*

### Configuración en Twilio
1. Entra a tu cuenta en [Twilio Console](https://www.twilio.com/console).
2. Ve a la configuración de tu número (Active Numbers).
3. En **Voice & Fax**, cambia **"A CALL COMES IN"** a **Webhook**.
4. Pega la URL pública que utilices y agrégale `/voice/` al final. (ej: `https://abcd.ngrok-free.app/voice/`)
5. Guarda los cambios. ¡Listo para llamar!
