from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import CustomUser


@receiver(post_save, sender=CustomUser)
def send_buyer_welcome_email(sender, instance, created, **kwargs):
    if created and instance.user_type == "Buyer":
        subject = "Welcome to Sellbuypatent Portal"
        message = render_to_string(
            "email_templates/buyer_welcome.py",
            {
                "first_name": instance.first_name,
            },
        )

        email = EmailMessage(subject, message, to=[instance.email])
        email.content_subtype = "html"

        try:
            email.attach_file("static/nda_template.pdf")
            email.attach_file("static/nda_template.docx")
            email.send()
        except Exception as e:
            print(f"Error sending email: {e}")
