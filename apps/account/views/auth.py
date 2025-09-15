from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.account.forms import UserRegisterForm


# login page
# ----------------------------------------------------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('student')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('student')
        else:
            messages.error(request, _('Пайдаланушының аты немесе пароль қате кетті!'))
    else:
        form = AuthenticationForm()

    return render(request, 'app/account/login/page.html', {'form': form})


# register page
# ----------------------------------------------------------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('student')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('student')
        else:
            messages.error(request, _('Тіркеу сәтсіз аяқталды. Деректерді тексеріңіз!'))
    else:
        form = UserRegisterForm()

    return render(request, 'app/account/register/page.html', {'form': form})


# logout
# ----------------------------------------------------------------------------------------------------------------------
def logout_view(request):
    logout(request)
    return redirect('login')
