from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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
            'sleep_hours_per_night',
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
        sleep_hours = cleaned_data.get('sleep_hours_per_night')
        sleep_start = cleaned_data.get('sleep_start_time')
        sleep_end = cleaned_data.get('sleep_end_time')

        if sleep_hours is not None and sleep_hours == 0 and (sleep_start or sleep_end):
            raise ValidationError('If sleep hours are set to 0, clear sleep start and end times.')

        if (sleep_start and not sleep_end) or (sleep_end and not sleep_start):
            raise ValidationError('Provide both sleep start and sleep end times, or leave both blank.')

        return cleaned_data