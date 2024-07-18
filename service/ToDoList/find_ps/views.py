from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import PasswordResetRequestForm, VerifyCodeForm
from .models import PasswordResetCode
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(username=username, email=email)
                code = get_random_string(6, allowed_chars='0123456789')
                PasswordResetCode.objects.create(user=user, code=code)
                send_mail(
                    'Password Reset Verification Code',
                    f'Your verification code is: {code}',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
                request.session['user_id'] = user.id
                return redirect('verify_code')
            except User.DoesNotExist:
                messages.error(request, 'No user is associated with this username and email address.')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'find_ps/password_reset_request.html', {'form': form})

def verify_code(request):
    if request.method == 'POST':
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            new_password = form.cleaned_data['new_password']
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    reset_code = PasswordResetCode.objects.filter(user=user, code=code, created_at__gte=datetime.now()-timedelta(minutes=10)).first()
                    if reset_code:
                        user.set_password(new_password)
                        user.save()
                        messages.success(request, 'Your password has been reset successfully.')
                        return redirect('login')  # Assuming you have a login view to redirect to
                    else:
                        messages.error(request, 'Invalid or expired verification code.')
                except User.DoesNotExist:
                    messages.error(request, 'Invalid user.')
            else:
                messages.error(request, 'No user session found.')
    else:
        form = VerifyCodeForm()

    return render(request, 'find_ps/verify_code.html', {'form': form})