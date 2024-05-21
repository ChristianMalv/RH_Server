from django.urls import path
from django.contrib import admin
from django.urls import re_path
from django.conf.urls import include
from people.views import PersonListView, PersonCreateView, PersonUpdateView, ReportePersonasPDF, PersonCheckView, searchPerson, saveCheckedPerson, PersonBajaListView, GetPersonas, InsertBaja, DirectoryListView, GetPersonasDirectory, GetCompPersonas, InsertComp, PersonCompListView, DetalleIncidencias, PersonInciListView, ReporteIncidenciasPDF, UpdateIncidencia, GetPersonasIncidencia, AddIncidencia, DeleteIncidencia, PersonDirectoryUpdateView, DeleteComp, AreasListView, json_to_pdf, GetPersonasCompensacion, compensacionesArea, IncidenciaConsulta, ValidatePersonIncidencia, DetailPersonIncidencia, GetIncidenciaTable, \
    loginAdmin, AdminConsulta, AdminInciListView, GetAdminIncidencia, reporteIncidencias, PersonAyudaListView, GetAyudaPersonas, InsertAyuda, DeleteAyuda, GetPersonasAyuda, DashboardCheck, UpdateDashboard, \
        GetPersonaAyuda,  SersocListView, SersocCreateView, CreateSersocPerson, AddAyuda, DeleteAyudaMonto, ValidateRFC, PersonVacacionesListView, GetPersonasVacacion, GetDetalleVacacion, \
        GetAsistencia, DeleteDayVacacion, SersocAsistListView, CapacitacionCreateView, CapacitacionListView, SaveCapacitacion, loginUsers, Capacitacion, CapacitacionesxPersona
from django.contrib.auth import views
from django.contrib.auth.decorators import login_required
from crede_api import urls as crede_urls
from registro import urls as registro_urls
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(next_page='/'), name='logout'),
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.LogoutView.as_view(next_page='/'), name='logout'),
    
    path('', PersonListView.as_view(), name='person_list'),
    path('activos/personas',PersonListView.as_view(), name='activos_list'),
    path('bajas/personas', PersonBajaListView.as_view(), name='baja_list' ),
    path('get_personas/', GetPersonas, name="get_Personas"),
    path('insert_baja/', InsertBaja, name="insert_baja"),

    #Vacaciones
    path('vacaciones/personas', PersonVacacionesListView.as_view(), name='vacaciones_list' ),
    path('vacaciones/busqueda', GetPersonasVacacion , name='search_person_vacacion'),
    path('vacaciones/detalle', GetDetalleVacacion , name='detail_vacacion'),
    path('vacaciones/delete', DeleteDayVacacion, name='delete_vacacion'),

    #Compensaciones
    path('compensaciones/personas', PersonCompListView.as_view(), name='comp_list' ),
    path('get_personas_comp/', GetCompPersonas, name="get_PersonasComp"),
    path('compensaciones/insert/', InsertComp, name="insert_comp"),
    path('compensaciones/delete', DeleteComp, name='delete_Compensacion' ),
    path('compensaciones/print/<str:fechaInicio>/<str:fechaFin>/<int:folio>', json_to_pdf, name='print_Compensaciones'),
    path('compensaciones/printarea/<str:fechaInicio>/<str:fechaFin>/<int:folio>', compensacionesArea, name='print_CompensacionesArea'),
    path('search_compensacion/', GetPersonasCompensacion, name='search_person_compensacion'),

    #Incidencias
    path('incidencias/personas', PersonInciListView.as_view(), name='inci_list' ),
    path('incidencias/imprimir/<int:pk>/<str:fechaInicio>/<str:fechaFin>', ReporteIncidenciasPDF.as_view(), name="incidencia_print_rango"),
    path('incidencias/detalle/<int:pk>/<str:fechaInicio>/<str:fechaFin>',  login_required(DetalleIncidencias.as_view()), name="detalle_incidencia_rango"),
    path('incidencias/detalle/<int:pk>/<str:fechaInicio>/',  login_required(DetalleIncidencias.as_view()), name="detalle_incidencia"),
    
    path('incidencias/update', UpdateIncidencia, name='update_Incidencia' ),
    path('incidencias/add', AddIncidencia, name='add_Incidencia' ),
    path('incidencias/delete', DeleteIncidencia, name='delete_Incidencia' ),
    path('search_incidencia/', GetPersonasIncidencia, name='search_person_incidencia'),
    path('incidencias/imprimir/<int:pk>/<str:fechaInicio>/<str:fechaFin>/<str:bases>', ReporteIncidenciasPDF.as_view(), name="print_all_Incidencia" ),
    

    #Consulta Incidencias por Personal
    path('incidencia/login', IncidenciaConsulta.as_view(), name="incidencia_consulta"),
    path('incidencia/validate', ValidatePersonIncidencia, name="validate_person"),
    path('incidencia/detail/<str:pk>', DetailPersonIncidencia.as_view()),
    path('incidencia/get/table', GetIncidenciaTable, name="get_incidencias"),
    #Consulta de Incidencias por Directivos
    path('incidencia/admin/login', AdminConsulta.as_view()),
    path('incidencia/admin/validate', loginAdmin, name="consulta_admin"),
    path('incidencia/admin/personas/<str:matricula>', AdminInciListView.as_view(), name='inci_list' ),
    path('incidencia/admin/search', GetAdminIncidencia, name='search_admin_incidencia'),
    path('incidencias/detalle/<str:admin>/<int:pk>/<str:fechaInicio>/<str:fechaFin>', DetalleIncidencias.as_view(), name="admin_detalle_incidencia_rango"),
    path('incidencias/reporte/<int:incidencia>/<str:fechaInicio>/<str:fechaFin>', reporteIncidencias, name="reporte_incidencia"),
    path('incidencia/admin/dashboard',DashboardCheck.as_view(), name="dashboard_admin"),
    path('incidencia/admin/update_dashboard', UpdateDashboard , name='update_dashboard'),
   

    path('admin/', admin.site.urls),
    path('add/', PersonCreateView.as_view(), name='person_add'),
    path('<int:pk>/edit/', PersonUpdateView.as_view(), name='person_edit'),
    path('<int:pk>/print/', ReportePersonasPDF.as_view(), name='person_print'),
    
    #Checador
    path('check/', PersonCheckView.as_view(), name='person_check'),
    path('checked/', saveCheckedPerson, name='person_check'),
    path('search/', searchPerson, name='person_search'), 
    ###########
    
    re_path(r'^chaining/', include('smart_selects.urls')),
    path('filter/<str:q>/', PersonCreateView.as_view(), name='person_filter'),
    #path('incidencia/<str:person>/changeIncidencias/<str:year>/<str:month>/<str:day><str:photo>', showImage, name='show_Imagen'),
    
    #Directorio
    path('directorio/personas',DirectoryListView.as_view(), name='directorio'),
    path('directorio/search', GetPersonasDirectory, name='search_directory'),
    path('<int:pk>/directory/edit/', PersonDirectoryUpdateView.as_view(), name='person_directory_edit'),    

    #Areas
    path('areas', AreasListView.as_view(), name='areas_list' ),

    ##Ayudas
    path('ayuda/personas', PersonAyudaListView.as_view(), name='ayuda_list' ),
    path('get_personas_ayuda/', GetAyudaPersonas, name="get_PersonasAyuda"),
    path('ayuda/agregar/', AddAyuda, name='add_ayuda'),
    path('ayuda/insert/', InsertAyuda, name="insert_ayuda"),
    path('ayuda/delete', DeleteAyuda, name='delete_ayuda' ),
    path('ayuda/monto/delete', DeleteAyudaMonto, name='delete_ayuda_monto'),
    path('search_ayuda/', GetPersonasAyuda, name='search_person_ayuda'),
    path('search/ayuda/area', GetPersonaAyuda, name="get_PersonaAyuda"),

    #Servicio Social
    #path('add/sersoc/', SersocCreateView.as_view(), name='sersoc_add'),
    path('add/sersoc/', CreateSersocPerson, name='sersoc_add'),
    path('<int:pk>/edit/sersoc/', CreateSersocPerson, name='sersoc_edit'),
    path('<int:pk>/<int:sersoc>/print/sersoc/', ReportePersonasPDF.as_view(), name='sersoc_print'),
    path('<int:person>/asist/sersoc/', SersocAsistListView.as_view(), name='sersoc_asist'),
    path('sersoc/', SersocListView.as_view(), name='sersoc_list'),

    #Consulta 
    path('consulta/<str:rfc>/', ValidateRFC, name='validate_rfc'),

    #Capacitacion
    
    path('capacitacion/', CapacitacionListView.as_view(), name='capacitacion_list'),
    path('capacitacion/add/', SaveCapacitacion, name='save_capacitacion'),
    path('<int:pk>/edit/', PersonUpdateView.as_view(), name='capacitacion_edit'),
    path('capacitacion/login', loginUsers, name="capacitacion_login"), 
    path('capacitacion/users', Capacitacion.as_view(), name="capacitacion_users"), 
    path('capacitacion/persona', CapacitacionesxPersona.as_view(), name="capacitacion_persona"),

    #Api URL's
    path('api-auth/', include('rest_framework.urls')),
    path('', include(crede_urls)),
    path('registro/', include(registro_urls)),

]   
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
