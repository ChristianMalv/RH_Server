from django.urls import path
from django.urls import include
from rest_framework import routers
from django.views.decorators.csrf import csrf_exempt


from .views import (
    PersonListApiView, 
    AreaListApiView,
    SalidaApiView, 
    PersonApiViewSet,
    TipoEquipoViewSet, 
    TipoIngresoViewSet, 
    EquipoViewSet, 
    AsignacionEquipoViewSet, 
    EntradaSalidaEquipoViewSet,
    LDAPDjangoAuthToken
    )


router = routers.DefaultRouter()
router.register(r'tipo-equipos', TipoEquipoViewSet)
router.register(r'tipo-ingresos', TipoIngresoViewSet)
router.register(r'equipos', EquipoViewSet)
router.register(r'asignacion-equipos', AsignacionEquipoViewSet)
router.register(r'entrada-salida-equipos', EntradaSalidaEquipoViewSet)


urlpatterns = [
   path('personal/api', csrf_exempt(PersonListApiView.as_view())),
   path('personal/api/search', csrf_exempt(PersonApiViewSet.as_view({'get': 'list'}))),
   path('personal/api/areas', csrf_exempt(AreaListApiView.as_view())),
   path('personal/api/salida',csrf_exempt(SalidaApiView.as_view())),
   path('equipos/', include(router.urls)),
   path('auth/', LDAPDjangoAuthToken.as_view())
]
