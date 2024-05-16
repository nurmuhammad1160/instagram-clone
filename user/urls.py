from django.urls import path
from . import views


urlpatterns = [
    path('singup/', views.UserCreate.as_view()),
    path('verify/', views.VerifyApiView.as_view()),
    path('new_verify/', views.GetNewVerifyCode.as_view()),
    path('update_user/', views.UserChangeInformation.as_view())
]
