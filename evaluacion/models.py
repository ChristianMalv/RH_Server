from django.db import models
from people.models import Person
from django.db.models.deletion import CASCADE

# Create your models here.
class Evaluacion(models.Model):
    clave = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    archivo = models.FileField(upload_to="evaluacion")
    renderizable = models.BooleanField()
    intentos = models.IntegerField()
    aprobatorio = models.DecimalField(max_digits=5, decimal_places=3)
    inicio = models.DateTimeField()
    cierre = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

class EvaluacionPersona(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=CASCADE)
    persona = models.ForeignKey(Person, on_delete=CASCADE)
    intentos = models.IntegerField()
    porcentaje = models.DecimalField(max_digits=5, decimal_places=3)
    archivo = models.FileField(upload_to="evaluacion")
    modified = models.DateField(auto_now=True)

