from django.urls import path
from .views import auth, account


urlpatterns = [
    # auth urls...
    path('login/', auth.login_view, name='login'),
    path('register/', auth.register_view, name='register'),
    path('logout/', auth.logout_view, name='logout'),

    # user urls...
    path('user/me/', account.account_view, name='account'),
    path('user/settings/', account.settings_view, name='settings'),
]
