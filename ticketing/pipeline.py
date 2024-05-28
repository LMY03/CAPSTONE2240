from .models import UserProfile

def create_or_update_user_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        # You can set the user type here based on additional logic or user input
        # For example, setting a default user type
        if created:
            user_profile.user_type = 'student'  # Default to student or determine based on response
            user_profile.save()