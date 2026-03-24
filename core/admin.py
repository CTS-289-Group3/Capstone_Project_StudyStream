from django.contrib import admin
from .models import PersonalEvent, WorkShift
from .models import Workspace


admin.site.register(PersonalEvent)
admin.site.register(WorkShift)
admin.site.register(Workspace)