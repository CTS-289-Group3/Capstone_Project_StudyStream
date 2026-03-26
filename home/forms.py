from django import forms

from core.models import (
    PersonalEvent,
    RecurringPersonalEvent,
    RecurringJobTitle,
    RecurringWorkLocation,
    RecurringWorkShift,
    WorkShift,
)


class PersonalEventForm(forms.ModelForm):
    recurring_enabled = forms.BooleanField(required=False, label="Make this a recurring event")
    recurrence_pattern = forms.ChoiceField(
        choices=RecurringPersonalEvent.RECUR_CHOICES,
        required=False,
        label="Repeat",
    )
    selected_weekdays = forms.MultipleChoiceField(
        choices=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Weekdays",
    )
    monthly_day = forms.IntegerField(required=False, min_value=1, max_value=31, label="Day of month")
    recurring_is_active = forms.BooleanField(required=False, initial=True, label="Recurring event active")

    class Meta:
        model = PersonalEvent
        fields = ["title", "description", "event_date", "start_time", "end_time", "location"]
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("recurring_enabled"):
            return cleaned_data

        recurrence_pattern = cleaned_data.get("recurrence_pattern")
        selected_weekdays = cleaned_data.get("selected_weekdays") or []
        monthly_day = cleaned_data.get("monthly_day")
        event_date = cleaned_data.get("event_date")

        if not recurrence_pattern:
            self.add_error("recurrence_pattern", "Select a recurring pattern.")

        if recurrence_pattern in {"weekly", "biweekly"} and not selected_weekdays:
            self.add_error("selected_weekdays", "Select at least one weekday.")

        if recurrence_pattern == "monthly":
            if not monthly_day and event_date:
                cleaned_data["monthly_day"] = event_date.day

        return cleaned_data

    def save_personal_event(self, user, commit=True):
        event = super().save(commit=False)
        event.user = user
        if commit:
            event.save()
        return event

    def save_recurring_event(self, user, commit=True):
        event_date = self.cleaned_data["event_date"]
        recurrence_pattern = self.cleaned_data["recurrence_pattern"]
        selected_weekdays = self.cleaned_data.get("selected_weekdays") or []

        recurring_event = RecurringPersonalEvent(
            user=user,
            title=self.cleaned_data["title"],
            description=self.cleaned_data.get("description", ""),
            start_date=event_date,
            start_time=self.cleaned_data.get("start_time"),
            end_time=self.cleaned_data.get("end_time"),
            location=self.cleaned_data.get("location", ""),
            recurrence_pattern=recurrence_pattern,
            weekdays=",".join(sorted(selected_weekdays)) if recurrence_pattern in {"weekly", "biweekly"} else "",
            monthly_day=(self.cleaned_data.get("monthly_day") or event_date.day) if recurrence_pattern == "monthly" else None,
            is_active=self.cleaned_data.get("recurring_is_active", True),
        )

        if commit:
            recurring_event.save()

        return recurring_event


class WorkShiftForm(forms.ModelForm):
    class Meta:
        model = WorkShift
        fields = ["job_title", "shift_date", "start_time", "end_time", "location", "notes", "color_hex"]
        widgets = {
            "shift_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "color_hex": forms.HiddenInput(),
        }


class RecurringWorkShiftForm(forms.ModelForm):
    class Meta:
        model = RecurringWorkShift
        fields = ["name", "start_time", "end_time", "location", "is_active"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }


class RecurringWorkLocationForm(forms.ModelForm):
    class Meta:
        model = RecurringWorkLocation
        fields = ["name", "is_active"]


class RecurringJobTitleForm(forms.ModelForm):
    class Meta:
        model = RecurringJobTitle
        fields = ["title", "is_active"]


class RecurringPersonalEventForm(forms.ModelForm):
    selected_weekdays = forms.MultipleChoiceField(
        choices=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Weekdays",
    )

    class Meta:
        model = RecurringPersonalEvent
        fields = [
            "title",
            "description",
            "start_date",
            "start_time",
            "end_time",
            "location",
            "recurrence_pattern",
            "monthly_day",
            "is_active",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.weekdays:
            self.fields["selected_weekdays"].initial = self.instance.weekdays.split(",")

    def clean(self):
        cleaned_data = super().clean()
        recurrence_pattern = cleaned_data.get("recurrence_pattern")
        selected_weekdays = cleaned_data.get("selected_weekdays") or []
        monthly_day = cleaned_data.get("monthly_day")
        start_date = cleaned_data.get("start_date")

        if recurrence_pattern in {"weekly", "biweekly"} and not selected_weekdays:
            self.add_error("selected_weekdays", "Select at least one weekday.")

        if recurrence_pattern == "monthly":
            if not monthly_day and start_date:
                cleaned_data["monthly_day"] = start_date.day
            if cleaned_data.get("monthly_day") and not 1 <= cleaned_data["monthly_day"] <= 31:
                self.add_error("monthly_day", "Monthly day must be between 1 and 31.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected_weekdays = self.cleaned_data.get("selected_weekdays") or []

        if instance.recurrence_pattern in {"weekly", "biweekly"}:
            instance.weekdays = ",".join(sorted(selected_weekdays))
            instance.monthly_day = None
        else:
            instance.weekdays = ""

        if commit:
            instance.save()

        return instance
