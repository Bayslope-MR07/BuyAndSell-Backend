from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
# from storages.backends.s3boto3 import S3Boto3Storage
from uuid import uuid4
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, user_type, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, user_type=user_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # return self.create_user(email, user_type='Both', password=password, **extra_fields)
        extra_fields.setdefault('user_type', 'Both')
        return self.create_user(email, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('Buyer', 'Buyer'),
        ('Seller', 'Seller'),
        ('Both', 'Both'),
    ]

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='Buyer')
    has_filled_seller_form = models.BooleanField(default=False)
    has_filled_buyer_form = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False, blank=True)

    objects = CustomUserManager()
    # 🔽 NEW FIELDS HERE
    is_verified = models.BooleanField(default=False)
    nda_signed_file = models.FileField(upload_to="nda_signed/", null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    def __str__(self):
        return self.email


# class UploadsFileS3Storage(S3Boto3Storage):
#     location = "formUploads"


def get_uploads_file_path(instance: "FormUploads", filename: str):
    if not filename or '.' not in filename:
        filename = f"upload_{uuid4().hex}.tmp"
    return f"uploads/{uuid4().hex}.{filename.split('.')[-1]}"


class SellerForm(models.Model):
    user = models.ForeignKey(
        "CustomUser", on_delete=models.SET_NULL, null=True, blank=True
    )

    # 🔽 nayi fields (seller form wale)
    portfolio_type = models.CharField(max_length=100, blank=True, null=True)
    patent_owner_status = models.CharField(max_length=100, blank=True, null=True)
    patent_owner_website = models.URLField(blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    current_assignee_status = models.CharField(max_length=100, blank=True, null=True)
    price_expectation = models.CharField(max_length=100, blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    primary_technology = models.CharField(max_length=255, blank=True, null=True)

    sr_no = models.IntegerField(null=True, blank=True)
    portfolio_code = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    tech_domain = models.CharField(max_length=255, blank=True, null=True)
    technology_tags = models.CharField(max_length=255, blank=True, null=True)
    portfolio_coverage = models.CharField(max_length=255, blank=True, null=True)
    number_of_patents = models.PositiveIntegerField(default=0)
    exclusive = models.BooleanField(default=False)
    number_of_patent_families = models.PositiveIntegerField(default=0)
    patent_geographies = models.CharField(max_length=255, blank=True, null=True)
    sep_patent = models.CharField(max_length=255, blank=True, null=True)
    any_ongoing_continuation = models.CharField(max_length=255, blank=True, null=True)
    portfolio_sold_before = models.CharField(max_length=255, blank=True, null=True)
    upcoming_fees = models.TextField(blank=True, null=True)
    patents_status = models.CharField(max_length=255, blank=True, null=True)
    seller_entity = models.CharField(max_length=255, blank=True, null=True)
    seller_entity_status = models.CharField(max_length=255, blank=True, null=True)
    seller_country = models.CharField(max_length=255, blank=True, null=True)
    monetization_preference = models.CharField(max_length=255, blank=True, null=True)
    monetization_strategy = models.CharField(max_length=255, blank=True, null=True)
    willingness_to_negotiate = models.CharField(max_length=255, blank=True, null=True)
    encumbrances = models.CharField(
        max_length=255, blank=True, null=True, default="None"
    )
    previous_history_selling = models.TextField(blank=True, null=True)
    diligence_material = models.CharField(max_length=255, blank=True, null=True)
    number_of_relevant_companies = models.CharField(
        max_length=255, blank=True, null=True
    )
    relevant_companies = models.CharField(max_length=255, blank=True, null=True)
    number_of_charts = models.CharField(max_length=255, blank=True, null=True)
    product_matching = models.CharField(max_length=255, blank=True, null=True)
    standard_mapping = models.CharField(max_length=255, blank=True, null=True)
    product_categories = models.CharField(max_length=255, blank=True, null=True)
    market_size = models.CharField(max_length=255, blank=True, null=True)
    dominant_litigation = models.CharField(max_length=255, blank=True, null=True)
    timeline_offer = models.CharField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    acquisition_status = models.CharField(
        max_length=50, choices=[("Open", "Open"), ("Closed", "Closed")], default="Open"
    )
    portfolio_rating = models.CharField(max_length=255, blank=True, null=True)
    buying_options = models.CharField(
        max_length=50,
        choices=[("Pursue", "Pursue"), ("Pass", "Pass")],
        default="Skip",
    )
    phone = models.CharField(max_length=25, default="", blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    spoc_company = models.CharField(max_length=255, blank=True, null=True)
    analysis_sheet = models.FileField(
        upload_to="analysis_sheets/", null=True, blank=True
    )
    claim_charts = models.FileField(upload_to='claim_charts/', null=True, blank=True)
    word_docs = models.FileField(upload_to='word_docs/', null=True, blank=True)
    zip_files = models.FileField(upload_to='zip_files/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.portfolio_code or 'No Code'} - {self.email or 'No Email'}"


class FormUploads(models.Model):
    # patent = models.ForeignKey(SellerForm, on_delete=models.DO_NOTHING, related_name="uploads")
    patent = models.ForeignKey(
    SellerForm,
    on_delete=models.DO_NOTHING,
    related_name="uploads",
    
)
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(
        
        upload_to='uploads/',
        null=True,
        blank=True
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upload no.{self.id}"

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None


class PatentFeedback(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patent_feedback")
    patent = models.ForeignKey(SellerForm, on_delete=models.CASCADE, related_name="feedback")
    action = models.CharField(
        max_length=10,
        choices=[('Pursue', 'Pursue'), ('Pass', 'Pass')],
        default='Unknown'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.email} - {self.patent.patent_number} - {self.action}"


class BuyerForm(models.Model):
    user = models.ForeignKey(
    settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_forms", null=True, blank=True
    )

    # Buyer basic info
    company_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    who_are_you = models.CharField(
        max_length=50, blank=True, null=True,
        choices=[
            ("NPE", "NPE"),
            ("Investor", "Investor"),
            ("Licensing House", "Licensing House"),
            ("Operating Company", "Operating Company"),
            ("Other", "Other"),
        ],
    )
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Acquisition Goals
    purpose = models.CharField(
        max_length=100
    )  # e.g. Litigation defense, Licensing, etc.
    desired_patent_types = models.TextField(blank=True, null=True)

    # Technology Focus
    tech_fields = models.TextField(blank=True, null=True)  # keywords, CPC/IPC classes
    competitors = models.TextField(blank=True, null=True)

    # Portfolio Size & Geography
    portfolio_size = models.CharField(max_length=50, blank=True, null=True)
    jurisdictions = models.TextField(blank=True, null=True)

    # Budget & Deal Structure
    budget_range = models.CharField(max_length=100, blank=True, null=True)
    deal_structure = models.CharField(max_length=100, blank=True, null=True)

    # Risk Appetite
    accept_litigation = models.CharField(
        max_length=20,
        choices=[("Yes", "Yes"), ("No", "No"), ("Case-by-case", "Case-by-case")],
        default="Case-by-case",
    )
    tolerance_for_encumbrances = models.TextField(blank=True, null=True)

    # Timeline & Urgency
    preferred_timeline = models.CharField(max_length=100, blank=True, null=True)
    acquisition_interest = models.CharField(max_length=50, blank=True, null=True)

    # Confidentiality
    nda_required = models.BooleanField(default=True)
    restrictions = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name if self.company_name else "Buyer"


# from django.db import models


class ExternalData(models.Model):
    # sno = models.BigIntegerField()
    sno = models.BigIntegerField(db_column="Sno", primary_key=True)
    applicationNumber = models.CharField(max_length=255, null=True, blank=True)
    patentNumber = models.CharField(max_length=255, null=True, blank=True)
    applicationType = models.CharField(max_length=255, null=True, blank=True)
    PublicationNumber = models.CharField(max_length=255, null=True, blank=True)
    PublicationType = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    entityStatus = models.CharField(max_length=255, null=True, blank=True)
    smallEntityStatus = models.CharField(max_length=255, null=True, blank=True)
    filingDate = models.DateField(null=True, blank=True)
    applicantName = models.CharField(max_length=255, null=True, blank=True)
    inventorBag = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "external_data"  # Supabase me jo table ka naam hai
        managed = (
            False  # table already bana hua hai, Django use sirf read ke liye karega
        )
