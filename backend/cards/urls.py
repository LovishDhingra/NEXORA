from django.urls import path

from .views import ChangePinView

urlpatterns = [path("change-pin/", ChangePinView.as_view())]
