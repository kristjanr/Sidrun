"""
Django settings for tasks project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MEDIA_ROOT = BASE_DIR + "/media/"
MEDIA_URL = '/media/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qk@lhmatzr$3fu=eua$urd73me&7@7louxx4v5=6p20)+_2f%m'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sidrun',
    'django_summernote',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tasks.urls'

WSGI_APPLICATION = 'tasks.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tasks',
        'USER': os.getlogin(),
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Tallinn'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_ROOT = 'sidrun/static/'
STATIC_URL = '/static/'

# more config options: https://github.com/lqez/django-summernote#options
SUMMERNOTE_CONFIG = {

    # Change editor size
    'width': '90%',
    'height': '300',
    'toolbar': [["style", ["style"]],
              ["font", ["bold", "italic", "underline", "superscript", "subscript", "strikethrough", "clear"]],
              ["fontname", ["fontname"]], ["color", ["color"]], ["para", ["ul", "ol", "paragraph"]],
              ["height", ["height"]], ["table", ["table"]], ["insert", ["link", "video", "hr"]],
              ["view", ["fullscreen", "codeview"]], ["help", ["help"]]]

}