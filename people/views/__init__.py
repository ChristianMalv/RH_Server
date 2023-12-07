
from .credencialesView import ReportePersonasPDF, saveCheckedPerson, PersonListView, PersonCreateView, PersonUpdateView, PersonCheckView, PersonBajaListView, GetPersonas, InsertBaja
from .directorioView import PersonDirectoryUpdateView, DirectoryListView, GetPersonasDirectory
from .incidenciasView import PersonInciListView, ReporteIncidenciasPDF, searchPerson, DetalleIncidencias, UpdateIncidencia, AddIncidencia, DeleteIncidencia, GetPersonasIncidencia, IncidenciaConsulta, ValidatePersonIncidencia, DetailPersonIncidencia, GetIncidenciaTable, \
loginAdmin, AdminConsulta, AdminInciListView, GetAdminIncidencia
from .compensacionesView import InsertComp, GetCompPersonas, PersonCompListView, DeleteComp, json_to_pdf, GetPersonasCompensacion, compensacionesArea,reporteIncidencias
from .areasView import AreasListView
from .ayudasView import PersonAyudaListView, GetAyudaPersonas, InsertAyuda, DeleteAyuda, GetPersonasAyuda, GetPersonaAyuda, AddAyuda, DeleteAyudaMonto
from .charts import DashboardCheck, UpdateDashboard
from .sersoc import  SersocListView, SersocCreateView, CreateSersocPerson
from .consulta import ValidateRFC
from .vacaciones import PersonVacacionesListView, GetPersonasVacacion, GetDetalleVacacion