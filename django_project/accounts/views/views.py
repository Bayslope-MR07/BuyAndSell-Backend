from datetime import datetime
from itertools import count
import json
from django.http import JsonResponse
from rest_framework.views import APIView
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from ..serializers import FormUploadsSerializer, UserSerializer, LoginSerializer
import logging
import openpyxl
import csv
from datetime import datetime

# from .email_template import WELCOME_EMAIL_SUBJECT, WELCOME_EMAIL_BODY
from django.core.mail import send_mail
from backend import settings
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.contrib.auth import authenticate

# from rest_framework.views import APIView
# from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import LoginSerializer
import logging


from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import os
from django.conf import settings

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import os


def send_welcome_email(email, first_name):
    subject = "Welcome to Sellbuypatent Portal"

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
    email_msg.content_subtype = "html"  # 

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


from django.core.mail import send_mail
from django.conf import settings


def send_buyer_signup_email(email, first_name):
    subject = "Thank you for signing up - Sellbuypatent"
    message = (
        f"Hi {first_name},\n\n"
        "Thank you for signing up for the Sellbuypatent portal. "
        "We're reviewing your details and will activate the account shortly.\n\n"
        "Best regards,\n"
        "Sellbuypatent Team"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


logger = logging.getLogger(__name__)


class SignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_verified=False)

            user_type = (user.user_type or "").strip()

            if user_type == "Buyer":
                send_buyer_signup_email(user.email, user.first_name)

            else:    
                send_welcome_email(user.email, user.first_name)
            return Response(
                {"message": "User created successfully"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# UpdateUserView to update user details
from rest_framework.permissions import IsAuthenticated


class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User updated successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # 🔹 Hardcoded Admin Check
        if email == "sarita@gmail.com" and password == "admins":
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "Admin user not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Password verify भी कर सकते हो
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST
                )

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "is_admin": True,
                    "user_type": user.user_type,
                    "has_filled_seller_form": getattr(
                        user, "has_filled_seller_form", False
                    ),
                    "message": "Admin login successful",
                },
                status=status.HTTP_200_OK,
            )

        # 🔹 Normal login flow
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            requested_user_type = request.data.get("user_type")

            if requested_user_type and user.user_type != requested_user_type:
                return Response(
                    {
                        "error": "User type mismatch. Please use the correct login option."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # 🟢 BLOCK UNVERIFIED USERS
            if not user.is_verified:
                nda_template_url = (
                    "http://localhost:4200//static/nda_template.pdf"  # update as needed
                )
                return Response(
                    {
                        "error": "Not verified. Please upload signed NDA.",
                        "nda_template_url": nda_template_url,
                        "nda_uploaded": bool(user.nda_signed_file),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            user.has_filled_seller_form = SellerForm.objects.filter(user=user).exists()
            user.save()

            has_filled_buyer_form = BuyerForm.objects.filter(user=user).exists()

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "is_admin": user.is_admin,
                    "user_type": user.user_type,
                    "phone_no": user.phone_number,
                    "has_filled_seller_form": user.has_filled_seller_form,
                    "has_filled_buyer_form": has_filled_buyer_form,
                    "is_new_buyer": (
                        user.user_type == "Buyer" and not has_filled_buyer_form
                    ),
                    "message": "Login successful",
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        # Validate old password
        if not request.user.check_password(old_password):
            return Response(
                {"message": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate new password length
        if len(new_password) < 5:
            return Response(
                {"message": "New password must be at least 5 characters long"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        request.user.set_password(new_password)
        request.user.save()

        # Keep the user logged in after changing the password
        update_session_auth_hash(request, request.user)

        return Response(
            {"message": "Password updated successfully"}, status=status.HTTP_200_OK
        )


from django.views.decorators.cache import never_cache


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @never_cache  # Prevents caching of the logout response
    def post(self, request):
        # print("Headers:", request.headers)
        # print("Request Data:", request.data)

        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()
            # Set cache control headers
            response = Response(
                {"message": "Logout successful"}, status=status.HTTP_200_OK
            )
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            return response

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from ..serializers import SellerFormSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import SellerForm, FormUploads
from ..serializers import SellerFormSerializer

""" class SellerFormView(APIView):
    def post(self, request):
        serializer = SellerFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user) 
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 """
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..serializers import SellerFormSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..serializers import SellerFormSerializer

import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..serializers import SellerFormSerializer


from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
from datetime import datetime
from django.http import JsonResponse

# from .models import SellerForm, FormUploads
# from .serializers import FormUploadsSerializer

# Force logging to console
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
from datetime import datetime
from django.http import JsonResponse

# from .models import SellerForm, FormUploads
# from .serializers import FormUploadsSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
from datetime import datetime
from django.http import JsonResponse

# from .models import SellerForm, FormUploads
# from .serializers import FormUploadsSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
from datetime import datetime
from django.http import JsonResponse

# from .models import SellerForm, FormUploads
# from .serializers import FormUploadsSerializer

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
from datetime import datetime
from django.http import JsonResponse

# from .models import SellerForm, FormUploads
# from .serializers import FormUploadsSerializer

# Force logging to console
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import logging
import json
from datetime import datetime
from django.http import JsonResponse

# from .models import SellerForm, FormUploads
# from .serializers import FormUploadsSerializer

# Force logging to console
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from django.utils.crypto import get_random_string
import logging
import json
from datetime import datetime
from django.http import JsonResponse

# from .models import SellerForm, FormUploads
# from .serializers import FormUploadsSerializer

# Force logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from ..models import SellerForm, FormUploads, CustomUser  # ensure CustomUser import


from django.utils.crypto import get_random_string
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from ..models import CustomUser, SellerForm, FormUploads
from ..serializers import FormUploadsSerializer
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])  # 👈 JWT auth disable – public endpoint
def seller_form_submission(request):
    try:
        # 1) Data + files
        data = request.data.copy()  # QueryDict ka mutable copy
        files = request.FILES.getlist("file")
        data.pop("file", None)
        data.pop("name", None)

        patents_data = json.loads(data.get("patents", "[]"))
        data.pop("patents", None)

        # 2) Seller user create / fetch
        email = data.get("email")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        if not email:
            return JsonResponse({"error": "Email is required"}, status=400)

        user = CustomUser.objects.filter(email__iexact=email).first()
        created_user = False
        raw_password = None

        if user is None:
            raw_password = get_random_string(10)
            # create_user(email, user_type, password=None, **extra_fields)
            user = CustomUser.objects.create_user(
                email=email,
                user_type="Seller",
                password=raw_password,
                first_name=first_name,
                last_name=last_name,
            )
            user.is_verified = True  # agar sellers ko direct allow karna hai
            user.save()
            created_user = True
        else:
            # Agar pehle se Buyer hai to Both bana sakte ho
            if user.user_type == "Buyer":
                user.user_type = "Both"
                user.save()

        # 3) Dates parse
        deadline_str = data.get("deadline") or ""
        expiry_str = data.get("expiry") or ""

        deadline = (
            datetime.strptime(deadline_str, "%Y-%m-%d").date() if deadline_str else None
        )
        expiry = (
            datetime.strptime(expiry_str, "%Y-%m-%d").date() if expiry_str else None
        )

        # 4) SellerForm create – naya + kuch purane fields
        seller_form_data = {
            "user": user,
            "portfolio_type": data.get("portfolio_type"),
            "patent_owner_status": data.get("patent_owner_status"),
            "patent_owner_website": data.get("patent_owner_website"),
            "first_name": first_name,
            "last_name": last_name,
            "country": data.get("country", "Unknown"),
            "email": email,
            "phone": data.get("phone") or data.get("Contact"),
            "city": data.get("city"),
            "postal_code": data.get("postal_code"),
            "current_assignee_status": data.get("current_assignee_status"),
            "price_expectation": data.get("price_expectation"),
            "deadline": deadline,
            "expiry": expiry,
            "primary_technology": data.get("primary_technology"),
        }

        new_patent = SellerForm.objects.create(**seller_form_data)

        # 5) Patents JSON se agar kuch basic info rakhna hai (sirf agar fields model me hon)
        if patents_data:
            p0 = patents_data[0]
            if hasattr(new_patent, "patent_number"):
                new_patent.patent_number = p0.get("patent_number")
            if hasattr(new_patent, "application_number"):
                new_patent.application_number = p0.get("application_number")
            if hasattr(new_patent, "publication_number"):
                new_patent.publication_number = p0.get("publication_number")
            if hasattr(new_patent, "status"):
                new_patent.status = p0.get("status")
            if hasattr(new_patent, "google_patent_link"):
                new_patent.google_patent_link = p0.get("google_patent_link")
            new_patent.save()

        # 6) Files ko FormUploads me save karo
        uploaded_files_data = []
        for f in files:
            if not f.name or not f.size:
                continue
            fu = FormUploads.objects.create(patent=new_patent, file=f)
            uploaded_files_data.append(FormUploadsSerializer(fu).data)

        user.has_filled_seller_form = True
        user.save()

        # 7) Agar naya user bana hai to credentials email bhejo
        if created_user and raw_password:
            send_seller_credentials_email(user, raw_password)

        return JsonResponse(
            {
                "message": "Seller form submitted successfully. "
                "If this is your first time, your login details have been emailed.",
                "uploaded_files": uploaded_files_data,
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


# def seller_form_submission(request):

#     if request.method == 'POST':
#         try:
#             """ print(request.data) """


#             """ body = request.body.decode('utf-8', errors='replace')  # Replace invalid bytes """
#             """ data = json.loads(request.data)  """

#             # print(request.data)
#             x=request.data.dict()
#             # print(x)
#             uploaded_file = request.FILES.get('file')
#             x.pop('file',None)
#             x['patents']=json.loads(x['patents'])
#             deadline = datetime.strptime(x['deadline'], '%Y-%m-%d').date()
#             expiry = datetime.strptime(x['expiry'], '%Y-%m-%d').date()
#             user = request.user
#             for patent_data in x['patents']:
#                 new_patent = SellerForm(
#                     user=user,
#                     portfolio_type=x['portfolio_type'],
#                     patent_owner_status=x['patent_owner_status'],
#                     patent_owner_website=x['patent_owner_website'],
#                     first_name=x['first_name'],
#                     last_name=x['last_name'],

#                     email=x['email'],
#                     phone=x['phone'],
#                     city=x['city'],
#                     postal_code=x['postal_code'],
#                     current_assignee_status=x['current_assignee_status'],
#                     price_expectation=x['price_expectation'],
#                     deadline=deadline,
#                     expiry=expiry,
#                     primary_technology=x['primary_technology'],
#                     # Saving individual patent details here
#                     country=patent_data.get('country'),
#                     status=patent_data.get('status'),
#                     patent_number=patent_data.get('patent_number'),
#                     publication_number=patent_data.get('publication_number'),
#                     application_number=patent_data.get('application_number'),
#                     google_patent_link=patent_data.get('google_patent_link'),
#                     file=uploaded_file
#                 )
#                 new_patent.save()

#             return JsonResponse({"message": "Data submitted successfully!"}, status=201)
#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON data"}, status=400)


#     return JsonResponse({"message": "Invalid request method."}, status=405)

from rest_framework import generics, status
from rest_framework.response import Response
from ..models import SellerForm
from ..serializers import (
    SellerFormSerializer,
    SellerFormVerificationSerializer,
    BuyerViewSerializer,
)

""" 
class SellerFormCreateView(generics.CreateAPIView):
    queryset = SellerForm.objects.all()
    serializer_class = SellerFormSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED) """


class SellerFormListView(generics.ListAPIView):
    queryset = SellerForm.objects.all()
    serializer_class = SellerFormSerializer


class SellerFormListViewPerUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:

            user = request.user  # Get user from JWT token
            seller_forms = SellerForm.objects.filter(user=user)
            serializer = SellerFormSerializer(seller_forms, many=True)
            # return Response(serializer.data)
            return Response({"data": serializer.data}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


""" class SellerFormVerificationView(generics.UpdateAPIView):
    queryset = SellerForm.objects.filter(verified=False)
    serializer_class = SellerFormVerificationSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK) """


class VerifySellerView(APIView):
    def patch(self, request, pk):
        try:
            seller = SellerForm.objects.get(pk=pk)
        except SellerForm.DoesNotExist:
            return Response(
                {"error": "Seller not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = SellerFormVerificationSerializer(
            seller, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Seller verification updated successfully!"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import generics
from ..models import SellerForm
from ..serializers import BuyerViewSerializer


class BuyerViewList(generics.ListAPIView):
    serializer_class = BuyerViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        status = self.request.query_params.get("status")
        exclusive = self.request.query_params.get("exclusive")

        if status == "1":
            return SellerForm.objects.filter(
                # verified=True,
                feedback__buyer=user,
                feedback__action__in=["Pursue", "Pass"],
                # ver/ified=True,
                # feedback__buyer=user,
                # feedback__action="Chase"
            ).distinct()
        elif status in ["2", "3", "4"]:
            # ✅ Filter based on specific action
            action_map = {
                "2": "Pursue",
                "3": "Pass",
                "4": "Delay",
            }
            return SellerForm.objects.filter(
                verified=True, feedback__buyer=user, feedback__action=action_map[status]
            ).distinct()
        # return SellerForm.objects.filter(verified=True).order_by("-id")  # Latest first
        return SellerForm.objects.all().order_by("-id")

    def list(self, request, *args, **kwargs):
        download = request.query_params.get("download")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        if download == "true":
            return self.download_excel(serializer.data)

        return Response(serializer.data)

    def download_excel(self, data):
        rows = []
        for item in data:
            feedback = item.get("user_feedback", {})
            timestamp = feedback.get("timestamp", None)

            if timestamp:
                try:
                    dt = pd.Timestamp(timestamp)
                    if dt.tz is not None:
                        dt = dt.tz_localize(None)  # Remove timezone
                    timestamp = dt
                except Exception:
                    timestamp = None

            rows.append(
                {
                    "Patent Number": item.get("patent_number", ""),
                    "Title": item.get("title", ""),
                    "Primary Technology": item.get("primary_technology", ""),
                    "Verified": "Yes" if item.get("verified") else "No",
                    "Important": "Yes" if item.get("important") else "No",
                    "User Feedback Action": feedback.get("action", "N/A"),
                    "User Feedback Timestamp": timestamp,
                }
            )

        df = pd.DataFrame(rows)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="patents_data.xlsx"'

        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Patents Data")

        return response


from rest_framework import generics
from ..models import SellerForm
from ..serializers import BuyerViewSerializer


class BuyerViewDetail(generics.RetrieveAPIView):
    queryset = (
        SellerForm.objects.all()
    )  # Fetching all SellerForms to access a specific one
    serializer_class = BuyerViewSerializer
    lookup_field = "id"  # Ensures the ID parameter is used to look up the object
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get_queryset(self):
        """Filter feedback to show only the logged-in user's choice for a particular patent"""
        user = self.request.user
        return SellerForm.objects.filter(id=self.kwargs["id"]).prefetch_related(
            "feedback"
        )

    def get_serializer_context(self):
        """Pass the logged-in user to the serializer"""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import SellerForm, PatentFeedback
from ..serializers import PatentFeedbackSerializer


class BuyerActionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        buyer = request.user
        patent_id = request.data.get("id")
        action = request.data.get("action")

        if action not in ["Pursue", "Pass", "Delay"]:
            return Response({"error": "Invalid action."}, status=400)

        try:
            patent = SellerForm.objects.get(id=patent_id)
        except SellerForm.DoesNotExist:
            return Response({"error": "Patent not found."}, status=404)

        buyer_action = PatentFeedback.objects.create(
            buyer=buyer,
            patent=patent,
            action=action,
        )

        serializer = PatentFeedbackSerializer(buyer_action)
        return Response(serializer.data, status=201)


from django.http import JsonResponse
from django.views import View
from ..models import SellerForm, PatentFeedback


from django.http import HttpResponse, JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import pandas as pd


class SellerDataView(View):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get sellers based on status filter
        if request.GET.get("status") == "1":
            sellers = SellerForm.objects.filter(verified=False)
        else:
            sellers = SellerForm.objects.all()

        sellers_list = list(
            sellers.values(
                "id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "country",
                "city",
                "primary_technology",
                "price_expectation",
                "important",
                "verified",
                "additional_notes",
                "patent_number",
            )
        )

        # Handle Excel download
        if "download" in request.GET and request.GET["download"].lower() == "true":
            df = pd.DataFrame(sellers_list)
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="seller_data.xlsx"'

            with pd.ExcelWriter(response, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Sellers Data")

            return response

        return JsonResponse(sellers_list, safe=False)


import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..models import SellerForm

import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..models import SellerForm, CustomUser
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models import SellerForm, CustomUser
from datetime import datetime
from django.db import transaction


# Converts booleans, handling empty or NaN values gracefully
def clean_boolean(value):
    if pd.isna(value) or value in [None, "nan", "", "NaN"]:
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ["true", "yes", "1"]
    return None


import logging

# from django.db import transaction
# import pandas as pd

logger = logging.getLogger(__name__)


def process_chunk(chunk):
    results = {"created": 0, "updated": 0, "errors": []}

    try:
        # Clean column names
        chunk.columns = chunk.columns.str.strip()

        seller_forms = []

        # Existing patent numbers to decide update/create
        existing_patent_numbers = set(
            SellerForm.objects.filter(
                patent_number__in=[
                    str(patent).upper()
                    for patent in chunk["Parent Patent Number"].unique()
                ]
            ).values_list("patent_number", flat=True)
        )

        for idx, row in chunk.iterrows():
            try:
                email = row.get("Email", None)
                user = None
                if email:
                    try:
                        user = CustomUser.objects.get(email=email)
                    except CustomUser.DoesNotExist:
                        user = None

                # Convert dates safely
                expiry = (
                    pd.to_datetime(row.get("Expiry Date"), errors="coerce")
                    if "Expiry Date" in chunk.columns
                    else None
                )
                filing_date = (
                    pd.to_datetime(row.get("Filing Date"), errors="coerce")
                    if "Filing Date" in chunk.columns
                    else None
                )
                grant_date = (
                    pd.to_datetime(row.get("Grant Date"), errors="coerce")
                    if "Grant Date" in chunk.columns
                    else None
                )
                priority = (
                    pd.to_datetime(row.get("Priority Date"), errors="coerce")
                    if "Priority Date" in chunk.columns
                    else None
                )
                deadline = (
                    pd.to_datetime(row.get("Deadline"), errors="coerce")
                    if "Deadline" in chunk.columns
                    else None
                )

                # Boolean conversion helper
                def to_bool(val):
                    if isinstance(val, str):
                        return val.strip().lower() in ["true", "1", "yes", "y"]
                    return bool(val)

                seller = SellerForm(
                    user=user,
                    patent_number=str(
                        row.get("Parent Patent Number", "Unknown")
                    ).upper(),
                    expiry=expiry if pd.notnull(expiry) else None,
                    priority=priority if pd.notnull(priority) else None,
                    bay_identification_code=row.get(
                        "Bay Identification Code", "Unknown"
                    ),
                    tech_domain=row.get("Tech Domain", "Unknown"),
                    number_of_patents=int(row.get("Number of Patents", 0) or 0),
                    number_of_patent_families=int(
                        row.get("Number of Patent families", 0) or 0
                    ),
                    buying_options=row.get("Buying Options", "Skip"),
                    acquisition_status=row.get("Status of Acquisition", "Open"),
                    exclusive=to_bool(row.get("Exclusive", False)),
                    analysis_sheet=None,
                    claim_charts=None,
                    bay_overall_rating=row.get("Bay rating", "Medium"),
                    market_relevance=row.get("Market Relevance", "Medium"),
                    ip_type=row.get("IP Type", ""),
                    enforceability=row.get("Enforceability", "Medium"),
                    target=row.get("Targets", ""),
                    entity_status=row.get("Entity Status", "Micro"),
                    upcoming_fees=row.get("Upcoming Fees | USPTO", ""),
                    title=row.get("Title", ""),
                    abstract=row.get("Abstract", ""),
                    first_claim=row.get("First Claim", ""),
                    filing_date=filing_date if pd.notnull(filing_date) else None,
                    grant_date=grant_date if pd.notnull(grant_date) else None,
                    current_assignee=row.get("Current Assignee", ""),
                    family_members=row.get("Family Members", "Single"),
                    concepts=row.get("Technology Concepts", ""),
                    keywords=row.get("Technology Keywords", ""),
                    technologies=row.get("Technologies", ""),
                    spoc_company=row.get("Spoc Company", ""),
                    company_name=row.get("Company Name", ""),
                    admin_contact=row.get("Contact", ""),
                    admin_email=row.get("Email", ""),
                    portfolio_type=row.get("Portfolio Type", "Unknown"),
                    patent_owner_status=row.get("Patent Owner Status", "Unknown"),
                    patent_owner_website=row.get("Patent Owner Website", ""),
                    first_name=row.get("First Name", "Unknown"),
                    last_name=row.get("Last Name", "Unknown"),
                    country=row.get("Country", "Unknown"),
                    email=row.get("Email", "sarita@bayslope.com"),
                    phone=row.get("Contact", "+91-9811967160"),
                    city=row.get("City", "Unknown"),
                    postal_code=row.get("Postal Code", "000000"),
                    current_assignee_status=row.get("Current Assignee Status", "No"),
                    price_expectation=row.get("Price Expectation", "Negotiable"),
                    deadline=deadline if pd.notnull(deadline) else None,
                    primary_technology=row.get("Primary Technology", "Unknown"),
                    application_number=row.get("Application Number", "Unknown"),
                    publication_number=row.get("Publication Number", "Unknown"),
                    status=row.get("Status", "Unknown"),
                    google_patent_link=row.get("Google Patent Link", ""),
                    file=None,
                    verified=True,
                    important=False,
                    additional_notes=row.get("AdditionalNotes", ""),
                    portfolio_code=row.get("Portfolio Code", "Unknown"),
                    industry=row.get("Industry", "Unknown"),
                    relevant_companies=row.get("Relevant Companies", ""),
                    assertability_strength=row.get(
                        "Assertability | Licensing strength", "Medium"
                    ),
                    seller_interest=row.get("Seller interest", ""),
                    reason_of_selling=row.get("Reason of Selling", ""),
                    encumbrances=row.get("Encumbrances", "None"),
                    seller_jurisdiction=row.get("Seller Jurisdiction", ""),
                )

                seller_forms.append((idx, seller))

            except Exception as row_err:
                logger.error(f"❌ Error at row {idx}: {row_err}")
                results["errors"].append(
                    {"row_index": idx, "row_data": row.to_dict(), "error": str(row_err)}
                )

        with transaction.atomic():
            to_update = SellerForm.objects.filter(
                patent_number__in=existing_patent_numbers
            )
            update_map = {s.patent_number: s for s in to_update}

            new_forms = []
            for idx, s in seller_forms:
                try:
                    if s.patent_number in existing_patent_numbers:
                        existing = update_map[s.patent_number]
                        for field in SellerForm._meta.fields:
                            field_name = field.name
                            if field_name != "id" and hasattr(s, field_name):
                                setattr(existing, field_name, getattr(s, field_name))
                        existing.save()
                        results["updated"] += 1
                    else:
                        new_forms.append(s)
                except Exception as update_err:
                    logger.error(f"❌ Update error at row {idx}: {update_err}")
                    results["errors"].append(
                        {
                            "row_index": idx,
                            "row_data": s.__dict__,
                            "error": str(update_err),
                        }
                    )

            if new_forms:
                try:
                    SellerForm.objects.bulk_create(new_forms)
                    results["created"] += len(new_forms)
                except Exception as bulk_err:
                    logger.error(f"❌ Bulk create error: {bulk_err}")
                    results["errors"].append({"bulk_create_error": str(bulk_err)})

    except Exception as e:
        logger.exception("❗ Exception in process_chunk")
        results["errors"].append({"chunk_level_error": str(e)})

    return results


import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.files.base import ContentFile
import zipfile
import tempfile
import os

# from .models import SellerForm
# from .utils import process_chunk

import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

logger = logging.getLogger(__name__)


import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

logger = logging.getLogger(__name__)


import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

logger = logging.getLogger(__name__)


# def is_valid_excel(data):
#     """A simple check to see if the file is a valid Excel (zip file with correct internal structure)."""
#     try:
#         with zipfile.ZipFile(BytesIO(data), "r") as z:
#             return "xl/workbook.xml" in z.namelist()
#     except zipfile.BadZipFile:
#         return False


import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream

# from django.core.files.base import ContentFile
import uuid

logger = logging.getLogger(__name__)

import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

import zipfile
import os
import uuid
import logging
from io import BytesIO

import olefile

# from oletools.olevba import OleNativeStream
from io import BytesIO
import binascii

import zipfile
import os
import uuid
import logging
from io import BytesIO
import binascii

import olefile

# import olefile
from oletools.oleobj import OleNativeStream
import binascii

# from oletools.olevba import OleNativeStream

logger = logging.getLogger(__name__)


import olefile
from io import BytesIO
import os
import zipfile

import zipfile
import os


import os
import zipfile
import olefile
from io import BytesIO

# from oletools.oleobj import OleNativeStream
import logging

logger = logging.getLogger(__name__)

import zipfile

# import olefile
import zipfile
import olefile
import os
from io import BytesIO
import logging

# from oletools.olevba import OleNativeStream
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

import zipfile
import olefile
import os
from io import BytesIO
import logging
import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

logger = logging.getLogger(__name__)


import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

import zipfile
import olefile
import os
from io import BytesIO
import logging
from oletools.oleobj import OleNativeStream
from django.core.files.base import ContentFile
import uuid

logger = logging.getLogger(__name__)


import zipfile
import olefile
import os
from io import BytesIO
import logging

# from oletools.olevba import OleNativeStream
from django.core.files.base import ContentFile
import uuid
import zipfile
import olefile
import os
from io import BytesIO
import logging

# from oletools.olevba import OleNativeStream
import zipfile
import olefile
import os
import uuid
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


# def is_valid_excel(data: bytes) -> bool:
#     """Quick check if data looks like a valid Excel file (ZIP based)."""
#     try:
#         with zipfile.ZipFile(BytesIO(data), "r") as zf:
#             return any(name.startswith("xl/") for name in zf.namelist())
#     except Exception:
#         return False


import os
import uuid
import zipfile
from io import BytesIO
import olefile
import logging
from openpyxl import load_workbook
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


def clean_excel(data: bytes) -> bytes:
    """
    Ensure the Excel file is properly saved with openpyxl
    so it doesn’t appear blank after download.
    """
    try:
        with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(data)
            tmp.flush()
            tmp_path = tmp.name

        wb = load_workbook(tmp_path)
        buffer = BytesIO()
        wb.save(buffer)
        wb.close()
        os.remove(tmp_path)
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        logger.error(f"❌ Failed to clean Excel: {e}")
        return data  # fallback to raw


def extract_embedded_files(file_path):
    """Extract embedded PDF/Excel/OLE files from an Excel workbook."""
    embedded_files = []
    try:
        with zipfile.ZipFile(file_path, "r") as zipf:
            for name in zipf.namelist():
                if name.startswith("xl/embeddings/"):
                    with zipf.open(name) as bin_file:
                        data = bin_file.read()
                        logger.info(
                            f"Processing embedded file: {name} (size: {len(data)} bytes)"
                        )

                        if data.startswith(b"PK") and is_valid_excel(data):
                            filename = f"embedded_{uuid.uuid4().hex[:8]}.xlsx"
                            logger.info(f"📊 Extracted Excel: {filename}")
                            cleaned = _repair_excel_resave_openpyxl(data) or data
                            embedded_files.append((filename, cleaned))

        logger.info(f"📎 Final extracted files: {[f[0] for f in embedded_files]}")
    except Exception as e:
        logger.error(f"❌ Error processing {file_path}: {e}")
    return embedded_files


import os
import magic  # Make sure this is installed: pip install python-magic-bin on Windows
from django.core.files.base import ContentFile


import os

# import magic
import logging

# from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)  # ✅ Django logger le lo


from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def is_valid_excel(file_data: bytes) -> bool:
    """Quick check if bytes look like a valid Excel (xlsx)."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=True) as tmp:
            tmp.write(file_data)
            tmp.flush()
            load_workbook(tmp.name)
        return True
    except Exception:
        return False


import os
import uuid
import tempfile
from io import BytesIO
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from django.core.files import File
from django.core.files.base import ContentFile


import tempfile
import pandas as pd
import os


import os
import uuid
import tempfile
from io import BytesIO
from pathlib import Path
import logging

import pandas as pd
from openpyxl import load_workbook
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


# --- Helpers ---

import os, tempfile, zipfile, logging
import pandas as pd
from openpyxl import load_workbook
from io import BytesIO

logger = logging.getLogger(__name__)


from pathlib import Path
import uuid
import os
import logging
from io import BytesIO
import zipfile
import re
import pandas as pd
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def _excel_has_data(file_data: bytes) -> bool:
    """Check if Excel has at least some non-empty cells."""
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as f:
            f.write(file_data)
            tmp = f.name

        df = pd.read_excel(tmp, engine="openpyxl")
        df = df.dropna(how="all")
        return not df.empty
    except Exception as e:
        logger.error(f"❌ Excel validation failed: {e}")
        return False
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def _repair_excel_resave_openpyxl(file_data: bytes):
    """Try to reload and resave Excel using openpyxl."""
    try:
        bio = BytesIO(file_data)
        wb = load_workbook(bio, data_only=True)
        out = BytesIO()
        wb.save(out)
        return out.getvalue()
    except Exception as e:
        logger.error(f"❌ OpenPyXL repair failed: {e}")
        return None


def _rebuild_values_only_with_pandas(file_data: bytes):
    """Rebuild Excel with just values using pandas."""
    try:
        df = pd.read_excel(BytesIO(file_data), engine="openpyxl")
        if df.empty:
            return None
        out = BytesIO()
        df.to_excel(out, index=False)
        return out.getvalue()
    except Exception as e:
        logger.error(f"❌ Pandas rebuild failed: {e}")
        return None


def _try_extract_ole(file_data, base_name):
    """Try to extract real Excel content from OLE container (for small ~10KB files)."""
    try:
        import olefile

        ole = olefile.OleFileIO(BytesIO(file_data))
        for stream in ole.listdir():
            if "Package" in stream or "Workbook" in stream:
                extracted = ole.openstream(stream).read()
                if extracted:
                    logger.info(f"✅ OLE stream extracted: {stream}")
                    return extracted
        logger.warning("⚠️ No valid Excel stream found inside OLE container")
        return None
    except Exception as e:
        logger.error(f"❌ OLE extraction failed: {e}")
        return None


def _extract_xml_values(file_data: bytes):
    """Extract raw text/values from Excel XML fallback."""
    rows = []
    try:
        with zipfile.ZipFile(BytesIO(file_data)) as z:
            xml_files = [f for f in z.namelist() if f.startswith("xl/worksheets/")]
            for xml_file in xml_files:
                data = z.read(xml_file).decode("utf-8", errors="ignore")
                values = re.findall(r"<v>(.*?)</v>|<t>(.*?)</t>", data)
                if values:
                    row = [v[0] or v[1] for v in values]
                    rows.append(row)
    except Exception as e:
        logger.error(f"❌ XML extraction failed: {e}")
    return rows


def save_embedded_to_seller(embedded_files, seller):
    for filename, file_data in embedded_files:
        ext = Path(filename).suffix.lower()
        unique_name = f"{Path(filename).stem}_{uuid.uuid4().hex[:6]}{ext}"
        if ext == ".xlsx":
            logger.info(f"📊 Saving Excel to seller.analysis_sheet: {unique_name}")
            seller.analysis_sheet.save(unique_name, ContentFile(file_data), save=False)
    seller.save()
    logger.info(f"✅ Seller {getattr(seller, 'id', '?')} updated with embedded files.")


from rest_framework.decorators import api_view
from rest_framework.response import Response

# from .models import SellerForm


@api_view(["GET"])
def get_embedded_file_urls(request, seller_id):
    try:
        seller = SellerForm.objects.get(id=seller_id)

        embedded_files = []

        if seller.claim_charts:
            embedded_files.append(
                {
                    "name": seller.claim_charts.name.split("/")[-1],
                    "type": "pdf",
                    "url": request.build_absolute_uri(seller.claim_charts.url),
                }
            )

        if seller.analysis_sheet:
            embedded_files.append(
                {
                    "name": seller.analysis_sheet.name.split("/")[-1],
                    "type": "excel",
                    "url": request.build_absolute_uri(seller.analysis_sheet.url),
                }
            )

        return Response({"embedded_files": embedded_files})

    except SellerForm.DoesNotExist:
        return Response({"error": "Seller not found"}, status=404)


from openpyxl.utils.exceptions import InvalidFileException
import os
import tempfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

import logging
import os
import tempfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


logger = logging.getLogger(__name__)


import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


import os
import tempfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


import os
import tempfile
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging
import gc

logger = logging.getLogger(__name__)


import os
import tempfile
import pandas as pd
import logging
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_excel(request):
    temp_path = None
    try:
        if "file" not in request.FILES:
            logger.error("❌ No file provided in request")
            return JsonResponse({"error": "No file provided"}, status=400)

        upload_file = request.FILES["file"]
        if not upload_file.name.lower().endswith((".xlsx", ".xls")):
            logger.error(f"❌ Invalid file type: {upload_file.name}")
            return JsonResponse(
                {"error": "Only Excel (.xlsx, .xls) files are supported"}, status=400
            )

        # Read file into memory
        file_data = bytearray()
        for chunk in upload_file.chunks(chunk_size=1048576):
            file_data.extend(chunk)
        logger.info(
            f"📂 File read into memory: {upload_file.name}, size: {len(file_data)} bytes"
        )

        looks_ok = _excel_has_data(file_data)
        final_bytes = file_data
        if not looks_ok:
            logger.info(f"⚠️ Attempting repair for {upload_file.name}")
            fixed_bytes = _repair_excel_resave_openpyxl(file_data)
            if fixed_bytes and _excel_has_data(fixed_bytes):
                final_bytes = fixed_bytes
                logger.info(f"✅ OpenPyXL repair succeeded for {upload_file.name}")
            else:
                rebuilt = _rebuild_values_only_with_pandas(file_data)
                if rebuilt and _excel_has_data(rebuilt):
                    final_bytes = rebuilt
                    logger.info(f"✅ Pandas rebuild succeeded for {upload_file.name}")
                else:
                    logger.warning(
                        f"❌ File {upload_file.name} has no meaningful data after repair"
                    )
                    return JsonResponse(
                        {"error": "No meaningful data in file after repair"}, status=400
                    )

        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(final_bytes)
            tmp.flush()
            temp_path = tmp.name
        logger.info(f"📂 Temporary file saved at {temp_path}")

        # Read DataFrame from Excel
        df = pd.DataFrame()
        with pd.ExcelFile(temp_path, engine="openpyxl") as xls:
            for sheet_name in xls.sheet_names:
                for header_row in range(4):  # Check first 4 rows for headers
                    temp_df = pd.read_excel(
                        xls, sheet_name=sheet_name, header=header_row, engine="openpyxl"
                    )
                    temp_df = temp_df.dropna(how="all").dropna(axis=1, how="all")
                    temp_df.columns = temp_df.columns.astype(str).str.strip()
                    temp_df = temp_df.loc[:, ~temp_df.columns.str.contains("^Unnamed")]
                    if not temp_df.empty and any(
                        any(
                            keyword.lower() in col.lower()
                            for keyword in ["s.no.", "patent", "title"]
                        )
                        for col in temp_df.columns
                    ):
                        df = pd.concat([df, temp_df], ignore_index=True)
                        logger.info(
                            f"✅ Headers found at row {header_row + 1} in sheet {sheet_name}: {df.columns.tolist()}"
                        )
                        break
                if not df.empty:
                    break

        if df.empty:
            logger.error("❌ No valid headers or data found in file")
            return JsonResponse({"error": "No valid data found"}, status=400)

        logger.info(f"📊 DataFrame shape: {df.shape}")

        # -------------------------
        # ✅ Save Data into SellerForm
        # -------------------------
        # from ..models import SellerForm

        created, updated = 0, 0

        for _, row in df.iterrows():
            portfolio_code = str(row.get("Portfolio Code", "")).strip()

            seller, is_created = SellerForm.objects.update_or_create(
                portfolio_code=portfolio_code,
                defaults={
                    "sr_no": row.get("S.No.", None),
                    "industry": row.get("Industry", ""),
                    "tech_domain": row.get("Tech Domain", ""),
                    "technology_tags": row.get("Technology Tags", ""),
                    "portfolio_coverage": row.get("Portolfio Coverage", ""),
                    "number_of_patents": row.get("Number of Patents", 0),
                    "number_of_patent_families": row.get(
                        "Number of Patent families", 0
                    ),
                    "patent_geographies": row.get("Patent Geographies", ""),
                    "sep_patent": row.get("SEP patent", ""),
                    "any_ongoing_continuation": row.get("Any Open continuation?", ""),
                    "portfolio_sold_before": row.get(
                        "Any portion of the portfolio sold before?", ""
                    ),
                    "upcoming_fees": row.get("Upcoming Fees", ""),
                    "patents_status": row.get("Patents Status", ""),
                    "seller_entity": row.get("Seller Entity", ""),
                    "seller_entity_status": row.get("Seller Entity Status", ""),
                    "seller_country": row.get("Seller Country", ""),
                    "monetization_preference": row.get(
                        "Seller Monetization Preference", ""
                    ),
                    "monetization_strategy": row.get(
                        "Seller Monetization Strategy Preference", ""
                    ),
                    "willingness_to_negotiate": row.get(
                        "Seller’s Willingness to Negotiate", ""
                    ),
                    "encumbrances": row.get("Encumbrances", "None"),
                    "previous_history_selling": row.get(
                        "Previous history of selling or licensing of the seller", ""
                    ),
                    "diligence_material": row.get("Diligence Material", ""),
                    "number_of_relevant_companies": row.get(
                        "Number of Relevant companies", ""
                    ),
                    "relevant_companies": row.get("Relevant Companies", ""),
                    "number_of_charts": row.get("Number of Charts", ""),
                    "product_matching": row.get("Patent Product Matrix", ""),
                    "standard_mapping": row.get("Standard Mapping", ""),
                    "product_categories": row.get("Products Category", ""),
                    "market_size": row.get("Market size of products", ""),
                    "dominant_litigation": row.get(
                        "Any landmark litigation in the space", "NA"
                    ),
                    "timeline_offer": row.get("Timeline to receiver offer", ""),
                    "comments": row.get("Comments", ""),
                    "acquisition_status": row.get("Acquisition Status", "Open"),
                    "portfolio_rating": row.get("Portfolio Rating", "Medium"),
                    "buying_options": row.get("Buying Options", "Skip"),
                    "phone": row.get("Phone", ""),
                    "email": row.get("Email", ""),
                    "spoc_company": row.get("Spoc Company", ""),
                    "exclusive": str(row.get("Exclusive", "")).strip().lower() == "yes",
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        logger.info(f"📊 SellerForm updated -> Created: {created}, Updated: {updated}")

        # Save processed file
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        processed_file_data = output.getvalue()

        media_path = f"analysis_sheets/processed_{os.path.basename(upload_file.name)}"
        if default_storage.exists(media_path):
            default_storage.delete(media_path)
        saved_path = default_storage.save(media_path, ContentFile(processed_file_data))
        saved_file_url = default_storage.url(saved_path)

        logger.info(f"💾 File saved at {saved_path}")

        return JsonResponse(
            {
                "message": "Main Excel processed & sellers updated!",
                "created": created,
                "updated": updated,
                "file_url": saved_file_url,
            },
            status=200,
        )

    except Exception as e:
        logger.exception("❗ Critical error processing upload")
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"🗑️ Removed temporary file {temp_path}")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove {temp_path}: {e}")
        gc.collect()


import zipfile
import re

# views.py
import re
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

# from .models import SellerForm  # ensure your SellerForm is imported


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_embedded(request):
    try:
        if "file" not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)

        upload_file = request.FILES["file"]
        filename = upload_file.name

        # ---------- CASE 1: EXCEL (Analysis Sheet) ----------
        if filename.lower().endswith((".xlsx", ".xls")):
            # Extract portfolio name (example: Bay_infringement_Marc.xlsx -> Marc)
            portfolio_code = None
            parts = filename.replace(".xlsx", "").replace(".xls", "").split("_")
            if len(parts) >= 2:
                portfolio_code = parts[-1]  # last part is portfolio code (Marc)

            if not portfolio_code:
                return JsonResponse(
                    {"error": "Portfolio code not found in filename"}, status=400
                )

            seller = SellerForm.objects.filter(
                portfolio_code__icontains=portfolio_code
            ).first()

            if not seller:
                return JsonResponse(
                    {"error": f"No Seller found for portfolio {portfolio_code}"},
                    status=404,
                )

            seller.analysis_sheet.save(filename, upload_file)
            seller.save()
            return JsonResponse(
                {
                    "message": f"Excel attached to {seller.portfolio_code}",
                    "seller_id": seller.id,
                },
                status=200,
            )

        # ---------- CASE 2: PDF (Claim Chart) ----------
        elif filename.lower().endswith(".pdf"):
            match = re.search(
                r"(US\d+[A-Z]?\d*|EP\d+[A-Z]?\d*|WO\d+[A-Z]?\d*)",
                filename,
                re.IGNORECASE,
            )
            patent_number = match.group(0) if match else None

            if not patent_number:
                return JsonResponse(
                    {"error": "Patent number not found in filename"}, status=400
                )

            seller = SellerForm.objects.filter(
                Q(patent_number__icontains=patent_number)
                | Q(parent_patent_number__icontains=patent_number)
            ).first()

            if not seller:
                return JsonResponse(
                    {"error": f"No Seller found for patent {patent_number}"}, status=404
                )

            seller.claim_charts.save(filename, upload_file)
            seller.save()
            return JsonResponse(
                {
                    "message": f"PDF attached to patent {seller.patent_number}",
                    "seller_id": seller.id,
                },
                status=200,
            )

        # ---------- CASE 3: WORD (Agreements or Docs) ----------
        elif filename.lower().endswith((".docx", ".doc")):
            match = re.search(
                r"(US\d+[A-Z]?\d*|EP\d+[A-Z]?\d*|WO\d+[A-Z]?\d*)",
                filename,
                re.IGNORECASE,
            )
            patent_number = match.group(0).upper() if match else None

            seller = None
            if patent_number:
                seller = SellerForm.objects.filter(
                    Q(patent_number__icontains=patent_number)
                    | Q(parent_patent_number__icontains=patent_number)
                ).first()

            if not seller:
                parts = re.split(
                    r"[_\s]+", filename.replace(".docx", "").replace(".doc", "")
                )
                for part in parts:
                    seller = SellerForm.objects.filter(
                        Q(portfolio_code__iexact=part)
                    ).first()
                    if seller:
                        break

            if not seller:
                return JsonResponse(
                    {"error": f"No Seller found for {patent_number or filename}"},
                    status=404,
                )

            seller.word_docs.save(filename, upload_file)
            seller.save()
            return JsonResponse(
                {
                    "message": f"Word file attached to {seller.portfolio_code or seller.patent_number}",
                    "seller_id": seller.id,
                },
                status=200,
            )

        # ---------- CASE 4: ZIP FILE (Multiple documents, archives) ----------
        elif filename.lower().endswith(".zip"):
            # Extract portfolio code or patent number (similar pattern)
            match = re.search(
                r"(US\d+[A-Z]?\d*|EP\d+[A-Z]?\d*|WO\d+[A-Z]?\d*)",
                filename,
                re.IGNORECASE,
            )
            patent_number = match.group(0) if match else None
            portfolio_code = None

            if not patent_number:
                parts = filename.replace(".zip", "").split("_")
                if len(parts) >= 2:
                    portfolio_code = parts[-1]

            # Find the seller based on patent or portfolio
            seller = None
            if patent_number:
                seller = SellerForm.objects.filter(
                    Q(patent_number__icontains=patent_number)
                    | Q(parent_patent_number__icontains=patent_number)
                ).first()
            elif portfolio_code:
                seller = SellerForm.objects.filter(
                    portfolio_code__icontains=portfolio_code
                ).first()

            if not seller:
                return JsonResponse(
                    {
                        "error": f"No Seller found for {patent_number or portfolio_code or filename}"
                    },
                    status=404,
                )

            # ⚡️ Make sure your model has a FileField for zip uploads, e.g. seller.zip_files
            seller.zip_files.save(filename, upload_file)
            seller.save()
            return JsonResponse(
                {
                    "message": f"ZIP file attached to {seller.portfolio_code or seller.patent_number}",
                    "seller_id": seller.id,
                },
                status=200,
            )

        else:
            return JsonResponse(
                {
                    "error": "Only Excel (.xlsx, .xls), PDF, Word (.docx, .doc), or ZIP files supported"
                },
                status=400,
            )

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..serializers import BuyerActionSerializer


@api_view(["GET"])
def get_buyer_actions(request):
    actions = PatentFeedback.objects.all()
    serializer = BuyerActionSerializer(actions, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_buyer_actions_byId(request, id):
    actions = PatentFeedback.objects.filter(patent__id=id)
    serializer = BuyerActionSerializer(actions, many=True)
    return Response(serializer.data)


from django.db.models.functions import Lower


class PatentAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Define a case-insensitive filter to exclude null, empty, and invalid values
            exclude_invalid = Q(primary_technology__isnull=False) & ~Q(
                primary_technology__in=["", "nan", "na", "none"]
            )

            # Get total unique patents
            total_patents = (
                SellerForm.objects.exclude(patent_number__isnull=True)
                .values("patent_number")
                .distinct()
                .count()
            )

            # Function to get unique counts with case-insensitive grouping
            def get_count_dict(field_name):
                return (
                    SellerForm.objects.exclude(**{field_name + "__isnull": True})
                    .exclude(**{field_name + "__in": ["", "nan", "na", "none"]})
                    .annotate(lower_field=Lower(field_name))  # Convert to lowercase
                    .values("lower_field")
                    .annotate(count=Count("id"))
                    .order_by()
                )

            # Feedback-based analytics
            chased_patents = (
                PatentFeedback.objects.filter(action__iexact="Pursue")
                .values("patent_id")
                .distinct()
                .count()
            )
            skipped_patents = (
                PatentFeedback.objects.filter(action__iexact="Skip")
                .values("patent_id")
                .distinct()
                .count()
            )
            delayed_patents = (
                PatentFeedback.objects.filter(action__iexact="Delay")
                .values("patent_id")
                .distinct()
                .count()
            )

            # Patents with no feedback
            patents_with_feedback = PatentFeedback.objects.values_list(
                "patent_id", flat=True
            ).distinct()
            patents_without_feedback = SellerForm.objects.exclude(
                id__in=patents_with_feedback
            ).count()

            user_counts = (
                CustomUser.objects.filter(is_admin=False)
                .values("user_type")
                .annotate(count=Count("user_type"))
            )

            response_data = {user["user_type"]: user["count"] for user in user_counts}
            # Prepare response
            data = {
                "user_type": response_data,
                "total_unique_patents": total_patents,
                "unique_patents_by_primary_technology": list(
                    get_count_dict("primary_technology")
                ),
                "unique_patents_by_entity_status": list(
                    get_count_dict("entity_status")
                ),
                "unique_patents_by_acquisition_status": list(
                    get_count_dict("acquisition_status")
                ),
                "unique_patents_by_ip_type": list(get_count_dict("ip_type")),
                "feedback_analytics": {
                    "chased_patents": chased_patents,
                    "skipped_patents": skipped_patents,
                    "delayed_patents": delayed_patents,
                    "patents_without_feedback": patents_without_feedback,
                },
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_type_counts(request):
    user_counts = (
        CustomUser.objects.filter(is_admin=False)
        .values("user_type")
        .annotate(count=Count("user_type"))
    )

    response_data = {user["user_type"]: user["count"] for user in user_counts}
    return Response(response_data, status=status.HTTP_200_OK)


User = get_user_model()


# @api_view(["POST"])
# @permission_classes([AllowAny])
# def send_reset_password_email(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         try:
#             user = CustomUser.objects.get(email=email)
#         except CustomUser.DoesNotExist:
#             return JsonResponse(
#                 {"message": "User with this email does not exist"}, status=404
#             )

#         # Generate password reset token
#         token_generator = PasswordResetTokenGenerator()
#         token = token_generator.make_token(user)
#         uid = urlsafe_base64_encode(force_bytes(user.pk))

#         # Create reset password URL
#         reset_url = f"https://www.sellbuypatent.com/confirm-password?fromForgot=true&uid={uid}&token={token}"
#         # reset_url = f"http://ec2-3-144-99-241.us-east-2.compute.amazonaws.com/confirm-password?fromForgot=true&uid={uid}&token={token}"

#         # Email content
#         subject = "🔐 Reset Your Password"
#         html_message = render_to_string(
#             "reset_password.html", {"reset_url": reset_url, "user": user}
#         )
#         plain_message = strip_tags(html_message)  # Fallback for plain text email

#         send_mail(
#             subject,
#             plain_message,
#             settings.DEFAULT_FROM_EMAIL,
#             [email],
#             html_message=html_message,
#         )

#         return JsonResponse(
#             {"message": "Password reset email sent successfully"}, status=200
#         )

#     return JsonResponse({"error": "Invalid request"}, status=400)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from ..models import CustomUser


@api_view(["POST"])
@permission_classes([AllowAny])
def send_reset_password_email(request):
    # DRF me JSON aayega to request.data use karna best hai
    email = (request.data.get("email") or "").strip()

    if not email:
        return Response({"error": "Email is required"}, status=400)

    # Case-insensitive lookup
    user = CustomUser.objects.filter(email__iexact=email).first()
    if not user:
        # OPTION‑1: 404 ke sath clear msg
        return Response(
            {"message": "User with this email does not exist"},
            status=404,
        )

        # OPTION‑2 (security friendly):
        # return Response(
        #     {"message": "If this email exists, a reset link has been sent."},
        #     status=200,
        # )

    # Generate password reset token
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # PRODUCTION URL use karo (localhost nahi)
    reset_url = (
        "https://www.sellbuypatent.com/confirm-password"
        f"?fromForgot=true&uid={uid}&token={token}"
    )

    subject = "Reset Your Password"
    html_message = render_to_string(
        "reset_password.html",
        {"reset_url": reset_url, "user": user},
    )
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )

    return Response(
        {"message": "Password reset email sent successfully"},
        status=200,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            uidb64 = data.get("uid")
            token = data.get("token")
            new_password = data.get("new_password")

            # Decode UID
            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return JsonResponse({"error": "Invalid link"}, status=400)

            # Validate token
            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                return JsonResponse({"error": "Invalid or expired token"}, status=400)

            # Set new password
            user.set_password(new_password)
            user.save()

            return JsonResponse(
                {"message": "Password has been reset successfully"}, status=200
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid request data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status


class UpdateSellerFormFileView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """
        Uploads a new PDF file once and updates the `file` field for all `SellerForm` entries to reference the same file.
        """
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Define the new file path
        file_name = f"uploads/{uploaded_file.name}"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        # Save the file once, overwriting the existing one
        if default_storage.exists(file_name):
            default_storage.delete(file_name)  # Remove old file before overwriting

        default_storage.save(
            file_name, ContentFile(uploaded_file.read())
        )  # Save new file once

        # Update all SellerForm entries to point to the single uploaded file
        SellerForm.objects.all().update(file=file_name)  # Update database field only

        return Response(
            {"message": "File updated successfully for all entries"},
            status=status.HTTP_200_OK,
        )


# from ..models import SellerForm, FormUploads

# from ..models import UploadsFileS3Storage, get_uploads_s3_file_path


class UploadAndLinkToAllSellerForms(APIView):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Step 1: Upload the file once to S3
        # storage = UploadsFileS3Storage()
        # unique_filename = get_uploads_s3_file_path(None, uploaded_file.name)
        # s3_path = storage.save(unique_filename, uploaded_file)

        # Step 2: Create the FormUploads instance once
        dummy_form = (
            SellerForm.objects.first()
        )  # Temporarily assign to one form for FK requirement
        file_instance = FormUploads.objects.create(
            # file=s3_path,
            patent=dummy_form
        )

        # Step 3: Update the `patent` field of that single FormUploads instance to point to all SellerForms
        # Since each FormUploads is linked to one SellerForm, we need to create duplicates

        all_forms = SellerForm.objects.exclude(id=dummy_form.id)

        form_uploads_to_create = [
            FormUploads(file=file_instance.file, patent=form) for form in all_forms
        ]
        FormUploads.objects.bulk_create(form_uploads_to_create)

        return Response(
            {
                "message": "File uploaded and linked to all SellerForm entries.",
                "file_url": file_instance.file.url,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_patent_files(request, patent_id):
    try:
        patent = SellerForm.objects.get(patent_number=patent_id)
        files = FormUploads.objects.filter(patent=patent)

        file_data = [{"id": file.id, "file_url": file.file_url} for file in files]

        return JsonResponse({"files": file_data}, status=200)
    except SellerForm.DoesNotExist:
        return JsonResponse({"error": "Patent not found"}, status=404)


class BuyerActionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        buyer = request.user
        patent_id = request.data.get("id")
        action = request.data.get("action")

        if action not in ["Pursue", "Pass"]:
            return Response({"error": "Invalid action."}, status=400)

        try:
            patent = SellerForm.objects.get(id=patent_id)
        except SellerForm.DoesNotExist:
            return Response({"error": "Patent not found."}, status=404)

        buyer_action = PatentFeedback.objects.create(
            buyer=buyer,
            patent=patent,
            action=action,
        )

        serializer = PatentFeedbackSerializer(buyer_action)
        return Response(serializer.data, status=201)

    def delete(self, request, *args, **kwargs):
        buyer = request.user
        patent_id = request.data.get("id")

        deleted_count, _ = PatentFeedback.objects.filter(
            buyer=buyer, patent_id=patent_id
        ).delete()

        if deleted_count == 0:
            return Response({"error": "Feedback not found."}, status=404)

        return Response(
            {"message": f"{deleted_count} feedback entries removed successfully."},
            status=200,
        )


# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers import BuyerFormSerializer
from ..models import BuyerForm, SellerForm

# agar Seller wahi models.py me hai


from django.db import models
from django.db.models import Q


class BuyerFormSubmissionView(APIView):
    def post(self, request):
        serializer = BuyerFormSerializer(data=request.data)
        if serializer.is_valid():
            buyer = serializer.save(user=request.user)

            # --- Start with all sellers ---
            matching_sellers = SellerForm.objects.all()

            # ✅ 1. Technology match
            if buyer.tech_fields:
                tech_keywords = [
                    kw.strip().lower() for kw in buyer.tech_fields.split(",")
                ]
                query = models.Q()
                for kw in tech_keywords:
                    query |= (
                        models.Q(primary_technology__icontains=kw)
                        | models.Q(tech_domain__icontains=kw)
                        | models.Q(technologies__icontains=kw)
                        | models.Q(keywords__icontains=kw)
                    )
                matching_sellers = matching_sellers.filter(query)

            # ✅ 2. Number of patents
            if buyer.portfolio_size and buyer.portfolio_size.isdigit():
                required_size = int(buyer.portfolio_size)
                matching_sellers = matching_sellers.filter(
                    number_of_patents__gte=required_size
                )

            # ✅ 3. Budget range
            budget_min, budget_max = None, None
            if buyer.budget_range and "-" in buyer.budget_range:
                parts = buyer.budget_range.split("-")
                if len(parts) == 2:
                    try:
                        budget_min = int(parts[0].strip())
                        budget_max = int(parts[1].strip())
                    except ValueError:
                        pass

            # seller side ka price_expectation abhi CharField hai → ideally int field hona chahiye
            # abhi ke liye simple check karo:
            if budget_max:
                matching_sellers = matching_sellers.filter(
                    models.Q(price_expectation__icontains="Negotiable")
                    | models.Q(
                        price_expectation__lte=str(budget_max)
                    )  # agar seller ne number string diya ho
                )

            # ✅ Response prepare
            response_data = {
                "buyer": BuyerFormSerializer(buyer).data,
                "matched_sellers": SellerFormSerializer(
                    matching_sellers, many=True
                ).data,
            }

            # ✅ Buyer form flag update
            request.user.has_filled_buyer_form = True
            request.user.save()

            return Response(response_data, status=201)

        return Response(serializer.errors, status=400)


from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# from .serializers import BuyerFormSerializer, SellerFormSerializer
from ..serializers import BuyerFormSerializer, SellerFormSerializer


# views.py (login view ka example)
class CustomLoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            user = User.objects.get(username=request.data["username"])

            response.data["role"] = "buyer" if user.is_buyer else "seller"
            response.data["is_new"] = (
                user.is_new
            )  # 👈 ek custom flag (registration ke time True, first login ke baad False)

        return response


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from ..models import BuyerForm, SellerForm

# from .serializers import BuyerFormSerializer, SellerFormSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_matching_sellers(request, buyer_id):
    try:
        buyer = BuyerForm.objects.get(id=buyer_id, user=request.user)
    except BuyerForm.DoesNotExist:
        return Response({"error": "Buyer not found or not authorized"}, status=404)

    # --- Start with all sellers ---
    matching_sellers = SellerForm.objects.all()

    # ✅ 1. Technology match
    if buyer.tech_fields:
        tech_keywords = [kw.strip().lower() for kw in buyer.tech_fields.split(",")]
        query = Q()
        for kw in tech_keywords:
            query |= (
                Q(primary_technology__icontains=kw)
                | Q(tech_domain__icontains=kw)
                | Q(technologies__icontains=kw)
                | Q(keywords__icontains=kw)
            )
        matching_sellers = matching_sellers.filter(query)

    # ✅ 2. Number of patents
    if buyer.portfolio_size and buyer.portfolio_size.isdigit():
        required_size = int(buyer.portfolio_size)
        matching_sellers = matching_sellers.filter(number_of_patents__gte=required_size)

    # ✅ 3. Budget range
    budget_min, budget_max = None, None
    if buyer.budget_range and "-" in buyer.budget_range:
        parts = buyer.budget_range.split("-")
        if len(parts) == 2:
            try:
                budget_min = int(parts[0].strip())
                budget_max = int(parts[1].strip())
            except ValueError:
                pass

    if budget_max:
        matching_sellers = matching_sellers.filter(
            Q(price_expectation__icontains="Negotiable")
            | Q(price_expectation__lte=str(budget_max))
        )

    return Response(
        {
            "buyer": BuyerFormSerializer(buyer).data,
            "matched_sellers": SellerFormSerializer(matching_sellers, many=True).data,
        }
    )


# from .matching import find_matching_sellers

# accounts/views.py

# accounts/views.py
# from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import BuyerForm, SellerForm

# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from .models import BuyerForm, SellerForm


# accounts/views/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

# from .models import BuyerForm, SellerForm
from ..models import BuyerForm

# from accounts.models import BuyerForm, SellerForm


# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.db.models import Q
# from accounts.models import BuyerForm, SellerForm
# from accounts.serializers import BuyerFormSerializer, SellerFormSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_matching_sellers(request, buyer_id):
    try:
        buyer = BuyerForm.objects.get(id=buyer_id, user=request.user)
    except BuyerForm.DoesNotExist:
        return Response({"error": "Buyer not found or not authorized"}, status=404)

    # --- Start with all sellers ---
    matching_sellers = SellerForm.objects.all()

    # ✅ 1. Technology match
    if buyer.tech_fields:
        tech_keywords = [kw.strip().lower() for kw in buyer.tech_fields.split(",")]
        query = Q()
        for kw in tech_keywords:
            query |= (
                Q(primary_technology__icontains=kw)
                | Q(tech_domain__icontains=kw)
                | Q(technologies__icontains=kw)
                | Q(keywords__icontains=kw)
            )
        matching_sellers = matching_sellers.filter(query)

    # ✅ 2. Number of patents
    if buyer.portfolio_size and buyer.portfolio_size.isdigit():
        required_size = int(buyer.portfolio_size)
        matching_sellers = matching_sellers.filter(number_of_patents__gte=required_size)

    # ✅ 3. Budget range
    budget_min, budget_max = None, None
    if buyer.budget_range and "-" in buyer.budget_range:
        parts = buyer.budget_range.split("-")
        if len(parts) == 2:
            try:
                budget_min = int(parts[0].strip())
                budget_max = int(parts[1].strip())
            except ValueError:
                pass

    if budget_max:
        matching_sellers = matching_sellers.filter(
            Q(price_expectation__icontains="Negotiable")
            | Q(price_expectation__lte=str(budget_max))  # agar string number diya ho
        )

    return Response(
        {
            "buyer": BuyerFormSerializer(buyer).data,
            "matched_sellers": SellerFormSerializer(matching_sellers, many=True).data,
        }
    )


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated


class UploadNDA(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user  # must be authenticated
        file_obj = request.FILES.get("nda_signed_file")
        if not file_obj:
            return Response({"error": "No file uploaded."}, status=400)

        if user.user_type != "Buyer":
            return Response({"error": "Only buyers can upload NDA"}, status=400)

        user.nda_signed_file = file_obj
        user.save()
        return Response({"message": "Signed NDA uploaded successfully."})


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from accounts.models import CustomUser

# from yourapp.models import SellerForm  # update if different
import os

#         return Response({"message": "Invoice email sent"}, status=200)
from django.utils import timezone
from django.http import HttpRequest
from datetime import timedelta
from docxtpl import DocxTemplate
from django.core.mail import EmailMessage
import os


class SendAnalysisEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest):
        user = request.user
        portfolio_id = request.data.get("portfolio_id")

        if not portfolio_id:
            return Response({"error": "Portfolio ID is required"}, status=400)

        try:
            portfolio = SellerForm.objects.get(id=portfolio_id)
        except SellerForm.DoesNotExist:
            return Response({"error": "Portfolio not found"}, status=404)

        today = timezone.now().date()
        due_date = today + timedelta(days=7)

        context = {
            "buyer_name": f"{user.first_name} {user.last_name}",
            "buyer_company": getattr(user, "company_name", ""),
            "buyer_telephone": user.phone_number,
            "buyer_email": user.email,
            "invoice_number": f"Bay-EX/25-26/{portfolio.id:02d}",
            "current_date": today.strftime("%d-%m-%Y"),
            "portfolio_code": portfolio.portfolio_code,
            "due_date": due_date.strftime("%d-%m-%Y"),
            "service_fee": "USD 500",
        }
        template_path = os.path.join(settings.BASE_DIR, "static", "Bay_Invoice.docx")
        doc = DocxTemplate(template_path)
        doc.render(context)

        # Save to a temporary file
        temp_invoice_path = os.path.join(
            settings.MEDIA_ROOT, f"invoice_{portfolio.id}.docx"
        )
        doc.save(temp_invoice_path)

        # Email Subject
        subject = "Your Invoice for Portfolio Download"

        # Render email content from template
        message = render_to_string(
            "email_templates/analysis_email.py",  # template path
            {
                "first_name": user.first_name,
                "portfolio_title": portfolio.portfolio_code,
            },
        )

        # Create Email
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.content_subtype = "html"  # Important for HTML rendering
        email.attach_file(temp_invoice_path)

        # Attach invoice PDF (optional)
        try:
            pdf_path = os.path.join(settings.BASE_DIR, "static", "invoice_template.pdf")
            if os.path.exists(pdf_path):
                email.attach_file(pdf_path)
        except Exception as e:
            print("Attachment error:", e)

        # Attach DOCX file
        try:
            docx_path = os.path.join(settings.BASE_DIR, "static", "Bay_Invoice.docx")
            if os.path.exists(docx_path):
                email.attach_file(docx_path)
        except Exception as e:
            print("DOCX Attachment error:", e)

        email.send()

        return Response({"message": "Invoice email sent to buyer."}, status=200)


from django.contrib import admin
from ..models import CustomUser

try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "user_type", "is_verified")
    list_filter = ("is_verified", "user_type")
    search_fields = ("email", "first_name", "last_name")
    actions = ["mark_as_verified", "mark_as_unverified"]

    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} user(s) marked as verified.")

    mark_as_verified.short_description = "Mark selected users as verified"

    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"{updated} user(s) marked as unverified.")

    mark_as_unverified.short_description = "Mark selected users as unverified"


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_user_list(request):
    users = CustomUser.objects.all().values(
        "id", "email", "first_name", "last_name", "user_type", "is_verified"
    )
    return Response(list(users), status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def admin_user_verify(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        was_verified = user.is_verified
        user.is_verified = True
        user.save()
        # ✅ Send welcome email only when changing from unverified -> verified
        if not was_verified:
            send_welcome_email(user.email, user.first_name)
        return Response(
            {"message": "User verified successfully"}, status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def admin_user_unverify(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_verified = False
        user.save()
        return Response(
            {"message": "User unverified successfully"}, status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def contact_form(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")
        email = data.get("email", "")
        phone = data.get("phone", "")
        message = data.get("message", "")

        email_body = f"""
New Contact Form Submission

Name: {first_name} {last_name}
Email: {email}
Phone: {phone}

Message:
{message}
"""

        mail = EmailMessage(
            subject="New Contact Form Submission",
            body=email_body,
            from_email="SellBuyPatent <patentteam@bayslope.com>",
            to=["patentteam@bayslope.com"],
            reply_to=[email],
        )

        mail.send(fail_silently=False)

        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request"}, status=400)


from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"detail": "CSRF cookie set"})


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


# @csrf_exempt
# @api_view(["POST"])
# @permission_classes([AllowAny])
# def login_test(request):
#     return Response(
#         {
#             "message": "login_test OK",
#             "data": request.data,
#         },
#         status=200,
#     )


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from ..serializers import LoginSerializer
from ..models import SellerForm, BuyerForm

User = get_user_model()


@csrf_exempt
def login_test(request):

    if request.GET.get("debug") == "1":
        return JsonResponse({
            "debug": True,
            "actual_method_received": request.method,
            "path": request.path,
            "user_agent": request.META.get("HTTP_USER_AGENT", "Unknown"),
            "remote_addr": request.META.get("REMOTE_ADDR", "Unknown"),
        }, status=200)
    
    # Sirf POST allow karo
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        body = request.body.decode("utf-8") if request.body else ""
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    email = data.get("email")
    password = data.get("password")
    requested_user_type = data.get("user_type")

    # 🔹 Hardcoded Admin Check
    if email == "sarita@gmail.com" and password == "admins":
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({"error": "Admin user not found"}, status=404)

        if not user.check_password(password):
            return JsonResponse({"error": "Invalid password"}, status=400)

        refresh = RefreshToken.for_user(user)
        return JsonResponse(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "is_admin": True,
                "user_type": user.user_type,
                "has_filled_seller_form": getattr(
                    user, "has_filled_seller_form", False
                ),
                "message": "Admin login successful",
            },
            status=200,
        )

    # 🔹 Normal login flow (DRF serializer use kar sakte hain)
    serializer = LoginSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    user = serializer.validated_data["user"]

    if requested_user_type and user.user_type != requested_user_type:
        return JsonResponse(
            {"error": "User type mismatch. Please use the correct login option."},
            status=400,
        )

    # 🟢 BLOCK UNVERIFIED USERS
    if not user.is_verified:
        nda_template_url = "https://www.sellbuypatent.com/static/nda_template.pdf"
        return JsonResponse(
            {
                "error": "Not verified. Please upload signed NDA.",
                "nda_template_url": nda_template_url,
                "nda_uploaded": bool(user.nda_signed_file),
            },
            status=403,
        )

    # Flags
    user.has_filled_seller_form = SellerForm.objects.filter(user=user).exists()
    user.save()

    has_filled_buyer_form = BuyerForm.objects.filter(user=user).exists()

    refresh = RefreshToken.for_user(user)
    return JsonResponse(
        {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_admin": getattr(user, "is_admin", False),
            "user_type": user.user_type,
            "phone_no": getattr(user, "phone_number", None),
            "has_filled_seller_form": user.has_filled_seller_form,
            "has_filled_buyer_form": has_filled_buyer_form,
            "is_new_buyer": (user.user_type == "Buyer" and not has_filled_buyer_form),
            "message": "Login successful",
        },
        status=200,
    )


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import resolve


@csrf_exempt
def debug_login_mapping(request):
    try:
        match = resolve("/api/accounts/login/")
        return JsonResponse(
            {
                "ok": True,
                "view_func": repr(match.func),
                "url_name": match.url_name,
                "route": match.route,
            }
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse(
            {
                "ok": False,
                "error": str(e),
            },
            status=500,
        )


from django.core.mail import send_mail
from django.conf import settings
from ..models import CustomUser  # ensure yeh import hai


def send_seller_credentials_email(user, raw_password):
    subject = "Your Sellbuypatent Seller Account Details"
    message = (
        f"Hi {user.first_name or ''},\n\n"
        "Thank you for submitting your seller form on Sellbuypatent.\n\n"
        "We have created your seller account. You can now log in using:\n\n"
        f"Email: {user.email}\n"
        f"Password: {raw_password}\n\n"
        "Login here: https://www.sellbuypatent.com/login?user_type=Seller\n\n"
        "For security, please change this password after your first login.\n\n"
        "Regards,\n"
        "Sellbuypatent Team"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


from django.http import JsonResponse
from ..models import ExternalData


def external_data_list(request):
    qs = ExternalData.objects.values(
        "sno",
        "applicationNumber",
        "patentNumber",
        "applicationType",
        "PublicationNumber",
        "PublicationType",
        "status",
        "entityStatus",
        "smallEntityStatus",
        "filingDate",
        "applicantName",
        "inventorBag",
    )[
        :100
    ]  # sirf 100 rows

    data = list(qs)
    return JsonResponse(data, safe=False)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reach_out_for_patent(request):
    user = request.user

    # Frontend se 'patentNumber' aa raha hai; optional 'patent_number' bhi allow kar do
    patent_number = request.data.get("patentNumber") or request.data.get(
        "patent_number"
    )

    if not patent_number:
        return Response({"error": "patentNumber is required"}, status=400)

    client_email = user.email
    admin_email = "patentteam@bayslope.com"

    subject = f"Thanks for reaching out about patent {patent_number}"

    message = (
        f"Hi {user.first_name or ''} {user.last_name or ''},\n\n"
        f"Thank you for showing interest in the following patent on SellBuyPatent:\n\n"
        f"Patent Number: {patent_number}\n\n"
        "Our team has received your request and will contact you shortly with "
        "more details about this patent and possible next steps.\n\n"
        "If you did not make this request, you can ignore this email.\n\n"
        "Best regards,\n"
        "SellBuyPatent Team"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [client_email],
        fail_silently=False,
    )
    # 2️⃣ Mail to ADMIN / team (copy with info of who clicked)
    subject_admin = f"[Reach Out] {user.email} requested info on {patent_number}"

    message_admin = (
        "A client has clicked 'Reach Out' on the External Data table.\n\n"
        f"Patent Number: {patent_number}\n\n"
        "Client details:\n"
        f"Name: {user.first_name or ''} {user.last_name or ''}\n"
        f"Email: {user.email}\n"
        f"User Type: {getattr(user, 'user_type', '')}\n"
        f"Phone: {getattr(user, 'phone_number', '')}\n\n"
        "Please follow up with the client regarding this patent.\n\n"
        "Regards,\nSellBuyPatent Portal"
    )

    send_mail(
        subject_admin,
        message_admin,
        settings.DEFAULT_FROM_EMAIL,
        [admin_email],
        fail_silently=False,
    )

    return Response({"message": "Reach-out email sent to client and admin."}, status=200)

    # return Response({"message": "Reach-out email sent to client."}, status=200)
