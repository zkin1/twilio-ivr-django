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
    response = VoiceResponse()
    
    # Configure gather to capture 1 digit and send it to /voice/menu/
    gather = Gather(num_digits=1, action='/voice/menu/', method='POST')
    gather.say(
        "Bienvenido a la central telefónica. "
        "Si desea comunicarse con ventas, marque 1. "
        "Si desea comunicarse con soporte, marque 2. "
        "Si desea comunicarse con administración, marque 3.",
        language="es-MX"
    )
    
    response.append(gather)
    response.redirect('/voice/')

    return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def voice_menu(request):
    """
    Endpoint /voice/menu/ que lee request.POST['Digits'], 
    si es 1,2,3 hace Dial al área correspondiente, si no, repite menú.
    """
    digits = request.POST.get('Digits', '')
    twilio_number = request.POST.get('To', '') # El número +1 de Twilio
    
    response = VoiceResponse()
    
    if digits == '1':
        response.say("Conectando con el departamento de ventas.", language="es-MX")
        response.dial(settings.PHONE_VENTAS, caller_id=twilio_number)
    elif digits == '2':
        response.say("Conectando con el departamento de soporte.", language="es-MX")
        response.dial(settings.PHONE_SOPORTE, caller_id=twilio_number)
    elif digits == '3':
        response.say("Conectando con administración.", language="es-MX")
        response.dial(settings.PHONE_ADMINISTRACION, caller_id=twilio_number)
    else:
        response.say("Opción no válida. Por favor, intente de nuevo.", language="es-MX")
        response.redirect('/voice/')
        
    return HttpResponse(str(response), content_type='text/xml')
