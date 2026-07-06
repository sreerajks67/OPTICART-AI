from django.contrib.auth.decorators import login_required, user_passes_test


def is_admin(user):
    return user.is_authenticated and user.is_superuser


admin_required = user_passes_test(
    is_admin,
    login_url='login',
)
