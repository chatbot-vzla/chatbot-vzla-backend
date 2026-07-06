from django.test import TestCase
from communications.models import Conversation

class ConversationModelTests(TestCase):
    def test_new_conversation_has_default_bot_state_and_session_data(self):
        conv = Conversation.objects.create(phone_number="+1234567890")
        self.assertEqual(conv.bot_state, 'IDLE')
        self.assertEqual(conv.session_data, {})

from django.urls import reverse
from unittest.mock import patch
import os

class TwilioWebhookTests(TestCase):
    def setUp(self):
        self.url = reverse('twilio_webhook')

    @patch.dict(os.environ, {"VALIDATE_TWILIO_SIGNATURE": "false"})
    def test_state_machine_flow(self):
        # 1. Start IDLE -> AWAITING_NAME
        response = self.client.post(self.url, {'From': '+123', 'Body': 'Hola', 'MessageSid': '123'})
        self.assertContains(response, "Bienvenido. Por favor ingrese el nombre del sujeto.")
        
        conv = Conversation.objects.get(phone_number='+123')
        self.assertEqual(conv.bot_state, 'AWAITING_NAME')

        # 2. AWAITING_NAME -> AWAITING_ID
        response = self.client.post(self.url, {'From': '+123', 'Body': 'Juan Perez', 'MessageSid': '124'})
        self.assertContains(response, "Ahora ingrese su cédula.")
        
        conv.refresh_from_db()
        self.assertEqual(conv.bot_state, 'AWAITING_ID')
        self.assertEqual(conv.session_data['name'], 'Juan Perez')

        # 3. AWAITING_ID (invalid) -> remains AWAITING_ID
        response = self.client.post(self.url, {'From': '+123', 'Body': 'abc', 'MessageSid': '125'})
        self.assertContains(response, "La cédula debe contener números.")
        
        conv.refresh_from_db()
        self.assertEqual(conv.bot_state, 'AWAITING_ID')

        # 4. AWAITING_ID (valid) -> COMPLETED
        response = self.client.post(self.url, {'From': '+123', 'Body': 'V-12345678', 'MessageSid': '126'})
        self.assertContains(response, "Gracias. Hemos registrado los datos.")
        
        conv.refresh_from_db()
        self.assertEqual(conv.bot_state, 'COMPLETED')
        self.assertEqual(conv.session_data['id_card'], 'V-12345678')

    @patch.dict(os.environ, {"VALIDATE_TWILIO_SIGNATURE": "false"})
    def test_escape_hatches(self):
        # Move to some state
        self.client.post(self.url, {'From': '+999', 'Body': 'Hola', 'MessageSid': '111'})
        conv = Conversation.objects.get(phone_number='+999')
        self.assertEqual(conv.bot_state, 'AWAITING_NAME')

        # Test CANCELAR
        response = self.client.post(self.url, {'From': '+999', 'Body': 'Cancelar', 'MessageSid': '222'})
        self.assertContains(response, "Operación cancelada.")
        
        conv.refresh_from_db()
        self.assertEqual(conv.bot_state, 'IDLE')
        self.assertEqual(conv.session_data, {})

        # Test AYUDA
        response = self.client.post(self.url, {'From': '+999', 'Body': 'AYUDA', 'MessageSid': '333'})
        self.assertContains(response, "Un operador humano se pondrá en contacto")
        
        conv.refresh_from_db()
        self.assertEqual(conv.status, 'PENDING_REVIEW')

    @patch.dict(os.environ, {"VALIDATE_TWILIO_SIGNATURE": "false"})
    def test_phase_4_case_creation_and_deduplication(self):
        # 1. New Case Creation
        conv1 = Conversation.objects.create(phone_number='+555', bot_state='AWAITING_ID', session_data={'name': 'Pedro'})
        self.client.post(self.url, {'From': '+555', 'Body': 'V-9999999', 'MessageSid': '444'})
        
        conv1.refresh_from_db()
        self.assertIsNotNone(conv1.case)
        self.assertEqual(conv1.case.missing_person.first_name, 'Pedro')
        self.assertEqual(conv1.case.missing_person.document_number, 'V-9999999')
        
        # 2. Deduplication
        conv2 = Conversation.objects.create(phone_number='+666', bot_state='AWAITING_ID', session_data={'name': 'Otro Pedro'})
        self.client.post(self.url, {'From': '+666', 'Body': 'V-9999999', 'MessageSid': '555'})
        
        conv2.refresh_from_db()
        self.assertIsNotNone(conv2.case)
        self.assertEqual(conv2.case.id, conv1.case.id) # Should link to same case
