from django.urls import path
from django.conf import settings
from .views import TwilioWebhookView, ChatCreateAPIView, ChatDetailAPIView, SimulateBotMessageView, SimulateUserMessageView

urlpatterns = [
    path('webhook/', TwilioWebhookView.as_view(), name='twilio_webhook'),
    path('chat/', ChatCreateAPIView.as_view(), name='create_chat_api'),
    path('chat/<int:conversation_id>/', ChatDetailAPIView.as_view(), name='chat_detail_api'),
]

# Las vistas de prueba y simulación solo se exponen en entorno de desarrollo
if settings.DEBUG:
    urlpatterns += [
        path('chat/test/simulate/bot/', SimulateBotMessageView.as_view(), name='simulate_bot'),
        path('chat/test/simulate/user/', SimulateUserMessageView.as_view(), name='simulate_user'),
    ]
