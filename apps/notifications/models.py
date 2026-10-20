from typing import Any
from django.db import models, transaction
from django.conf import settings
import threading
import requests


class Notification(models.Model):
    id: int
    pk: Any
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(max_length=50)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            payload = {
                'notification_id': self.id,
                'user_email': self.user.email,
                'user_name': self.user.get_full_name() or self.user.username,
                'title': self.title,
                'message': self.message,
                'priority': self.priority,
                'category': self.category
            }
            webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/send-notification')

            def send_to_n8n():
                try:
                    requests.post(webhook_url, json=payload, timeout=5)
                except Exception as e:
                    print(f"Failed to trigger N8N Webhook: {e}")

            transaction.on_commit(
                lambda: threading.Thread(target=send_to_n8n, daemon=True).start()
            )

    def __str__(self):
        return f"{self.title} - {self.user.username}"

