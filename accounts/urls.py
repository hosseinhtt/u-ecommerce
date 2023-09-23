from django.urls import path
from accounts.views import *
app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('forgot/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('resetpassword_validate/<uidb64>/<token>/', ResetPasswordValidateView.as_view(), name='resetpassword_validate'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]