from django.contrib import admin
from .models import (
	PersonalEvent,
	RecurringPersonalEvent,
	RecurringJobTitle,
	RecurringWorkLocation,
	RecurringWorkShift,
	WorkloadAnalysis,
	WorkShift,
)
from .models import Workspace


admin.site.register(PersonalEvent)
admin.site.register(WorkShift)
admin.site.register(RecurringWorkShift)
admin.site.register(RecurringPersonalEvent)
admin.site.register(RecurringWorkLocation)
admin.site.register(RecurringJobTitle)
admin.site.register(Workspace)
admin.site.register(WorkloadAnalysis)