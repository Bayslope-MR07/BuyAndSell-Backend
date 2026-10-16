# Serializer for login to validate the email and password
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'user_type', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            user_type=validated_data['user_type'],
            password=validated_data['password']
        )
        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        
        attrs['user'] = user
        return attrs

from rest_framework import serializers
from .models import SellerForm
from rest_framework import serializers
from .models import PatentFeedback

class BuyerActionSerializer(serializers.ModelSerializer):
    buyer_email = serializers.SerializerMethodField()
    patent_number = serializers.SerializerMethodField()

    class Meta:
        model = PatentFeedback
        fields = ['id', 'action', 'buyer_email', 'patent_number', 'timestamp']

    def get_buyer_email(self, obj):
        return obj.buyer.email if obj.buyer else None

    def get_patent_number(self, obj):
        return obj.patent.patent_number if obj.patent else None
from rest_framework import serializers

from rest_framework import serializers
from .models import SellerForm  # Assuming you have a SellerForm model
from .models import BuyerForm

""" 
class SellerFormSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    contact = serializers.CharField(max_length=15)
    patents = serializers.CharField(max_length=255)
    google_link = serializers.URLField()
    company_name = serializers.CharField(max_length=255)
    file = serializers.FileField(required=False)

    def create(self, validated_data):
        # Create and return a new SellerForm instance
        return SellerForm.objects.create(**validated_data) """


from rest_framework import serializers
from .models import SellerForm

class SellerFormSerializer(serializers.ModelSerializer):
    claim_charts_url = serializers.SerializerMethodField()
    analysis_sheet_url = serializers.SerializerMethodField()
    class Meta:
        model = SellerForm
        fields = '__all__'
        extra_kwargs = {
            "patent_number": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "email": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },  # agar email bhi optional
        }
        # read_only_fields = ['user']

    def get_claim_charts_url(self, obj):
        request = self.context.get('request')
        if obj.claim_charts and hasattr(obj.claim_charts, 'url'):
            return request.build_absolute_uri(obj.claim_charts.url) if request else obj.claim_charts.url
        return None

    def get_analysis_sheet_url(self, obj):
        request = self.context.get('request')
        if obj.analysis_sheet and hasattr(obj.analysis_sheet, 'url'):
            return request.build_absolute_uri(obj.analysis_sheet.url) if request else obj.analysis_sheet.url
        return None

    def get_word_docs_url(self, obj):
        request = self.context.get("request")
        if obj.word_docs and hasattr(obj.word_docs, "url"):
            return (
                request.build_absolute_uri(obj.word_docs.url)
                if request
                else obj.word_docs.url
            )
        return None


from rest_framework import serializers
from .models import SellerForm

class SellerFormVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerForm
        fields = [
            'verified', 'important', 'additional_notes', 'entity_status', 'acquisition_status', 
            'bay_overall_rating', 'enforceability', 'target', 'company_name', 'admin_contact', 'admin_email',
            'upcoming_fees', 'title', 'abstract', 'first_claim', 'filing_date', 'grant_date',
            'current_assignee', 'ip_type', 'family_members', 'concepts', 'keywords', 'technologies'
        ]

    def update(self, instance, validated_data):
        instance.verified = validated_data.get('verified', instance.verified)
        instance.important = validated_data.get('important', instance.important)
        instance.additional_notes = validated_data.get('additional_notes', instance.additional_notes)
        instance.entity_status = validated_data.get('entity_status', instance.entity_status)
        instance.acquisition_status = validated_data.get('acquisition_status', instance.acquisition_status)
        # instance.bay_rating = validated_data.get('bay_rating', instance.bay_rating)
        instance.bay_overall_rating = validated_data.get('bay_overall_rating', instance.bay_overall_rating)
        instance.enforceability = validated_data.get('enforceability', instance.enforceability)
        instance.target = validated_data.get('target', instance.target)
        instance.company_name = validated_data.get('company_name', instance.company_name)
        instance.admin_contact = validated_data.get('admin_contact', instance.admin_contact)
        instance.admin_email = validated_data.get('admin_email', instance.admin_email)
        instance.upcoming_fees = validated_data.get('upcoming_fees', instance.upcoming_fees)
        instance.title = validated_data.get('title', instance.title)
        instance.abstract = validated_data.get('abstract', instance.abstract)
        instance.first_claim = validated_data.get('first_claim', instance.first_claim)
        instance.filing_date = validated_data.get('filing_date', instance.filing_date)
        instance.grant_date = validated_data.get('grant_date', instance.grant_date)
        instance.current_assignee = validated_data.get('current_assignee', instance.current_assignee)
        instance.ip_type = validated_data.get('ip_type', instance.ip_type)
        instance.family_members = validated_data.get('family_members', instance.family_members)
        instance.concepts = validated_data.get('concepts', instance.concepts)
        instance.keywords = validated_data.get('keywords', instance.keywords)
        instance.technologies = validated_data.get('technologies', instance.technologies)

        instance.save()
        return instance


from rest_framework import serializers
from .models import PatentFeedback

class PatentFeedbackSerializer(serializers.ModelSerializer):
    patent = SellerFormSerializer(read_only=True)
    class Meta:
        model = PatentFeedback
        fields = ['id', 'buyer', 'patent', 'action', 'timestamp']
        read_only_fields = ['id', 'timestamp']

# class BuyerViewSerializer(serializers.ModelSerializer):
#     user_feedback = serializers.SerializerMethodField()
#     class Meta:
#         model = SellerForm
#         fields = [
#             'id', 'primary_technology', 'google_patent_link', 'file', 'verified',
#             'important', 'additional_notes', 'entity_status', 'acquisition_status',
#             'bay_rating', 'enforceability', 'target', 'company_name', 'admin_contact',
#             'admin_email', 'upcoming_fees', 'title', 'abstract', 'first_claim', 'filing_date',
#             'grant_date', 'current_assignee', 'ip_type', 'family_members', 'concepts',
#             'keywords', 'technologies','expiry','patent_number','user_feedback'
#         ]
#     def get_user_feedback(self, obj):
#         """Filter the feedback to show only the signed-in user's response"""
#         request = self.context.get('request')  # Get request context
#         if request and hasattr(request, "user"):
#             user_feedback = obj.feedback.filter(buyer=request.user).order_by('-timestamp').first()
#             if user_feedback:
#                 return {

#                     "action": user_feedback.action,
#                     "timestamp": user_feedback.timestamp,
#                 }
#         return None

from rest_framework import serializers
from .models import SellerForm


class BuyerViewSerializer(serializers.ModelSerializer):
    user_feedback = serializers.SerializerMethodField()
    uploaded_files = serializers.SerializerMethodField()

    class Meta:
        model = SellerForm
        fields = [
            "id",
            "sr_no",
            "portfolio_code",
            "tech_domain",
            "industry",
            "exclusive",
            "technology_tags",
            "portfolio_coverage",
            "number_of_patents",
            "number_of_patent_families",
            "patent_geographies",
            "sep_patent",
            "any_ongoing_continuation",
            "portfolio_sold_before",
            "upcoming_fees",
            "patents_status",
            "seller_entity",
            "seller_entity_status",
            "seller_country",
            "monetization_preference",
            "monetization_strategy",
            "willingness_to_negotiate",
            "encumbrances",
            "analysis_sheet",
            "zip_files",
            "previous_history_selling",
            "diligence_material",
            "number_of_relevant_companies",
            "relevant_companies",
            "number_of_charts",
            "product_matching",
            "standard_mapping",
            "product_categories",
            "market_size",
            "dominant_litigation",
            "timeline_offer",
            "comments",
            "acquisition_status",
            "portfolio_rating",
            "buying_options",
            "phone",
            "email",
            "spoc_company",
            "user_feedback",
            "uploaded_files",
            "created_at",
        ]

    def get_user_feedback(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user_feedback = (
                obj.feedback.filter(buyer=request.user).order_by("-timestamp").first()
            )
            if user_feedback:
                return {
                    "action": user_feedback.action,
                    "timestamp": user_feedback.timestamp,
                }
        return None

    def get_uploaded_files(self, obj):
        return [
            {
                "id": upload.id,
                "file_url": upload.file.url if upload.file else None,
                "generated_at": upload.generated_at,
            }
            for upload in obj.uploads.all()
        ]


# serializers.py

from .models import FormUploads

class FormUploadsSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = FormUploads
        fields = ['id', 'file', 'file_url', 'generated_at']

    def get_file_url(self, obj):
        return obj.file.url if obj.file else None


    def get_uploaded_files(self, obj):  # 👈 Make sure this is indented properly
        uploads = obj.uploads.all()
        return [
            {
                "id": file.id,
                "file": file.file.url if file.file else None,
                "generated_at": file.generated_at
            }
            for upload in obj.uploads.all() 
            for file in uploads
        ]


class PatentFeedbackSerializer2(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.username", read_only=True)

    class Meta:
        model = PatentFeedback
        fields = ['buyer_name', 'action', 'timestamp']


from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.account import app_settings as allauth_account_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import EmailAddress, SocialAccount
from allauth.socialaccount.providers.base import AuthProcess
from allauth.utils import get_username_max_length
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponseBadRequest
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext_lazy as _
from requests.exceptions import HTTPError
from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import BuyerForm

class CustomSocialLoginSerializer(SocialLoginSerializer):
    def validate(self, attrs):
        view = self.context.get('view')
        request = self._get_request()

        if not view:
            raise self.ValidationError(
                _('View is not defined, pass it as a context variable'),
            )

        adapter_class = getattr(view, 'adapter_class', None)
        if not adapter_class:
            raise self.ValidationError(_('Define adapter_class in view'))

        adapter = adapter_class(request)
        app = adapter.get_provider().app

        access_token = attrs.get('access_token')
        code = attrs.get('code')

        if access_token:
            tokens_to_parse = {'access_token': access_token}
            token = access_token
            id_token = attrs.get('id_token')
            if id_token:
                tokens_to_parse['id_token'] = id_token

        elif code:
            self.set_callback_url(view=view, adapter_class=adapter_class)
            self.client_class = getattr(view, 'client_class', None)

            if not self.client_class:
                raise self.ValidationError(_('Define client_class in view'))

            provider = adapter.get_provider()
            scope = provider.get_scope_from_request(request)

            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope,
                # REMOVE `scope_delimiter` to avoid duplicate values
                headers=adapter.headers,
                basic_auth=adapter.basic_auth,
            )

            try:
                token = client.get_access_token(code)
            except OAuth2Error as ex:
                raise self.ValidationError(
                    _('Failed to exchange code for access token')
                ) from ex

            access_token = token['access_token']
            tokens_to_parse = {'access_token': access_token}

            for key in ['refresh_token', 'id_token', adapter.expires_in_key]:
                if key in token:
                    tokens_to_parse[key] = token[key]
        else:
            raise self.ValidationError(_('Incorrect input. access_token or code is required.'))

        social_token = adapter.parse_token(tokens_to_parse)
        social_token.app = app

        try:
            if adapter.provider_id == 'google' and not code:
                login = self.get_social_login(adapter, app, social_token, response={'id_token': id_token})
            else:
                login = self.get_social_login(adapter, app, social_token, token)

            ret = complete_social_login(request, login)
        except HTTPError:
            raise self.ValidationError(_('Incorrect value'))

        if isinstance(ret, HttpResponseBadRequest):
            raise self.ValidationError(ret.content)

        if not login.is_existing:
            if allauth_account_settings.UNIQUE_EMAIL:
                account_exists = get_user_model().objects.filter(
                    email=login.user.email,
                ).exists()
                if account_exists:
                    raise self.ValidationError(_('User is already registered with this e-mail address.'))

            login.lookup()
            try:
                login.save(request, connect=True)
            except IntegrityError as ex:
                raise self.ValidationError(_('User is already registered with this e-mail address.')) from ex

            self.post_signup(login, attrs)

        attrs['user'] = login.account.user

        return attrs


class BuyerFormSerializer(serializers.ModelSerializer):
    companyName = serializers.CharField(source='company_name', required=False, allow_blank=True)
    contactPerson = serializers.CharField(source='contact_person', required=False, allow_blank=True)
    whoAreYou = serializers.CharField(source='who_are_you', required=False, allow_blank=True)
    techFields = serializers.CharField(source='tech_fields', required=False, allow_blank=True)
    class Meta:
        model = BuyerForm
        fields = "__all__"
        read_only_fields = ["id", "created_at", "user"]
        extra_kwargs = {
            "company_name": {"required": False, "allow_blank": True},
            "contact_person": {"required": False, "allow_blank": True},
            "who_are_you": {"required": False, "allow_blank": True},
            "email": {"required": False, "allow_blank": True},
            
        }

    def create(self, validated_data):
        # user ko request se attach karna
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)


from rest_framework import serializers
from .models import BuyerForm


class BuyerFormSerializer(serializers.ModelSerializer):
    # Custom field names for frontend
    companyName = serializers.CharField(
        source="company_name", required=False, allow_blank=True, allow_null=True
    )
    contactPerson = serializers.CharField(
        source="contact_person", required=False, allow_blank=True, allow_null=True
    )
    whoAreYou = serializers.CharField(
        source="who_are_you", required=False, allow_blank=True, allow_null=True
    )
    techFields = serializers.CharField(
        source="tech_fields", required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = BuyerForm
        fields = "__all__"
        read_only_fields = ["id", "created_at", "user"]
        extra_kwargs = {
            "company_name": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "contact_person": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "who_are_you": {"required": False, "allow_blank": True, "allow_null": True},
            "email": {"required": False, "allow_blank": True, "allow_null": True},
            "tech_fields": {"required": False, "allow_blank": True, "allow_null": True},
            "purpose": {"required": False, "allow_blank": True, "allow_null": True},
            "desired_patent_types": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "competitors": {"required": False, "allow_blank": True, "allow_null": True},
            "portfolio_size": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "jurisdictions": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "budget_range": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "deal_structure": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "accept_litigation": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "tolerance_for_encumbrances": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "preferred_timeline": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "acquisition_interest": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "nda_required": {"required": False},
            "restrictions": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
        }

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)

    def to_representation(self, instance):
        """
        Convert empty strings to null in JSON output for consistency.
        """
        rep = super().to_representation(instance)
        for key, value in rep.items():
            if value == "":
                rep[key] = None
        return rep


# class CustomSocialLoginSerializer(SocialLoginSerializer):
#     def validate(self, attrs):
#         view = self.context.get('view')
#         request = self._get_request()

#         if not view:
#             raise self.ValidationError(
#                 _('View is not defined, pass it as a context variable'),
#             )

#         adapter_class = getattr(view, 'adapter_class', None)
#         if not adapter_class:
#             raise self.ValidationError(_('Define adapter_class in view'))

#         adapter = adapter_class(request)
#         app = adapter.get_provider().app

#         access_token = attrs.get('access_token')
#         code = attrs.get('code')

#         if access_token:
#             tokens_to_parse = {'access_token': access_token}
#             token = access_token
#             id_token = attrs.get('id_token')
#             if id_token:
#                 tokens_to_parse['id_token'] = id_token

#         elif code:
#             self.set_callback_url(view=view, adapter_class=adapter_class)
#             self.client_class = getattr(view, 'client_class', None)

#             if not self.client_class:
#                 raise self.ValidationError(_('Define client_class in view'))

#             provider = adapter.get_provider()
#             scope = provider.get_scope_from_request(request)

#             client = self.client_class(
#                 request,
#                 app.client_id,
#                 app.secret,
#                 adapter.access_token_method,
#                 adapter.access_token_url,
#                 self.callback_url,
#                 scope,
#                 headers=adapter.headers,
#                 basic_auth=adapter.basic_auth,
#             )

#             try:
#                 token = client.get_access_token(code)
#             except OAuth2Error as ex:
#                 raise self.ValidationError(
#                     _('Failed to exchange code for access token')
#                 ) from ex

#             access_token = token['access_token']
#             tokens_to_parse = {'access_token': access_token}

#             for key in ['refresh_token', 'id_token', adapter.expires_in_key]:
#                 if key in token:
#                     tokens_to_parse[key] = token[key]
#         else:
#             raise self.ValidationError(_('Incorrect input. access_token or code is required.'))

#         social_token = adapter.parse_token(tokens_to_parse)
#         social_token.app = app

#         try:
#             if adapter.provider_id == 'google' and not code:
#                 login = self.get_social_login(adapter, app, social_token, response={'id_token': id_token})
#             else:
#                 login = self.get_social_login(adapter, app, social_token, token)

#             ret = complete_social_login(request, login)
#         except HTTPError:
#             raise self.ValidationError(_('Incorrect value'))

#         if isinstance(ret, HttpResponseBadRequest):
#             raise self.ValidationError(ret.content)

#         if not login.is_existing:
#             if allauth_account_settings.UNIQUE_EMAIL:
#                 account_exists = get_user_model().objects.filter(
#                     email=login.user.email,
#                 ).exists()
#                 if account_exists:
#                     raise self.ValidationError(_('User is already registered with this e-mail address.'))

#             login.lookup()
#             try:
#                 login.save(request, connect=True)
#             except IntegrityError as ex:
#                 raise self.ValidationError(_('User is already registered with this e-mail address.')) from ex

#             self.post_signup(login, attrs)

#         user = login.account.user

#         # Format the response to match custom login response
#         return {
#             "access_token": access_token,
#             "refresh_token": tokens_to_parse.get("refresh_token", ""),
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "email": user.email,
#             "is_admin": user.is_admin,
#             "user_type": user.user_type,
#             "phone_no": user.phone_number if user.phone_number else "",
#             "message": "Login successful"
#         }
