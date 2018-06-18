
from django.conf.urls import url
from vtatour import views

urlpatterns = [
    url(r'^$', views.index.as_view()), # Notice the URL has been named
    #url(r'^json/', views.json, name='json'), # Notice the URL has been named
   
]
