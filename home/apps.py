import os
import sys

from django.apps import AppConfig
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError


class HomeConfig(AppConfig):
    name = 'home'
    _sessions_cleared = False

    def ready(self):
        if self._sessions_cleared or not settings.DEBUG:
            return

        if 'runserver' not in sys.argv:
            return

        using_reloader = '--noreload' not in sys.argv
        is_reloader_child = os.environ.get('RUN_MAIN') == 'true'

        # With autoreload enabled, only clear sessions in the serving process.
        if using_reloader and not is_reloader_child:
            return

        try:
            from django.contrib.sessions.models import Session
            Session.objects.all().delete()
            self._sessions_cleared = True
        except (OperationalError, ProgrammingError):
            # Ignore startup states where the sessions table is not ready yet.
            return
