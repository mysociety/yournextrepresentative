"""
Django settings for mysite project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
import os
import sys
import yaml
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

configuration_file = os.path.join(
    BASE_DIR, 'conf', 'general.yml'
)
with open(configuration_file) as f:
    conf = yaml.load(f)

# Load the credentials for the PopIt instance

POPIT_INSTANCE = conf['POPIT_INSTANCE']
POPIT_HOSTNAME = conf['POPIT_HOSTNAME']
POPIT_PORT = conf.get('POPIT_PORT', 80)
POPIT_USER = conf.get('POPIT_USER', '')
POPIT_PASSWORD = conf.get('POPIT_PASSWORD', '')
POPIT_API_KEY = conf.get('POPIT_API_KEY', '')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = conf['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(conf.get('STAGING')))

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'mysite', 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS += (
    # Required by allauth template tags
    "django.core.context_processors.request",
    # allauth specific context processors
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
)

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_nose',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.twitter',
    'pipeline',
    'candidates',
    'debug_toolbar',
)

SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

SOCIALACCOUNT_PROVIDERS = {
    'google': {'SCOPE': ['https://www.googleapis.com/auth/userinfo.profile'],
               'AUTH_PARAMS': {'access_type': 'online'}},
}

LOGIN_REDIRECT_URL = '/'

SOCIALACCOUNT_AUTO_SIGNUP = False

ROOT_URLCONF = 'mysite.urls'

WSGI_APPLICATION = 'mysite.wsgi.application'

DEBUG_TOOLBAR_PATCH_SETTINGS = False

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

if 'test' not in sys.argv:
    STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_CSS = {
    'all': {
        'source_filenames': (
            'candidates/style.scss',
            'select2/select2.css',
            'jquery/jquery-ui.css',
            'jquery/jquery-ui.structure.css',
            'jquery/jquery-ui.theme.css',
        ),
        'output_filename': 'css/all.css',
    }
}

PIPELINE_JS = {
    'all': {
        'source_filenames': (
            'jquery/jquery-1.11.1.js',
            'jquery/jquery-ui.js',
            'foundation/js/foundation/foundation.js',
            'foundation/js/foundation/foundation.equalizer.js',
            'foundation/js/foundation/foundation.dropdown.js',
            'foundation/js/foundation/foundation.tooltip.js',
            'foundation/js/foundation/foundation.offcanvas.js',
            'foundation/js/foundation/foundation.accordion.js',
            'foundation/js/foundation/foundation.joyride.js',
            'foundation/js/foundation/foundation.alert.js',
            'foundation/js/foundation/foundation.topbar.js',
            'foundation/js/foundation/foundation.reveal.js',
            'foundation/js/foundation/foundation.slider.js',
            'foundation/js/foundation/foundation.magellan.js',
            'foundation/js/foundation/foundation.clearing.js',
            'foundation/js/foundation/foundation.orbit.js',
            'foundation/js/foundation/foundation.interchange.js',
            'foundation/js/foundation/foundation.abide.js',
            'foundation/js/foundation/foundation.tab.js',
            'select2/select2.js',
        ),
        'output_filename': 'js/all.js'
    }
}

PIPELINE_COMPILERS = (
  'pipeline.compilers.sass.SASSCompiler',
)

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'

# On some platforms this might be called "yuicompressor", so it may be
# necessary to symlink it into your PATH as "yui-compressor".
PIPELINE_YUI_BINARY = '/usr/bin/env yui-compressor'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--nocapture',
    '--with-doctest',
    '--with-coverage',
    '--cover-package=candidates'
]
