from django.conf.urls import url

from . import views

urlpatterns = [
				url(r'^$', views.index, name='index'),
				url(r'^auth/', views.authenticate, name='authenticate'),
				url(r'^error/', views.error, name='error'),
				url(r'^analyze/', views.process, name='process'),
				url(r'^results/', views.results, name='results'),
]