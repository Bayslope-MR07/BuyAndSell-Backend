from django.urls import path
from .views.views import (
    BuyerViewDetail,
    SignUpView,
    # LoginView,
    LogoutView,
    seller_form_submission,
    SellerFormListView,
    BuyerViewList,
    VerifySellerView,
    BuyerActionCreateAPIView,
    SellerDataView,
    upload_excel,
    upload_embedded,
    get_buyer_actions,
    SellerFormListViewPerUser,
    get_buyer_actions_byId,
    UpdateUserView,
    ChangePasswordView,
    PatentAnalyticsView,
    get_embedded_file_urls,
    get_matching_sellers,
    UploadNDA,
    SendAnalysisEmailView,
    admin_user_list,
    admin_user_verify,
    admin_user_unverify,
    contact_form,
    csrf,
    login_test,
    external_data_list,
    reach_out_for_patent,
)
from django.conf.urls.static import static
from backend import settings
from rest_framework_simplejwt.views import TokenRefreshView
from .views.googleLogin import google_signup
from .views.views import (
    send_reset_password_email,
    reset_password,
    UpdateSellerFormFileView,
    get_patent_files,
    UploadAndLinkToAllSellerForms
    # upload_embedded,
    
)
# from .views import contact_form

# from django.urls import path
from .views.views import BuyerFormSubmissionView
# from django.urls import path
from . import views

urlpatterns = [
    path("google-signup/", google_signup, name="google-signup"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("update-profile/", UpdateUserView.as_view(), name="update-profile"),
    # path("login/", login_test, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("buyer-actions/", get_buyer_actions, name="buyer-actions"),
    path("buyer-actions/<int:id>", get_buyer_actions_byId, name="buyer-actions"),
    path("seller-form/", seller_form_submission, name="seller-form-create"),
    path("seller-data/", SellerFormListView.as_view(), name="seller-data"),
    path("user-seller-data/", SellerFormListViewPerUser.as_view(), name="seller-data"),
    path("seller-da/", SellerDataView.as_view(), name="seller-data"),
    path(
        "accounts/verify-seller/<int:pk>/",
        VerifySellerView.as_view(),
        name="verify-seller",
    ),
    path("buyer-data/", BuyerViewList.as_view(), name="buyer-data"),
    path("buyer-data/<int:id>/", BuyerViewDetail.as_view(), name="buyer-detail"),
    path(
        "buyerChoice/", BuyerActionCreateAPIView.as_view(), name="buyer-action-create"
    ),
    path("upload_excel/", upload_excel, name="upload-excel"),
    path("upload_embedded/", upload_embedded, name="upload-embedded"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("analytics/", PatentAnalyticsView.as_view(), name="analytics"),
    path("forgot-password/", send_reset_password_email, name="forgot-password"),
    path("reset-password/", reset_password, name="reset-password"),
    path(
        "update-filepath/",
        UploadAndLinkToAllSellerForms.as_view(),
        name="update-filepath",
    ),
    path("see-files/<str:patent_id>/", get_patent_files, name="update-filepath"),
    path(
        "sellers/<int:seller_id>/embedded-files/",
        get_embedded_file_urls,
        name="get-embedded-files",
    ),
    path(
        "buyer_form_submission/",
        BuyerFormSubmissionView.as_view(),
        name="buyer_form_submission",
    ),
    path(
        "buyers/<int:buyer_id>/matches/",
        get_matching_sellers,
        name="get_matching_sellers",
    ),
    path("api/upload-nda/", UploadNDA.as_view(), name="upload-nda"),
    # path("download/<str:filename>/", views.download_file, name="download_file"),
    # path(
    #     "buyers/<int:buyer_id>/matches/",
    #     views.get_matching_sellers,
    #     name="buyer-matches",
    # ),
    path("send-analysis-email/", SendAnalysisEmailView.as_view()),
    path("admin/users/", admin_user_list, name="admin_user_list"),
    path(
        "admin/users/<int:user_id>/verify/", admin_user_verify, name="admin_user_verify"
    ),
    path(
        "admin/users/<int:user_id>/unverify/",
        admin_user_unverify,
        name="admin_user_unverify",
    ),
    path("contact/", contact_form, name="contact_form"),
    path("external-data/", external_data_list),
    path("reach-out/", reach_out_for_patent, name="reach-out"),
    # path("contact/", views.contact_form, name="contact_form"),
    path("csrf/", csrf),
]
