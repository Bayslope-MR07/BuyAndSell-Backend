from django.contrib import admin
from .models import (
    CustomUser,
    FormUploads,
    SellerForm,
    PatentFeedback,
)


# ✅ Custom Admin for CustomUser
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "user_type",
        "is_verified",
        "nda_signed_file_present",
    )
    list_filter = ("user_type", "is_verified")
    search_fields = ("email", "first_name", "last_name")
    actions = ["mark_as_verified"]

    def mark_as_verified(self, request, queryset):
        updated = queryset.filter(user_type="Buyer").update(is_verified=True)
        self.message_user(request, f"{updated} buyer(s) marked as verified.")

    def nda_signed_file_present(self, obj):
        return bool(obj.nda_signed_file)

    nda_signed_file_present.boolean = True
    nda_signed_file_present.short_description = "NDA Uploaded?"


# ✅ Admin for FormUploads to show generated_at as readonly
class UploadsAdmin(admin.ModelAdmin):
    readonly_fields = ("pk", "generated_at")


# ✅ Optional: Tweak for SellerForm for better display in admin
class SellerFormAdmin(admin.ModelAdmin):
    list_display = ("portfolio_code", "tech_domain", "industry", "email")
    search_fields = ("portfolio_code", "tech_domain", "email")
    list_filter = ("industry", "tech_domain", "acquisition_status", "buying_options")


# ✅ Registering all models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(FormUploads, UploadsAdmin)
admin.site.register(SellerForm, SellerFormAdmin)
admin.site.register(PatentFeedback)
