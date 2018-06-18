
from django.conf.urls import url, include # Add include to the imports here
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    #url(r'^$', include('vt.urls')), # tell django to read urls.py in example app
    url(r'^$', include('vtatour.urls')) # tell django to read urls.py in example app
]
