from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import (
    PersonListApiView, AreaListApiView,
    )
urlpatterns = [
   path('personal/api', csrf_exempt(PersonListApiView.as_view())),
   path('personal/api/areas', csrf_exempt(AreaListApiView.as_view())),
   
]