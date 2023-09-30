from django.urls import path
from accounts.views import *
app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),

    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('resetpassword_validate/<uidb64>/<token>/', ResetPasswordValidateView.as_view(), name='resetpassword_validate'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('activate/<uidb64>/<token>/', ActivateAccountView.as_view(), name='activate'),

    path('my_orders/',MyOrdersView.as_view(), name='my_orders'),
    path('edit_profile/', EditProfileView.as_view(), name='edit_profile'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),
    path('order_detail/<int:order_id>/', OrderDetailView.as_view(), name='order_detail'),
]