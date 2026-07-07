from django.db import models

class Conversation(models.Model):
    CHANNEL_CHOICES = [
        ('WHATSAPP', 'WhatsApp')
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Activa'),
        ('PENDING_REVIEW', 'Pendiente por Revisión'),
        ('ARCHIVED', 'Archivada'),
    ]

    case = models.ForeignKey(
        'core.Case',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text="Caso asociado a esta conversación"
    )
    phone_number = models.CharField(max_length=50)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='WHATSAPP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    bot_state = models.CharField(max_length=50, default='IDLE', help_text="Estado actual en el flujo del menú")
    session_data = models.JSONField(default=dict, blank=True, help_text="Respuestas parciales del reportante")
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversación {self.channel} - {self.phone_number} (Caso #{self.case_id or 'Sin asignar'})"


class Message(models.Model):
    SENDER_CHOICES = [
        ('USER', 'Usuario / Familiar'),
        ('OPERATOR', 'Operador'),
        ('SYSTEM', 'Sistema / Bot'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    message = models.TextField()
    twilio_sid = models.CharField(max_length=100, blank=True, null=True, help_text="Identificador único del mensaje en Twilio")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje de {self.get_sender_display()} a las {self.created_at.strftime('%H:%M:%S')}"
