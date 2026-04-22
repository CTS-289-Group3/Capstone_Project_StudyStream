from .models import Profile

def profile_context(request):
    if not request.user.is_authenticated:
        return {}
    profile = Profile.objects.filter(user=request.user).first()
    display = profile.display_name if profile and profile.display_name else request.user.username
    avatar  = profile.avatar_text[:1].upper() if profile and profile.avatar_text else display[:1].upper()
    return {
        'profile_display_name': display,
        'profile_avatar_text':  avatar,
    }
