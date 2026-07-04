import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        session_or_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        from communications.services import ChatService
        from communications.models import Conversation
        
        try:
            # Try to fetch by integer ID
            conv_id = int(session_or_id)
            self.conversation = await database_sync_to_async(Conversation.objects.get)(id=conv_id)
        except (ValueError, Conversation.DoesNotExist):
            # It's a string (UUID) or doesn't exist, create/get for WEB channel
            self.conversation = await database_sync_to_async(ChatService.get_or_create_conversation)(
                phone_number=session_or_id,
                channel='WEB'
            )

        self.room_group_name = f"chat_{self.conversation.id}"

        # Unirse al grupo de la conversación
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Recibe mensajes directamente del cliente WebSocket y los guarda usando ChatService.
        """
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        sender = text_data_json.get('sender', 'USER')

        # Importar ChatService localmente para evitar importación circular
        from communications.services import ChatService
        import asyncio

        # Guardar en base de datos de manera segura y asíncrona
        try:
            msg_obj = await database_sync_to_async(ChatService.add_message)(
                conversation=self.conversation,
                sender=sender,
                message=message
            )
            
            # --- SIMULADOR TEMPORAL DE RESPUESTA DEL BOT ---
            if sender == 'USER':
                # Pausar un momento para simular que el bot está "escribiendo"
                await asyncio.sleep(1.5)
                await database_sync_to_async(ChatService.add_message)(
                    conversation=self.conversation,
                    sender='SYSTEM',
                    message="*Este es un mensaje automático de prueba.* ¡Hemos recibido tu mensaje correctamente! Pronto conectaremos nuestra Inteligencia Artificial aquí. 🚀"
                )
            # -----------------------------------------------

        except Exception as e:
            # Enviar mensaje de error al WebSocket del emisor
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def chat_message(self, event):
        """
        Recibe los eventos difundidos en el grupo y los retransmite al WebSocket.
        """
        await self.send(text_data=json.dumps({
            'id': event.get('id'),
            'message': event.get('message'),
            'sender': event.get('sender'),
            'created_at': event.get('created_at')
        }))
