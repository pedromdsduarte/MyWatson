from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import SignupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
from core.forms import CustomAuthForm



def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("mywatson")
    else:
        return redirect(reverse('login'))


def landing(request):
    if request.method == 'POST':

        signup_form = SignupForm(auto_id='signup_%s')
        login_form = CustomAuthForm(auto_id='login_%s')

        if (request.POST.get('form_type') == 'signup'):
            signup_form = SignupForm(request.POST, auto_id='signup_%s')

            if signup_form.is_valid():
                signup_form.save()
                username = signup_form.cleaned_data.get('username')
                raw_password = signup_form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                login(request, user)
                return redirect(reverse('mywatson:index'))

        elif (request.POST.get('form_type') == 'login'):

            login_form = CustomAuthForm(data=request.POST, auto_id='login_%s')

            if login_form.is_valid():

                username = request.POST['username']
                raw_password = request.POST['password']
                user = authenticate(username=username, password=raw_password)

                login(request, user)

                return redirect(reverse('mywatson:index'))

    else:
        signup_form = SignupForm(auto_id='signup_%s')
        login_form = CustomAuthForm(auto_id='login_%s')
    return render(request, 'core/landing.html', {'signup_form': signup_form,
                                                 'login_form': login_form})


"""
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})
"""

"""
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():

            to_email = form.cleaned_data.get('email')

            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your MyWatson account'

            domain = current_site.domain
            domain = 'localhost:8000'
            uid = urlsafe_base64_encode(force_bytes(user.pk)).decode('utf-8')
            token = account_activation_token.make_token(user)

            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': domain,
                'uid': uid,
                'token': token,
            })

            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')

"""


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect(reverse('index'))
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})
