from rest_framework import serializers
from people.models import Person, AreaOrganigrama, AreaInterna
from .models import Visitante
class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["matricula", "nombres", "apellido1", "apellido2", "extension_telefonica"]

class AreaInternaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaInterna
        fields = ['pk','nombre']
class AreaOrganigramaSerializer(serializers.ModelSerializer):
    #areaInterna = AreaInternaSerializer()
    class Meta:
        model = AreaOrganigrama
        #fields = ["nombre", "areaInterna"]
        fields = ['pk','nombre']

class VisitanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitante
        fields = ['metadatos','ingreso']