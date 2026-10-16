from django.utils.deprecation import MiddlewareMixin


class DisableCSRFMiddleware(MiddlewareMixin):
    """
    Sirf API-type paths ke liye CSRF disable karega.
    Django admin, normal HTML forms par CSRF chalta rahega.
    """

    API_PREFIXES = (
        "/accounts/",  # tumhara existing
        "/dj-rest-auth/",  # agar dj-rest-auth use kar rahe ho
        "/api/",  # agar koi custom api/ prefix hai
    )

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Sirf unsafe methods ke liye CSRF disable karo
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if request.path.startswith(self.API_PREFIXES):
                setattr(request, "_dont_enforce_csrf_checks", True)
        return None
