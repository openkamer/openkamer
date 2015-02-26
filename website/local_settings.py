DEBUG = True
TEMPLATE_DEBUG = True

# SECURITY WARNING: Make this unique, and don't share it with anybody.
SECRET_KEY = 'p]+zH>-(*NY0~d5[%9m06z(C|6W*uS^x_xX=j7<=QE$9=dt+VS'

TIME_ZONE = "Europe/Amsterdam"

ALLOWED_HOSTS = ['127.0.0.1']

DATABASES = {
    "default": {
        # Add "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.db.backends.sqlite3",
        # DB name or path to database file if using sqlite3.
        "NAME": "dev.db",
        # Not used with sqlite3.
        "USER": "",
        # Not used with sqlite3.
        "PASSWORD": "",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}
