import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# import os
# from dotenv import load_dotenv
load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# EMAIL_BACKEND = 'django_ses.SESBackend'
# AWS_SES_REGION_NAME = 'us-east-2'  # Change this based on your AWS region

# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# File storage
# AWS_STORAGE_BUCKET_NAME = 'buyandsellforms'
# AWS_S3_REGION_NAME = 'us-east-2'


DEFAULT_FROM_EMAIL = "SellBuyPatent <patentteam@bayslope.com>"
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!


import os

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-7mq%qz=5wp)afgx&b$707+y@od7hi_ho#&j$oo_98y@i$w44t(",
)

MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
MAILJET_API_SECRET = os.getenv("MAILJET_API_SECRET")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
# DEBUG = False
AUTH_USER_MODEL = "accounts.CustomUser"


ALLOWED_HOSTS = ["*"]

# Google Ids

# GOOGLE_OAUTH_CALLBACK_URL='http://localhost:4200/google-callback'
GOOGLE_OAUTH_CALLBACK_URL = os.getenv(
    "GOOGLE_OAUTH_CALLBACK_URL",
    "https://buyandsell-frontend-6uf8.onrender.com/google-callback",
)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",  # Your app
    "django.contrib.sites",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",  # JWT package
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    "allauth.socialaccount.providers.google",
    # "storages"
]

# Ensure SITE_ID is set
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "accounts.middleware.DisableCSRFMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# django-allauth (social)
# Authenticate if local account with this email address already exists
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
# Connect local account and social account if local account with that email address already exists
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": GOOGLE_CLIENT_ID,
                "secret": GOOGLE_CLIENT_SECRET,
                "key": "",
            },
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {
            # "access_type": "online",
            "access_type": "offline",  # Changed to offline for refresh token
            "prompt": "consent",
        },
    }
}

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}  # Use Email / Password authentication
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"  # Do not require email confirmation

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "https://buyandsell-frontend-6uf8.onrender.com",
    "https://buyandsell-backend-74mg.onrender.com",
    "http://ec2-3-144-99-241.us-east-2.compute.amazonaws.com",
    "https://bas-3nw9.onrender.com",
    "https://sellbuypatent.com",
    "https://www.sellbuypatent.com",
    "http://sellbuypatent-frontend.s3-website-us-east-1.amazonaws.com",
    "https://hba62kd2ksjp72b46igtad3bta0volhy.lambda-url.us-east-1.on.aws",
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:4200",
    "https://buyandsell-frontend-6uf8.onrender.com",
    "https://buyandsell-backend-74mg.onrender.com",
    "http://ec2-3-144-99-241.us-east-2.compute.amazonaws.com",
    "https://bas-3nw9.onrender.com",
    "https://sellbuypatent.com",
    "https://www.sellbuypatent.com",
    "https://api.sellbuypatent.com",
    "http://sellbuypatent-frontend.s3-website-us-east-1.amazonaws.com",
    "https://bp6fqe0ma0.execute-api.us-east-1.amazonaws.com",
]
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "OPTIONS",
    "PATCH",
]

# File Upload Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # Higher than the count of fields

# Media files (Uploaded files)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Ensure the media directory exists
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Ensure the static files directory exists
os.makedirs(STATIC_ROOT, exist_ok=True)

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=50),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_BLACKLIST_ENABLED": True,
}
ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'BuySellPatentDb',
#         'USER': 'Sarita',
#         'PASSWORD':'Bayslope_23',
#         'HOST': 'litigationdbinstance.cd842y2iqcq8.us-east-2.rds.amazonaws.com',
#         'PORT': 5432,

#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


import dj_database_url
import os

# DATABASES = {
#     'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
# }


# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "postgres",
#         "USER": "postgres.ukwjakeaeahmhpfakaoy",
#         "PASSWORD": "BayMay@123_",
#         "HOST": "aws-1-ap-southeast-1.pooler.supabase.com",
#         "PORT": "6543",
#         "OPTIONS": {
#             "sslmode": "require",
#         },
#     }
# }

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.getenv("DB_NAME"),
#         "USER": os.getenv("DB_USER"),
#         "PASSWORD": os.getenv("DB_PASSWORD"),
#         "HOST": os.getenv("DB_HOST"),
#         "PORT": os.getenv("DB_PORT"),
#     }
# }

database_url = os.getenv("DATABASE_URL")
if database_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


REST_AUTH_SERIALIZERS = {
    "SOCIAL_LOGIN_SERIALIZER": "accounts.serializers.CustomSocialLoginSerializer",
}

REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_HTTPONLY": False,  # Makes sure refresh token is sent
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
}
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# EMAIL_HOST = "mail.bayslope.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True

# EMAIL_HOST_USER = "patentteam@bayslope.com"
# EMAIL_HOST_PASSWORD = "Bayoperations@45"

# DEFAULT_FROM_EMAIL = "SellBuyPatent <patentteam@bayslope.com>"




CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SAMESITE = "None"

CSRF_COOKIE_HTTPONLY = False

# Allow CSRF cookie to be shared across subdomains
# CSRF_COOKIE_DOMAIN = ".sellbuypatent.com"
# SESSION_COOKIE_DOMAIN = ".sellbuypatent.com"


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True


CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]
