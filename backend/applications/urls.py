from django.urls import path

from . import views

urlpatterns = [
    path("", views.ApplicationListCreate.as_view()),
    path("<int:pk>/", views.ApplicationDetail.as_view()),
]
