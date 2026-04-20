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