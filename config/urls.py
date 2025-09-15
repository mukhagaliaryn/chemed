from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve


urlpatterns = [
    path('summernote/', include('django_summernote.urls')),
    path('__reload__/', include('django_browser_reload.urls')),
    path('admin/', admin.site.urls),

    path('account/', include('apps.account.urls')),
    path('', include('apps.dashboard.student.urls')),
    path('teacher/', include('apps.dashboard.teacher.urls')),
]


urlpatterns += [re_path(r'^i18n/', include('django.conf.urls.i18n'))]
urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
urlpatterns += [re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT})]
