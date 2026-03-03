# Documentación Técnica: Sistema IVR Avanzado con Twilio y Django

Este documento detalla la arquitectura actual del sistema de Respuesta de Voz Interactiva (IVR), las modificaciones necesarias para su escalabilidad a un modelo B2B (Business-to-Business) en producción, los pasos para migrar a una cuenta Twilio profesional, la futura integración con Inteligencia Artificial y la guía de despliegue en infraestructuras compartidas como cPanel.

---

## 1. Arquitectura del Proyecto y Estructura de Archivos

El proyecto está construido sobre el framework web **Django** (Python), proporcionando una estructura modular (MVT) que facilita la escalabilidad. La arquitectura funciona como un puente de API entre Twilio (el proveedor de telecomunicaciones) y la lógica de negocio de la empresa.

### Archivos y Directorios Clave:

- **`manage.py`**: El punto de entrada para ejecutar comandos de Django (servidor local, migraciones de base de datos, creación de usuarios, etc.).
- **`ivr_project/` (Directorio Project):**
  - **`settings.py`**: Contiene la configuración global del proyecto. Aquí se cargan variables de entorno críticas como credenciales de Twilio, la clave secreta (`SECRET_KEY`), y configuraciones de base de datos.
  - **`urls.py`**: El enrutador central del sistema. Redirige el tráfico que entra a ciertas rutas (ej. `/voice/`) hacia la aplicación correspondiente (`ivr_app`).
  - **`wsgi.py` / `asgi.py`**: Interfaces estándar de Python para comunicar la aplicación Django con el servidor web en producción (ej. Gunicorn, uWSGI o Passenger en cPanel).
- **`ivr_app/` (Directorio Base de Lógica IVR):**
  - **`views.py`**: *El corazón del sistema*. Contiene los endpoints web (ej. `voice_prompt`, `voice_menu`, `voice_status`). Genera y devuelve instrucciones a Twilio mediante `TwiML` (Twilio Markup Language - un formato basado en XML) indicando si debe hablar, atrapar dígitos de presiones o redirigir una llamada.
  - **`urls.py`**: Define las rutas internas de la aplicación. Mapea la URL `/voice/` a la función `voice_prompt` de `views.py`.
- **`.env`**: Archivo de seguridad (no versionado en git) que almacena las credenciales de la API, números telefónicos de destino y configuraciones en texto plano.
- **`requirements.txt`**: Lista de dependencias del proyecto (Django, twilio, python-dotenv), fundamental para clonar el proyecto en el servidor de producción.

---

## 2. Transición de Entorno de Pruebas a Producción (Ambiente B2B)

Para que el proyecto deje de ser un caso de uso aislado y pase a ser un software comercial B2B (Software as a Service o producto multi-cliente), deben modificarse las siguientes áreas:

### A. Soporte Multi-Tenant (Multi-Empresa)
En vez de leer un solo número telefónico desde el `.env`, el sistema debe soportar N empresas.
- **Cambio Requerido:** Implementar modelos (`models.py`) para `Empresa`, `NumeroTwilio` y `Departamento`.
- **Flujo:** Cuando Twilio dispara el webhook, envía el número hacia el cual se está llamando (`To`). El sistema debe buscar ese número en la base de datos, identificar a qué empresa pertenece y generar el audio/menú/redirección personalizado para esa empresa en particular.

### B. Seguridad del Webhook
Actualmente se usa el decorador `@csrf_exempt` ya que Twilio no envía tokens CSRF del navegador.
- **Cambio Requerido:** Implementar **Twilio Request Validation**. Esto asegura que las solicitudes POST entrantes realmente provengan de los servidores seguros de Twilio y no de un tercero malicioso simulando ser Twilio. Se hace comparando la firma criptográfica incluida en el header `X-Twilio-Signature`.

### C. Almacenamiento de Registros Inmutables
- **Cambio Requerido:** La función `voice_status` actualmente imprime logs en consola. En un ambiente B2B, es necesario crear un modelo Base de Datos `CallLog` que guarde la fecha, hora, duración, origen, destino y la grabación de todas las llamadas para auditoría o reportabilidad del cliente final.

---

## 3. Transición de Cuenta Twilio Trial a Cuenta Pagada (Full)

Al actualizar de una cuenta "*Free Trial*" a una con fondos o nivel "*Upgraded*", desaparecerán varias limitaciones que facilitarán la implementación:

1. **Fin de Destinos Verificados:** Ya no tendrás que vincular y verificar manualmente los números de teléfono de destino (las personas que contestan las llamadas). El `<Dial>` funcionará hacia cualquier número local o internacional (según tus permisos geográficos habilitados en las opciones de Twilio).
2. **Caller ID Dinámico Autorizado:** El atributo `caller_id` dentro de la etiqueta `<Dial>` te permitirá reflejar los identificadores reales de manera fluida, por lo que el agente que reciba la llamada verá el número "origen" del cliente.
3. **Eliminación del Mensaje de Prueba:** Desaparecerá esa "voz por defecto" o restricción al iniciar que avisa al cliente final que la llamada se hace desde una cuenta de prueba de Twilio.
4. **Grabación de Llamadas Escalable:** Si bien se puede probar en Trial, en una cuenta full podrás activar `<Record>` de forma programática con una cuota de uso en la nube mayor, descargando archivos vía API para análisis.

---

## 4. Implementación de Inteligencia Artificial (El Futuro del Proyecto)

Para integrar IA conversacional real (un modelo de lenguaje natural o LLM que conteste en base a conocimientos pre-entrenados del negocio B2B) y presentarlo en su práctica, la arquitectura sufrirá un salto cualitativo potente:

### Flujo Técnico: Media Streams y WebSockets (Tiempo Real)
En lugar de depender de `<Gather>` (que espera a que el usuario marque un dígito), utilizarás **Twilio Media Streams**.

1. **Modificación de la Redirección (TwiML):**
   Tu vista ya no responderá con un menú numérico, sino con una etiqueta:
   `<Connect> <Stream url="wss://tu-dominio.com/media-stream" /> </Connect>`
2. **Implementación de Servidor WebSocket (ej. Django Channels o FastAPI):**
   La llamada abre un puerto de audio bidireccional puro. Envía el audio (fragmentos PCM) directamente al servidor.
3. **Procesamiento de IA (Tubería de 3 Capas):**
   - **Speech-to-Text (STT):** Como Google Speech API o Deepgram. Recibe el audio UDP de Twilio y lo pasa a texto.
   - **Large Language Model (LLM):** Envías ese texto como prompt a la API de OpenAI (GPT-4) para generar una respuesta estratégica como "Agente Inteligente".
   - **Text-to-Speech (TTS):** Transformas la respuesta del LLM a voz (ej. con ElevenLabs o OpenAI TTS) y envías los binarios de vuelta a través del WebSocket hacia el teléfono del celular de la persona conectada.

*Alternativa más veloz (Menos realista, pero funcional):* Integrar el motor **Twilio Autopilot/Twilio AI Asisstant** o usar `<Gather input="speech">`, que captura la frase hablada por el usuario, te envía el texto traducido al webhook, procesas en ChatGPT con una latencia de 3 a 6 segundos, y respondes con `<Say>`.

---

## 5. Despliegue en Producción (cPanel)
### Pasos en cPanel (Passenger WSGI)

1. **Configurar el Entorno de Python:**
   En tu tablero de cPanel, busca "*Setup Python App*". Crea una nueva aplicación seleccionando la versión más reciente de Python instalada.
2. **Directorio y Subdominio:**
   Asigna el directorio raíz al subdominio elegido (ej. `app.tuempresa.com`). cPanel generará automáticamente un archivo `passenger_wsgi.py`.
3. **Migración de Archivos:**
   Sube todos tus archivos (vía FTP o File Manager) excluyendo la carpeta oculta `venv` que usas en local y `.sqlite3`.
4. **Dependencias:**
   Vía SSH o la consola web de cPanel, navega hasta la carpeta y corre:
   `pip install -r requirements.txt`
   *(A veces cPanel lo permite directo desde el módulo web de Python App)*.
5. **Configuración del WSGI:**
   El módulo Passenger en cPanel necesita conectarse a tu objeto `application`. Deberás abrir `passenger_wsgi.py` e importar el de tu proyecto Django:
   ```python
   import sys
   from ivr_project.wsgi import application
   ```
6. **HTTPS y SSL (Vital para Twilio):**
   Twilio es reticente a enviar webhooks POST a sitios HTTP. Ingresa a la sección "SSL/TLS Status" en cPanel y habilita o lanza AutoSSL para tu dominio.
7. **Modificar Webhook en Twilio:**
   Ingresa a tu consola de Twilio > *Phone Numbers* > *Manage* > Selecciona tu número. En la sección "A call comes in...", pegua el link final:
   `https://app.tuempresa.com/voice/` (Asegúrate de cambiar de GET a POST). 

---

**Resumen de Cierre:**
Presentar este documento evidenciará que no solo lograste crear un script de Django comunicándose con Twilio, sino que posees una visión macro de arquitectura, escalabilidad para empresas, consideraciones del ciclo de facturación y proyección real de integraciones tecnológicas de vanguardia (IA), demostrando gran madurez técnica en este proyecto de práctica profesional.
