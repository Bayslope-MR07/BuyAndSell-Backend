# from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
# from allauth.socialaccount.providers.oauth2.client import OAuth2Client
# from dj_rest_auth.registration.views import SocialLoginView
# from django.conf import settings


# class GoogleLogin(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     client_class = OAuth2Client
#     callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from ..serializers import CustomSocialLoginSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import random
import string
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import CustomUser  # Your user model
from backend import settings
# from .email_template import WELCOME_EMAIL_SUBJECT, WELCOME_EMAIL_BODY
from django.core.mail import send_mail

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import os

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import os


def send_welcome_email(email, first_name):
    subject = "Welcome to BuySellAssist Portal"

    # ✅ Load HTML content from template
    message = render_to_string(
        "email_templates/buyer_welcome.py",
        {
            "first_name": first_name,
        },
    )

    # ✅ Send using EmailMessage
    email_msg = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    email_msg.content_subtype = 'html'  # 💥 Important: render HTML properly

    # ✅ Attach NDA files
    try:
        email_msg.attach_file(
            os.path.join(settings.BASE_DIR, "static", "nda_template.pdf")
        )
        email_msg.attach_file(
            os.path.join(settings.BASE_DIR, "static", "nda_template.docx")
        )
    except Exception as e:
        print("Attachment error:", e)

    email_msg.send()



def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

@api_view(['POST'])
def google_signup(request):
    token = request.data.get('token')
    phone_number = request.data.get('phone_number')
    user_type = request.data.get('user_type')

    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)

        email = idinfo['email']
        first_name = idinfo.get('given_name', '')  
        last_name = idinfo.get('family_name', '')

        # Check if user exists
        user, created = CustomUser.objects.get_or_create(email=email, defaults={
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'user_type': user_type,
            'password': generate_random_password()  # Set a random password
        })

        if not created:
            return Response({'message': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        send_welcome_email(email, first_name)
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

    except ValueError:
        return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLogin(SocialLoginView):
    serializer_class = CustomSocialLoginSerializer
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL
    client_class = OAuth2Client
    def get_response(self):
        original_response = super().get_response()
        user = self.user  # Get the authenticated user

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        # send_welcome_email(user.email, user.first_name)
        # Custom response with user details from CustomUser model
        response_data = {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "email": user.email or "",
            "is_admin": user.is_superuser,
            "user_type": user.user_type if hasattr(user, "user_type") else "Buyer",  # Default to "Buyer"
            "phone_no": user.phone_no if hasattr(user, "phone_no") else "",
            "message": "Login successful"
        }

        return Response(response_data, status=original_response.status_code)
