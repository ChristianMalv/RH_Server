from django.db import models
from django.db.models import JSONField
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