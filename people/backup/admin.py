from django.contrib import admin
# Register your models here.
from .models import AreaInterna, AreaOrganigrama, Bajas, ClavePuesto, Contratacion, Filiacion, Horarios, Incidencia, Person, EntidadFederativa,  Nivel, NivelSueldo, Nombramiento, Pais, Puesto, TipoRelacion, TipoVia, Horarios, CausaIncidencia

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



# Register the admin class with the associated model
admin.site.register(AreaOrganigrama, OrgqanigramaAdmin)