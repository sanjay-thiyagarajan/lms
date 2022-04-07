from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('', include('panel.urls'), name='home'),
    path('admin/', admin.site.urls),
]
