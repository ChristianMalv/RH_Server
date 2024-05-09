from django.urls import path
from .views import (
    PersonListApiView, AreaListApiView,
    )
urlpatterns = [
   path('personal/api', PersonListApiView.as_view()),
   path('personal/api/areas', AreaListApiView.as_view()),
   
]