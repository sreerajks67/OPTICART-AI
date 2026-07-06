from django.apps import AppConfig


class CartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cart'

    def ready(self):

        import os

        # prevents double scheduler
        if os.environ.get('RUN_MAIN') == 'true':

            from .scheduler import start

            start()