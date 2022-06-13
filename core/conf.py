import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '@j9sgq$_elrgl9np-u=n*xvgki6o-wyf71t_r12d56f8r#xmc7'

DEBUG = True

ALLOWED_HOSTS = ["w-sports.ru"]

DATABASES = {
    'old': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'j92673989_wsports-bd',
        'USER': 'j92673989_admin',
        'PASSWORD': 'Philip7997'
    }
}
