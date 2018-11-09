"""mywatson_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from core import views as core_views
from django.conf.urls.static import static
from django.conf import settings

from core.forms import CustomAuthForm

from django.views.generic.base import RedirectView

from django.views.static import serve



urlpatterns = [
    # path('', core_views.index, name='index'),
    path('', core_views.landing, name='landing'),

    path('login', auth_views.login,
          {'template_name': 'core/login.html',
           'authentication_form': CustomAuthForm,
		   'redirect_authenticated_user': True}, name='login'),

    path('mywatson/', include('mywatson.urls'), name='mywatson'),
    path('admin/', admin.site.urls),
    url(r'^signup/$', core_views.signup, name='signup'),
    # url(r'^login/$', auth_views.login, {'template_name': 'core/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),

    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),

    # url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', core_views.activate, name='activate'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
