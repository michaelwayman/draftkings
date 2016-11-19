"""draftkings URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from basketball.views import (
    PlayerDetail,
    HomeView,
    PlayerList,
    TeamDetail,
    TeamList,
    GameDetail,
    ELOView,
    CustomLineupView,
    ContestListView,
    ContestDetailView,
)

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^players/$', PlayerList.as_view(), name='players'),
    url(r'^players/(?P<pk>[0-9]+)/', PlayerDetail.as_view(), name='player'),
    url(r'^teams/$', TeamList.as_view(), name='teams'),
    url(r'^teams/(?P<pk>[0-9]+)/', TeamDetail.as_view(), name='team'),
    url(r'^games/(?P<pk>[0-9]+)/', GameDetail.as_view(), name='game'),
    url(r'^tools/elo/', ELOView.as_view(), name='elo'),
    url(r'^tools/custom-lineup/', CustomLineupView.as_view(), name='custom_lineup'),
    url(r'^contests/', ContestListView.as_view(), name='contests'),
    url(r'^contest/(?P<pk>[0-9]+)/', ContestDetailView.as_view(), name='contest'),
]
