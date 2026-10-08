from django.db import models
from django.conf import settings

class Notification(models.Model):
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
            import threading
            import requests
            
            def send_to_n8n():
                webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/send-notification')
                try:
                    payload = {
                        'notification_id': self.id,
                        'user_email': self.user.email,
                        'user_name': self.user.get_full_name() or self.user.username,
                        'title': self.title,
                        'message': self.message,
                        'priority': self.priority,
                        'category': self.category
                    }
                    requests.post(webhook_url, json=payload, timeout=5)
                except Exception as e:
                    print(f"Failed to trigger N8N Webhook: {e}")
                    
            threading.Thread(target=send_to_n8n, daemon=True).start()

    def __str__(self):
        return f"{self.title} - {self.user.username}"
