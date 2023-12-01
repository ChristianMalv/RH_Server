from distutils.command.upload import upload
from xml.parsers.expat import model
from django.db import models
from django.utils import timezone
from smart_selects.db_fields import ChainedForeignKey 
from multi_email_field.fields import MultiEmailField
# Create your models here.
import os


class Catalogo(models.Model):
    class Meta:
        abstract = True
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    nombre = models.CharField(max_length=255)
    def __str__(self):
        return self.nombre

class Credencial(models.Model):
   
    nombre = models.CharField(max_length=200)
    codigoQr = models.IntegerField
    matricula = models.CharField(max_length=200)
    areaPpal = models.CharField(max_length=200)
    areaSecon = models.CharField(max_length=200)
    matricula = models.TextField()
    created_date = models.DateTimeField(
            default=timezone.now)
    printed_date = models.DateTimeField(
            blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title


class Contratacion(Catalogo):
    class Meta:
        verbose_name = "Contratación"
        verbose_name_plural = "Contrataciones"
    def __str__(self):
        return str(self.pk) +"_"+ self.nombre 
    pass
class Nombramiento(Catalogo):
    class Meta:
        verbose_name = "Nombramiento"
        verbose_name_plural = "Nombramientos"
    pass
class Nivel(Catalogo):
    class Meta:
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"
    pass
class AreaInterna(Catalogo):
    class Meta:
        verbose_name = "Área Interna"
        verbose_name_plural = "Areas Internas"
    pass
class AreaOrganigrama(Catalogo):
    areaInterna = models.ForeignKey(AreaInterna, on_delete=models.DO_NOTHING, related_name="AreaInterna")
    class Meta:
        verbose_name = "Área Organigrama"
        verbose_name_plural = "Areas Organigrama"
    


    pass
class TipoRelacion(Catalogo):
    class Meta:
        verbose_name = "Tipo de Relación"
        verbose_name_plural = "Tipo de Relaciones"
    pass
class NivelSueldo(Catalogo):
    class Meta:
        verbose_name = "Nivel Sueldo"
        verbose_name_plural = "Niveles de Sueldos"
    pass
class Puesto(Catalogo):
    class Meta:
        verbose_name = "Puesto"
        verbose_name_plural = "Puestos"
    pass
class EntidadFederativa(Catalogo):
    class Meta:
        verbose_name = "Entidad Federativa"
        verbose_name_plural = "Countries"
    pass
class Pais(Catalogo):
    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Paises"
    pass
class TipoVia(Catalogo):
    class Meta:
        verbose_name = "Tipo de Vía"
        verbose_name_plural = "Tipo de Vías"
    pass
class Horarios(Catalogo):
    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
    pass

class ClavePuesto(Catalogo):
    class Meta:
        verbose_name = "Clave de Puesto"
        verbose_name_plural = "Claves de Puesto"
    pass

class Compensacion(Catalogo):
    numero = models.IntegerField(null=False, blank=False, verbose_name="Cantidad")
    montoUnitario =  models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False, verbose_name="Monto Unitario")
    codigo = models.CharField(max_length=255, blank=True, verbose_name="Código")
    class Meta:
        verbose_name = "Actividad Compensación"
        verbose_name_plural = "Actividades de Compensación"
    pass 
class Filiacion(Catalogo):
    clavepuesto = models.ForeignKey(ClavePuesto, on_delete=models.DO_NOTHING, null=False, blank=False, verbose_name="Clave de Puesto")
    filiacion = models.CharField(max_length=255, blank=True, verbose_name="Filiación") 
    activo = models.BooleanField(blank=True, null=True, default=True)
    class Meta:
        verbose_name = "Filiación"
        verbose_name_plural = "Filiaciones"
    pass



class Person(models.Model):
    matricula = models.CharField(max_length=255, blank=True, verbose_name="Mátricula")
    nombres = models.CharField(max_length=255, blank=False, verbose_name="Nombre")
    apellido1 = models.CharField(max_length=255, blank=False, verbose_name="Apellido Paterno")
    apellido2 = models.CharField(max_length=255, blank=False, verbose_name="Apellido Materno")
    cat_contratacion = models.ForeignKey(Contratacion, on_delete=models.DO_NOTHING, null=False, blank=False, verbose_name="Contratación")
    areaInterna = models.ForeignKey(AreaInterna, on_delete=models.DO_NOTHING, null=True, blank=False, verbose_name="Área Interna")
    cat_area_org = ChainedForeignKey( AreaOrganigrama,  chained_field="areaInterna",   chained_model_field="areaInterna",   show_all=False,     auto_choose=True,  sort=True, null= True, verbose_name="Área Organigrama")

    puesto = models.CharField(max_length=255, blank=False, verbose_name="Puesto")
    curp = models.CharField(max_length=255, blank=False, verbose_name="CURP")
    rfc = models.CharField(max_length=255, blank=False, verbose_name="RFC")
    fecha_ingreso = models.DateField(null=False, blank=False, verbose_name="Fecha Ingreso")
    municipio = models.CharField(max_length=255, blank=False, verbose_name="Municipio")
    cp = models.CharField(max_length=255, blank=False, verbose_name="Código Postal")
    colonia = models.CharField(max_length=255, blank=False, verbose_name="Colonia")
    nombre_via = models.CharField(max_length=255, blank=False, verbose_name="Calle")
    num_exterior = models.CharField(max_length=255, blank=False, verbose_name="Número Ext.")
    num_interior = models.CharField(max_length=255, blank=False, verbose_name="Número Int.")
    cat_entidades_federativas = models.ForeignKey(EntidadFederativa, on_delete=models.DO_NOTHING, null=False, blank=False, verbose_name="Estado")
    cat_nombramiento = models.ForeignKey(Nombramiento, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="Tipo de Nombramiento")
    cat_tipo_via = models.ForeignKey(TipoVia, on_delete=models.DO_NOTHING, null=False, blank=False, verbose_name="Tipo de vía")
    email_personal = models.CharField(max_length=255, blank=False, verbose_name="Correo electrónico")
    email_institucional = MultiEmailField(blank= True, verbose_name="Correo(s) institucional")
    extension_telefonica = models.CharField(max_length=255, blank=True, verbose_name="Extensión telefónica")
    telefono1 = models.CharField(max_length=14, blank=False, verbose_name="Teléfono de Contacto 1")
    telefono2= models.CharField(max_length=14, blank=False, verbose_name="Teléfono de Contacto 2")
    emergencia_contacto = models.CharField(max_length=255, blank=False, verbose_name="A quien llamar en caso de emergencia")
    emergencia_telefono = models.CharField(max_length=14, blank=False, verbose_name="Teléfono Emergencia")
    emergencia_cat_relacion = models.ForeignKey(TipoRelacion, on_delete=models.DO_NOTHING, null=False, blank=False, verbose_name="Parentesco o relación")
    imagen = models.ImageField(upload_to='persona/%Y/%m/%d', null=True, blank=True)
    imagen_base64 = models.TextField(blank=True,null=True)
    activo= models.BooleanField(blank=True, null=True, default=True)
    vacaciones_extra = models.BooleanField(blank=True, null=True, default=False,  verbose_name="Vacaciones extraordinarias")
    date_update_vacaciones =  models.DateTimeField(null=True, blank=True)
    horario_finde = models.BooleanField(blank=True, null=True, default=False, verbose_name="Horario Fin de Semana")
    clave_presupuestal = models.CharField(max_length=255, blank=True, verbose_name="Clave Presupuestal")
    comision_sindical = models.BooleanField(blank=True, null=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cat_horario = models.ForeignKey(Horarios, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="Horario")
    cat_filiacion = models.ForeignKey(Filiacion, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="Filiación")
    def __str__(self) -> str:
        return "%s - %s %s %s " %(self.matricula, self.apellido1, self.apellido2, self.nombres)
    
    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        permissions = (("datos_personales", "Puede ver datos personales"),   ("tomar_fotografia", "Puede tomar fotografía"),   ("imprimir_credencial", "Puede imprimir credencial"), ("dar_baja", "Puede dar de baja"), ("modificar_directorio", "Puede modificar directorio"), ("ver_vacaciones", "Puede modificar vacaciones"), )   
       
class Bajas(models.Model):
    info_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
         return "%s - %s %s %s " %(self.info_person.matricula, self.info_person.apellido1, self.info_person.apellido2, self.info_person.nombres)
    class Meta:
        verbose_name = "Baja"
        verbose_name_plural = "Bajas"

class Compensaciones(models.Model):
    info_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    compensacion = models.ForeignKey(Compensacion, on_delete=models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
         return "%s - %s %s %s " %(self.info_person.matricula, self.info_person.apellido1, self.info_person.apellido2, self.info_person.nombres)
    class Meta:
        verbose_name = "Compensacion"
        verbose_name_plural = "Compensaciones"
        permissions = (("asignar_comp", "Puede asignar compensaciones"), )

class CausaIncidencia(Catalogo):
    class Meta:
        verbose_name = "Causa Incidencia"
        verbose_name_plural = "Causas Incidencias"
    pass
class Incidencia(models.Model):
    matriculaCredencial = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="Credencial")
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    imagen = models.ImageField(upload_to="Incidencias//%Y/%m/%d",null=True)
    created_at_original= models.DateTimeField(auto_now_add=True)
    modificacion= models.BooleanField(blank=True, null=True, default=False)
    causa_incidencia =  models.ForeignKey(CausaIncidencia, on_delete=models.DO_NOTHING, related_name="Credencial", null=True, blank=True)
    def __str__(self):
        return "%s - %s %s %s " %(self.created_at.strftime("%H:%M:%S"), self.matriculaCredencial.apellido1, self.matriculaCredencial.apellido2, self.matriculaCredencial.nombres)
    class Meta:
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"
        permissions = (("ver_incidencias", "Puede ver Incidencias"),  )   
       

class InfoPersonalAdd(models.Model):
    info_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    cat_nivel = models.ForeignKey(Nivel, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="Nivel")
    cat_nombramiento = models.ForeignKey(Nombramiento, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="Tipo de Nombramiento")
    cat_sueldo = models.ForeignKey(NivelSueldo, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="Nivel de Sueldo")  
    sueldo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Sueldo")
    despensa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Ayuda de Despensa (38)")
    prevision = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Previsión Social Múltiple (44)")
    servicios = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Ayuda por Servicios (46)")
    compensacion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Compensación Garantizada (06)")
    sueldo_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Sueldo Total")
    sueldo_neto_nivel = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Sueldo Neto Nivel")
    sueldo_neto_trab = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Sueldo Neto Trabajador")

class Ayudas(models.Model):
    info_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    created_by = models.CharField(max_length=255, blank=False, verbose_name="User")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    montoXDia =  models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False, verbose_name="Monto Unitario")
    def __str__(self):
         return "%s - %s %s %s " %(self.info_person.matricula, self.info_person.apellido1, self.info_person.apellido2, self.info_person.nombres)
    class Meta:
        verbose_name = "Ayuda"
        verbose_name_plural = "Ayudas"


class PersonaAyuda(models.Model):
    ayuda = models.ForeignKey(Ayudas,  on_delete=models.CASCADE)
    created_date = models.DateTimeField(blank=True)
    servicio = models.CharField(max_length=255, blank=False, verbose_name="Servicio")
    destino = models.CharField(max_length=255, blank=False, verbose_name="Destino")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
         return "%s - %s %s %s " %(self.info_person.matricula, self.info_person.apellido1, self.info_person.apellido2, self.info_person.nombres)
    class Meta:
        verbose_name = "Persona con acceso a Ayuda"
        verbose_name_plural = "Personas con Ayudas"
        permissions = (("asignar_ayudas", "Puede asignar ayudas"), )


class MultipleOrganigrama(models.Model):
    info_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    areasInternas = models.ForeignKey(AreaInterna, on_delete=models.DO_NOTHING, related_name="multiples_areas")


class Salidas(models.Model):
    personas = models.ForeignKey(PersonaAyuda, on_delete=models.DO_NOTHING)
   
class ServicioSocial(models.Model):
    info_person = models.ForeignKey(Person, on_delete=models.CASCADE)
    tipo_sangre = models.CharField(max_length=14, blank=False, verbose_name="Tipo de Sangre")
    escuela_procedencia = models.CharField(max_length=255, blank=False, verbose_name="Escuela de Procedencia")
    escuela_domicilio = models.CharField(max_length=255, blank=False, verbose_name="Domicilio de la Escuela")
    carrera = models.CharField(max_length=255, blank=False, verbose_name="Carrera o Especialidad")
    creditos_cursados = models.CharField(max_length=20, blank=False, verbose_name="Total de Créditos Cursados")
    numero_matricula = models.CharField(max_length=20, blank=False, verbose_name="Número de Matrícula")
    telefono_escuela = models.CharField(max_length=14, blank=False, verbose_name="Teléfono de la Escuela")
    periodo = models.CharField(max_length=255, blank=False, verbose_name="Periodo en el que se realizará el Servicio")
    horario = models.CharField(max_length=255, blank=False, verbose_name="Horario de desempeño de las actividades")
    description = models.TextField(max_length=250, blank=True, verbose_name="Actividades")
    class Meta:
        verbose_name = "Servicio social"
        verbose_name_plural = "Servicios sociales"
        permissions = (("servicio_social", "Puede ver, crear y editar servicios sociales"), )


