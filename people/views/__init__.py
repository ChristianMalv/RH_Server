
from .credencialesView import ReportePersonasPDF, saveCheckedPerson, PersonListView, PersonCreateView, PersonUpdateView, PersonCheckView, PersonBajaListView, GetPersonas, InsertBaja
from .directorioView import PersonDirectoryUpdateView, DirectoryListView, GetPersonasDirectory
from .incidenciasView import PersonInciListView, ReporteIncidenciasPDF, searchPerson, DetalleIncidencias, UpdateIncidencia, AddIncidencia, DeleteIncidencia, GetPersonasIncidencia, IncidenciaConsulta, ValidatePersonIncidencia, DetailPersonIncidencia, GetIncidenciaTable, \
loginAdmin, AdminConsulta, AdminInciListView, GetAdminIncidencia
from .compensacionesView import InsertComp, GetCompPersonas, PersonCompListView, DeleteComp, json_to_pdf, GetPersonasCompensacion, compensacionesArea,reporteIncidencias
from .areasView import AreasListView