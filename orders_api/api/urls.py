from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from api.views import RegisterAccount, ConfirmAccount, LoginAccount, AccountDetails, ContactView

app_name = 'api'

urlpatterns = [
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('user/details', AccountDetails.as_view(), name='user-details'),
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
]
