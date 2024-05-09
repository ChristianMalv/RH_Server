from rest_framework import serializers
from people.models import Person, AreaOrganigrama, AreaInterna
class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["matricula", "nombres", "apellido1", "apellido2", "areaInterna", "cat_area_org"]

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
