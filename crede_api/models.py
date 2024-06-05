from django.db import models
from django.db.models import JSONField
from people.models import Person
from django.contrib.auth import get_user_model
# Create your models here.
#Un modelo visitante con id, metadatos tipo json, timestamp de ingreso timestamp de salida,  clave del tarjetón en texto 
class Visitante(models.Model):
    id = models.BigAutoField(primary_key=True, auto_created=True)
    metadatos = JSONField()
    ingreso = models.DateTimeField()
    salida = models.DateTimeField(null=True)
    clave = models.CharField(max_length=200, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usuario = models.CharField(max_length=128,null=True)




class TipoEquipo(models.Model):
    nombre = models.CharField(max_length=150, default='-')
    descripcion = models.CharField(max_length=150, default='-')
    def __str__(self):
        return self.nombre


class TipoIngreso(models.Model):
    nombre = models.CharField(max_length=150, default='-')
    descripcion = models.CharField(max_length=150, default='-')
    fecha_compra = models.DateTimeField(null=True)
    def __str__(self):
        return self.nombre
class Equipo(models.Model):
    tipo = models.ForeignKey(TipoEquipo, null=True, on_delete=models.DO_NOTHING)
    ingreso = models.ForeignKey(TipoIngreso, null=True, on_delete=models.DO_NOTHING)
    nombre = models.CharField(max_length=150, default='-')
    observaciones = models.CharField(max_length=150, default='-')
    serie = models.CharField(max_length=150, default='-')
    marca = models.CharField(max_length=150, default='-')
    modelo = models.CharField(max_length=150, default='-')
    activo = models.BooleanField(default=True)
    fecha_baja = models.DateTimeField(null=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(null=True,upload_to='equipos/%Y/%m/%d')
    usuario = models.CharField(max_length=128,null=True)
    def __str__(self):
        return self.nombre
class AsignacionEquipo(models.Model):
    equipo = models.ForeignKey(Equipo, null=True, on_delete=models.DO_NOTHING)
    persona = models.ForeignKey(Person, null=True, on_delete=models.DO_NOTHING)
    usuario = models.ForeignKey(get_user_model(), null=True, on_delete=models.DO_NOTHING)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_retiro = models.DateTimeField(null=True)
    observaciones = models.CharField(max_length=150, default='-')
    activo = models.BooleanField(default=True)
    usuario = models.CharField(max_length=128,null=True)
    def __str__(self):
        return "%s - %s"%(self.equipo,self.persona)
class EntradaSalidaEquipo(models.Model):
    equipo = models.ForeignKey(Equipo, null=True, on_delete=models.DO_NOTHING)
    usuario = models.ForeignKey(get_user_model(), null=True, on_delete=models.DO_NOTHING)
    ingreso = models.DateTimeField(auto_now_add=True)
    salida = models.DateTimeField(null=True)
    observaciones = models.CharField(max_length=150, default='-')
    imagen = models.ImageField(null=True,upload_to='ingreso_equipos/%Y/%m/%d')
    def __str__(self):
        return "%s - %s"%(self.equipo,self.ingreso)




