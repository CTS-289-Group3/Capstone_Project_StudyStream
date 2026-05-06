from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
from .models import Profile

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, max_length=254)

    class Meta:
        model = Profile
        fields = ['display_name', 'avatar_text', 'bio', 'major', 'year']

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None and not self.is_bound:
            self.fields['email'].initial = user.email

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            return email

        if self.user is None:
            return email

        User = get_user_model()
        exists = User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists()
        if exists:
            raise ValidationError('This email is already in use by another account.')

        return email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user is not None:
            self.user.email = self.cleaned_data.get('email', '')
            if commit:
                self.user.save(update_fields=['email'])
        return profile


class WorkloadPreferencesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'sleep_start_time',
            'sleep_end_time',
            'personal_time_hours_per_week',
            'family_time_hours_per_week',
            'commute_time_hours_per_week',
        ]
        widgets = {
            'sleep_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'sleep_end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        sleep_start = cleaned_data.get('sleep_start_time')
        sleep_end = cleaned_data.get('sleep_end_time')

        if (sleep_start and not sleep_end) or (sleep_end and not sleep_start):
            raise ValidationError('Provide both sleep start and sleep end times, or leave both blank.')

        if sleep_start and sleep_end:
            start_dt = datetime.combine(date.today(), sleep_start)
            end_dt = datetime.combine(date.today(), sleep_end)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            hours = (end_dt - start_dt).total_seconds() / 3600
            if hours > 16:
                raise ValidationError('Sleep window cannot exceed 16 hours per night.')
            cleaned_data['sleep_hours_per_night'] = round(hours, 1)

        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        sleep_hours = self.cleaned_data.get('sleep_hours_per_night')
        if sleep_hours is not None:
            profile.sleep_hours_per_night = sleep_hours
        if commit:
            profile.save()
        return profile