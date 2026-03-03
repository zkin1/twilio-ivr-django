from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.voice_response import VoiceResponse, Gather
from django.conf import settings

@csrf_exempt
def voice_prompt(request):
    """
    Endpoint /voice/ que saluda al usuario, usa Gather para capturar 1 dígito
    y ofrece 3 anexos.
    """
    print(f"\n[IVR] --- NUEVA LLAMADA ---")
    print(f"[IVR] De: {request.POST.get('From', 'Desconocido')} | Para: {request.POST.get('To', 'Desconocido')}")

    response = VoiceResponse()
    
    # Configure gather to capture 1 digit and send it to /voice/menu/
    gather = Gather(num_digits=1, action='/voice/menu/', method='POST')
    gather.say(
        "Bienvenido a la central de niu planet. "
        "Si desea comunicarse con ene planet, presione 1. "
        "Si desea comunicarse con top planet, presione 2. ",
        language="es-MX"
    )
    
    response.append(gather)
    # Si el usuario no ingresa nada, redirigimos automáticamente al primer número (opción 1)
    response.say("No hemos recibido su respuesta. Conectando con el primer departamento.", language="es-MX")
    response.redirect('/voice/auto_first/')

    return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def voice_menu(request):
    """
    Endpoint /voice/menu/ que lee request.POST['Digits'], 
    si es 1,2,3 hace Dial al área correspondiente, si no, repite menú.
    """
    digits = request.POST.get('Digits', '')
    twilio_number = request.POST.get('To', '') 
    
    # En Trial Accounts de Twilio, el Caller ID debe ser tu número Twilio verificado
    # Si usamos 'twilio dev-phone' desde el navegador, dev-phone pasa IDs inválidos como 'client:...'
    # Por eso usamos TWILIO_PHONE_NUMBER como fallback oficial.
    caller_id = getattr(settings, 'TWILIO_PHONE_NUMBER', twilio_number)
    
    # Limpieza básica: un caller ID válido en Twilio (fuera de SIP/Client) empieza con '+'
    if not caller_id.startswith('+'):
        # Si no es válido, mejor omitirlo y que Twilio intente usar el default.
        caller_id = '' 
        
    print(f"[IVR] Opción marcada por el usuario: '{digits}'")
    print(f"[IVR] Caller ID configurado para la redirección: '{caller_id}'")

    response = VoiceResponse()
    
    destinos = {
        '1': ("ventas", getattr(settings, 'PHONE_VENTAS', '')),
        '2': ("soporte", getattr(settings, 'PHONE_SOPORTE', '')),
        '3': ("administración", getattr(settings, 'PHONE_ADMINISTRACION', '')),
    }

    if digits in destinos:
        departamento, telefono_destino = destinos[digits]
        
        if not telefono_destino:
            print(f"[IVR] [ERROR] El número para {departamento} no está configurado en .env")
            response.say("Lo sentimos, este departamento no está disponible por el momento.", language="es-MX")
            response.redirect('/voice/')
        else:
            print(f"[IVR] Conectando con {departamento} al número: {telefono_destino}...")
            response.say(f"Conectando con el departamento de {departamento}.", language="es-MX")
            
            # El action URL permite saber SI LA LLAMADA FALLA durante el Dial.
            # Recordar: Las trial accounts solo pueden llamar a números VERIFICADOS.
            if caller_id:
                response.dial(telefono_destino, caller_id=caller_id, action="/voice/status/", method="POST")
            else:
                response.dial(telefono_destino, action="/voice/status/", method="POST")
    else:
        print(f"[IVR] [ADVERTENCIA] Opción inválida ingresada: '{digits}'")
        response.say("Opción no válida. Por favor, intente de nuevo.", language="es-MX")
        response.redirect('/voice/')
        
    return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
def voice_auto_first(request):
    """
    Endpoint /voice/auto_first/ que conecta automáticamente con la opción '1'
    cuando el usuario no presiona ninguna tecla en el menú inicial.
    """
    print("[IVR] Usuario no ingresó dígito: redirigiendo automáticamente a la opción 1")

    response = VoiceResponse()

    telefono_destino = getattr(settings, 'PHONE_VENTAS', '')
    caller_id = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
    if not telefono_destino:
        print("[IVR] [ERROR] PHONE_VENTAS no configurado.")
        response.say("Lo sentimos, no es posible conectar con el departamento en este momento.", language="es-MX")
        response.redirect('/voice/')
        return HttpResponse(str(response), content_type='text/xml')

    response.say("Le conectaremos ahora con el primer departamento.", language="es-MX")
    if caller_id and caller_id.startswith('+'):
        response.dial(telefono_destino, caller_id=caller_id, action="/voice/status/", method="POST")
    else:
        response.dial(telefono_destino, action="/voice/status/", method="POST")

    return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def voice_status(request):
    """
    Endpoint /voice/status/ para depurar fallos de redirección (<Dial>).
    Twilio invoca esta URL al terminar la llamada, o cuando falla.
    """
    call_status = request.POST.get('DialCallStatus', 'unknown')
    print(f"[IVR] Estado final de la redirección (DialCallStatus): {call_status.upper()}")
    
    response = VoiceResponse()
    
    if call_status == 'failed':
        print("[IVR] [ERROR] La llamada falló. Causas comunes: Caller ID inválido o número destino no verificado en Trial Account.")
        response.say(
            "La llamada no pudo ser completada. "
            "Si está usando una cuenta de prueba, verifique que el número de destino esté autorizado.", 
            language="es-MX"
        )
    elif call_status in ['no-answer', 'busy']:
        print(f"[IVR] Número ocupado o sin respuesta.")
        response.say("El departamento no responde en este momento. Intente más tarde.", language="es-MX")
    elif call_status == 'completed':
        print(f"[IVR] Llamada completada exitosamente.")
        response.say("Gracias por comunicarse con nosotros.", language="es-MX")
        
    response.hangup()
    return HttpResponse(str(response), content_type='text/xml')
