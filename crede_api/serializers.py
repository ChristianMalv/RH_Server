from rest_framework import serializers
from django.contrib.auth.models import User
from people.models import Person, AreaOrganigrama, AreaInterna
from .models import Visitante
from .models import TipoEquipo, TipoIngreso, Equipo, AsignacionEquipo, EntradaSalidaEquipo

class AreaInternaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaInterna
        fields = ['pk','nombre']

class PersonSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Person
        fields = ["pk","matricula", "nombres", "apellido1", "apellido2", "extension_telefonica"]
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['areaInterna']= AreaInternaSerializer(instance.areaInterna,many=False).data
        return representation

class AreaOrganigramaSerializer(serializers.ModelSerializer):
    #areaInterna = AreaInternaSerializer()
    class Meta:
        model = AreaOrganigrama
        #fields = ["nombre", "areaInterna"]
        fields = ['pk','nombre']

class VisitanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitante
        fields = ['metadatos','ingreso','salida']
        read_only_fields=['salida']


class TipoEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEquipo
        fields = ['id', 'nombre', 'descripcion']

class TipoIngresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoIngreso
        fields = ['id', 'nombre', 'descripcion', 'fecha_compra']

class EquipoSerializer(serializers.ModelSerializer):
    tipo = serializers.PrimaryKeyRelatedField(queryset=TipoEquipo.objects.all())
    ingreso = serializers.PrimaryKeyRelatedField(queryset=TipoIngreso.objects.all())
   
    class Meta:
        model = Equipo
        fields = ['id', 'tipo', 'ingreso', 'nombre', 'observaciones', 'serie', 'marca', 'modelo', 'activo', 'imagen']
        read_only_fields=['activo']
class AsignacionEquipoSerializer(serializers.ModelSerializer):
    equipo = serializers.PrimaryKeyRelatedField(queryset=Equipo.objects.all())
    persona = serializers.PrimaryKeyRelatedField(queryset=Person.objects.all())
    #usuario = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = AsignacionEquipo
        fields = ['id', 'equipo', 'persona', 'fecha_asignacion', 'fecha_retiro', 'observaciones', 'activo']
        read_only_fields=['activo', 'fecha_asignacion', 'fecha_retiro']
class EntradaSalidaEquipoSerializer(serializers.ModelSerializer):
    equipo = EquipoSerializer()
    usuario = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = EntradaSalidaEquipo
        fields = ['id', 'equipo', 'usuario', 'ingreso', 'salida', 'observaciones', 'imagen']

