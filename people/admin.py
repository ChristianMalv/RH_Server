from django.contrib import admin
# Register your models here.
from .models import AreaInterna, AreaOrganigrama, Bajas, ClavePuesto, Compensacion, Compensaciones, Contratacion, Filiacion, Horarios, Incidencia, Person, EntidadFederativa, \
      Nivel, NivelSueldo, Nombramiento, Pais, Puesto, TipoRelacion, TipoVia, Horarios, CausaIncidencia, Compensaciones, MultipleOrganigrama, ServicioSocial, PeriodosVacaciones,\
      Capacitacion

admin.site.register(Nombramiento)
admin.site.register(Nivel)
admin.site.register(AreaInterna)
#admin.site.register(AreaOrganigrama)
admin.site.register(TipoRelacion)
admin.site.register(NivelSueldo)
admin.site.register(Puesto)
admin.site.register(EntidadFederativa)
admin.site.register(Pais)
admin.site.register(TipoVia)
admin.site.register(Contratacion)
admin.site.register(Person)
admin.site.register(Horarios)
admin.site.register(Bajas)
admin.site.register(Filiacion)
admin.site.register(ClavePuesto)
admin.site.register(CausaIncidencia)
admin.site.register(Compensaciones)
admin.site.register(MultipleOrganigrama)
admin.site.register(ServicioSocial)
admin.site.register(PeriodosVacaciones)
admin.site.register(Capacitacion)
@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    list_display = ('matriculaCredencial', 'created_at')
    list_filter = ('matriculaCredencial', 'created_at')
    ordering = ('created_at',)
    search_fields = ('matriculaCredencial',)
    



class OrgqanigramaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'areaInterna')
    list_filter = ('areaInterna', 'nombre')
    ordering = ('areaInterna',)
    search_fields = ('nombre',)
    
    pass

class CompensacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero', 'montoUnitario', 'codigo') 

    pass


# Register the admin class with the associated model
admin.site.register(AreaOrganigrama, OrgqanigramaAdmin)
admin.site.register(Compensacion, CompensacionAdmin )