from django.shortcuts import render, redirect, get_object_or_404
from accounts.forms import RegistrationForm, UserForm, UserProfileForm
from accounts.models import Account, UserProfile
from django.contrib import messages, auth
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from carts.views import CartMixin
from carts.models import Cart, CartItem
from order.models import Order, OrderProduct
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
import requests
from django.views.generic import View, TemplateView

class RegisterView(TemplateView):
    template_name = 'accounts/register.html'

    def get(self, request):
        form = RegistrationForm()
        context = {'form': form}
        return render(request, self.template_name, context)

    
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()
            
            # Create a user profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, "Registeration Successfully")
            return redirect('/accounts/login/?command=verification&email='+email)
        context = {'form': form}
        return render(request, 'accounts/register.html', context)

class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html')

    def post(self, request):
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cartM = CartMixin()
                cart_id = cartM(request)

                cart = Cart.objects.get(cart_id=cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('index')
        else:
            messages.error(request, 'Invalid login credentials')
        return redirect('accounts:login')

class LogoutView(View):
    def get(self, request):
        auth.logout(request)
        messages.success(request, 'You are logged out.')
        return redirect('index')

class ForgotPasswordView(View):
    def get(self, request):
        return render(request, 'accounts/forgot_password.html')

    def post(self, request):
        email = request.POST['email']
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('accounts:forgot-password')

class ResetPasswordValidateView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            User = get_user_model()
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            request.session['uid'] = uid
            messages.success(request, 'Please reset your password')
            return redirect('accounts:reset-password')
        else:
            messages.error(request, 'This link has expired!')
            return redirect('accounts:login')

class ResetPasswordView(View):
    def get(self, request):
        return render(request, 'accounts/reset_password.html', {'form': PasswordResetForm()})

    def post(self, request):
        # form = PasswordResetForm(request.POST)
        # if form.is_valid():
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            User = get_user_model()
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('accounts:login')
            # else:
            #     messages.error(request, 'Password does not match!'
        
        return render(request, 'accounts/reset_password.html')


    
class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Account._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, 'Congratulations! Your account is activated.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Invalid activation link')
            return redirect('accounts:register')
        

class DashboardView(View):
    @method_decorator(login_required(login_url='accounts:login'))
    def get(self, request):
        try:
            userprofile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            userprofile = None

        orders = Order.objects.order_by('-created_at').filter(user=request.user, is_ordered=True)
        orders_count = orders.count()
        
        context = {
            'orders_count': orders_count,
            'userprofile': userprofile,
        }
        return render(request, 'accounts/dashboard.html', context)
    
class MyOrdersView(View):
    @method_decorator(login_required(login_url='login'))
    def get(self, request):
        orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
        context = {
            'orders': orders,
        }
        return render(request, 'accounts/my_orders.html', context)

class EditProfileView(View):
    @method_decorator(login_required(login_url='accounts:login'))
    def get(self, request):
        userprofile = get_object_or_404(UserProfile, user=request.user)
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'userprofile': userprofile,
        }
        return render(request, 'accounts/edit_profile.html', context)

    def post(self, request):
        userprofile = get_object_or_404(UserProfile, user=request.user)
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:edit_profile')
        else:
            messages.error(request, 'There was an error updating your profile.')
            return redirect('accounts:edit_profile')

@method_decorator(login_required(login_url='login'), name='dispatch')
class ChangePasswordView(View):
    template_name = 'accounts/change_password.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully.')
                return redirect('accounts:login')
            else:
                messages.error(request, 'Please enter a valid current password')
                return render(request, self.template_name)
        else:
            messages.error(request, 'Passwords do not match!')
            return render(request, self.template_name)

@method_decorator(login_required(login_url='login'), name='dispatch')
class OrderDetailView(View):
    template_name = 'accounts/order_detail.html'

    def get(self, request, order_id):
        try:
            order_detail = OrderProduct.objects.filter(order__order_number=order_id)
            order = Order.objects.get(order_number=order_id)
            subtotal = sum(item.product_price * item.quantity for item in order_detail)

            print(order_detail)
            print(order)
            print(subtotal)
            context = {
                'order_detail': order_detail,
                'order': order,
                'subtotal': subtotal,
            }

            return render(request, self.template_name, context)
        except Order.DoesNotExist:
            # Handle the case where the order doesn't exist
            return render(request, 'accounts/order_not_found.html')
