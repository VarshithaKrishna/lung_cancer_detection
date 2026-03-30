from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('patient/', views.upload_ct, name='upload_ct'),
    path('', views.home, name='home'),
    path('know_more/<str:diagnosis>/', views.know_more, name='know_more'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

