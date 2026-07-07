import logging
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import render
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import uuid
from django.shortcuts import redirect
from communications.models import Conversation
from communications.services import ChatService

logger = logging.getLogger("twilio_whatsapp")

class TwilioWebhookView(APIView):
    """
    APIView de Django REST Framework para recibir mensajes entrantes de WhatsApp vía Twilio.
    Valida la firma de seguridad X-Twilio-Signature, persiste la conversación y los mensajes,
    y responde usando TwiML con un mensaje echo de retorno.
    """
    permission_classes = []  # El webhook es público; la seguridad se maneja mediante X-Twilio-Signature

    def post(self, request, *args, **kwargs):
        # 1. Extraer los datos enviados por Twilio
        from_number = request.data.get('From', '')
        body_text = request.data.get('Body', '')
        message_sid = request.data.get('MessageSid', '')

        # 2. Validar firma de Twilio si está activo en la configuración
        validate_sig = os.environ.get("VALIDATE_TWILIO_SIGNATURE", "true").lower() in ("1", "true", "yes")
        if validate_sig:
            auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
            if not auth_token:
                logger.error("VALIDATE_TWILIO_SIGNATURE está activo pero TWILIO_AUTH_TOKEN no está definido.")
                return Response("Configuración de firma incompleta", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            validator = RequestValidator(auth_token)
            signature = request.headers.get("X-Twilio-Signature", "")
            
            # Obtener URL absoluta solicitada por Twilio
            url = request.build_absolute_uri()
            
            # Convertir request.POST (QueryDict) a dict estándar para el validador
            params = request.POST.dict()
            
            if not validator.validate(url, params, signature):
                logger.warning("Firma de Twilio inválida detectada y rechazada.")
                return Response("Invalid signature", status=status.HTTP_403_FORBIDDEN)

        logger.info(f"Mensaje entrante de {from_number}: {body_text}")

        # 3. Guardar en base de datos y transmitir en tiempo real mediante ChatService
        try:
            # Obtener o crear la conversación
            conversation = ChatService.get_or_create_conversation(
                phone_number=from_number,
                channel='WHATSAPP'
            )
            
            # Registrar el mensaje entrante (enviado por el familiar/usuario)
            ChatService.add_message(
                conversation=conversation,
                sender='USER',
                message=body_text,
                twilio_sid=message_sid
            )
        except Exception as e:
            logger.error(f"Error procesando mensaje en ChatService: {str(e)}")
            return Response("Error processing message", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. State Machine, Validation & Escape Hatches
        body_upper = body_text.strip().upper()
        reply = ""

        # Global escape hatches
        if body_upper == 'CANCELAR':
            conversation.bot_state = 'IDLE'
            conversation.session_data = {}
            conversation.save()
            reply = "Operación cancelada. Puede iniciar de nuevo enviando cualquier mensaje."
        elif body_upper == 'AYUDA':
            conversation.status = 'PENDING_REVIEW'
            conversation.save()
            reply = "Un operador se pondrá en contacto con usted pronto."
        else:
            # State routing
            state = conversation.bot_state
            if state == 'IDLE':
                reply = "Bienvenido. Por favor ingrese el nombre del sujeto."
                conversation.bot_state = 'AWAITING_NAME'
                conversation.save()
            elif state == 'AWAITING_NAME':
                session_data = conversation.session_data or {}
                session_data['name'] = body_text.strip()
                conversation.session_data = session_data
                conversation.bot_state = 'AWAITING_ID'
                conversation.save()
                reply = "Ahora ingrese su cédula."
            elif state == 'AWAITING_ID':
                import re
                numbers = re.sub(r'\D', '', body_text)
                if len(numbers) >= 6:
                    session_data = conversation.session_data or {}
                    session_data['id_card'] = body_text.strip()
                    
                    from subjects.models import MissingPerson
                    from core.models import Case
                    
                    existing_person = MissingPerson.objects.filter(document_number=session_data['id_card']).first()
                    if existing_person:
                        conversation.case = existing_person.case
                    else:
                        new_case = Case.objects.create()
                        MissingPerson.objects.create(
                            case=new_case,
                            document_number=session_data['id_card'],
                            first_name=session_data.get('name', 'Desconocido')
                        )
                        conversation.case = new_case

                    conversation.session_data = session_data
                    conversation.bot_state = 'COMPLETED'
                    conversation.save()
                    reply = "Gracias. Hemos registrado los datos."
                else:
                    reply = "La cédula debe contener números. Por favor, intente de nuevo."
            elif state == 'COMPLETED':
                reply = "El reporte ya fue completado. Gracias."
            else:
                reply = "Estado desconocido. Reiniciando."
                conversation.bot_state = 'IDLE'
                conversation.session_data = {}
                conversation.save()

        # Log bot reply
        try:
            ChatService.add_message(
                conversation=conversation,
                sender='SYSTEM',
                message=reply
            )
        except Exception as e:
            logger.error(f"Error procesando respuesta del bot en ChatService: {str(e)}")

        twiml = MessagingResponse()
        twiml.message(reply)
        return HttpResponse(str(twiml), content_type="application/xml")


class ChatCreateAPIView(APIView):
    """
    Crea una nueva conversación de prueba con un número generado al azar
    y retorna los datos de la conversación en JSON.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        session_id = uuid.uuid4().hex
        conversation = ChatService.get_or_create_conversation(
            phone_number=session_id,
            channel='WEB'
        )
        return Response({
            "status": "success",
            "conversation_id": conversation.id,
            "phone_number": conversation.phone_number
        }, status=status.HTTP_201_CREATED)

class ChatDetailAPIView(APIView):
    """
    Retorna los detalles de la conversación y sus mensajes en formato JSON.
    """
    permission_classes = []

    def get(self, request, conversation_id, *args, **kwargs):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            messages = conversation.messages.all().order_by('created_at')
            return Response({
                "status": "success",
                "conversation_id": conversation.id,
                "phone_number": conversation.phone_number,
                "messages": [
                    {
                        "id": msg.id,
                        "sender": msg.sender,
                        "message": msg.message,
                        "created_at": msg.created_at.isoformat()
                    } for msg in messages
                ]
            }, status=status.HTTP_200_OK)
        except Conversation.DoesNotExist:
            return Response({"error": "La conversación no existe."}, status=status.HTTP_404_NOT_FOUND)

class SimulateBotMessageView(APIView):
    """
    Endpoint para simular el envío de un mensaje por parte del BOT.
    Útil para probar el flujo de WebSockets desde Postman.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        conversation_id = request.data.get('conversation_id')
        message = request.data.get('message', 'Este es un mensaje de prueba desde el BOT.')
        
        if not conversation_id:
            return Response({"error": "conversation_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            msg = ChatService.add_message_by_id(
                conversation_id=conversation_id,
                sender='BOT',
                message=message
            )
            return Response({
                "status": "success",
                "message_id": msg.id,
                "message": msg.message,
                "sender": msg.sender
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error simulando mensaje BOT: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SimulateUserMessageView(APIView):
    """
    Endpoint para simular el envío de un mensaje por parte del USUARIO.
    Útil para probar el flujo de WebSockets y hooks desde Postman.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        conversation_id = request.data.get('conversation_id')
        message = request.data.get('message', 'Este es un mensaje de prueba desde el USUARIO.')
        
        if not conversation_id:
            return Response({"error": "conversation_id es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            msg = ChatService.add_message_by_id(
                conversation_id=conversation_id,
                sender='USER',
                message=message
            )
            return Response({
                "status": "success",
                "message_id": msg.id,
                "message": msg.message,
                "sender": msg.sender
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error simulando mensaje USER: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

