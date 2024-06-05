from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from people.models import Person, AreaOrganigrama, AreaInterna
from .models import Visitante,TipoEquipo, TipoIngreso, Equipo, AsignacionEquipo, EntradaSalidaEquipo
from .serializers import PersonSerializer, AreaOrganigramaSerializer, AreaInternaSerializer, VisitanteSerializer
from .serializers import  TipoEquipoSerializer, TipoIngresoSerializer, EquipoSerializer, AsignacionEquipoSerializer, EntradaSalidaEquipoSerializer
from itertools import groupby
from django.db.models import Q
import datetime
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from people.views.ldapView import get_attributes 



class PersonApiViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = PersonSerializer
    queryset = Person.objects.all()

    def get_queryset(self):
        q = self.request.query_params.get("q", "").split(" ")
        qs = Person.objects.filter(activo=True)
        for t in q:
            qs = qs.filter( Q(nombres__icontains=t)|Q(apellido1__icontains=t)|Q(apellido2__icontains=t)|Q(extension_telefonica=t))

        return qs
        



class PersonListApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        areas = AreaInterna.objects.all()
        serialized_areas = []
        serializer = []
        for area in areas:
            personal = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6) & Q(areaInterna_id = area.pk))
            serializer = PersonSerializer(personal, many=True)
            serialized_area = {
            'direccion': AreaInternaSerializer(area).data,
            'personas': serializer.data
            }
            serialized_areas.append(serialized_area)
        print(serialized_areas)
        return Response(serialized_areas, status=status.HTTP_200_OK)

    # 2. Create
    def post(self, request, *args, **kwargs):
        '''
        Create the Todo with given todo data
        '''
        data = {
            'task': request.data.get('task'), 
            'completed': request.data.get('completed'), 
            'user': request.user.id
        }
        serializer = PersonSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AreaListApiView(APIView):
    permission_classes = (AllowAny,)
    # 1. List all
    def get(self, request, *args, **kwargs):
        areas = AreaInterna.objects.all()
        serialized_areas = []
        serializer = []
        for area in areas:
            area_organigramas = AreaOrganigrama.objects.filter(areaInterna_id = area.pk)
            serializer = AreaOrganigramaSerializer(area_organigramas, many=True)
            serialized_area = {
            'direccion': AreaInternaSerializer(area).data,
            'areas': serializer.data
            }
            serialized_areas.append(serialized_area)
        print(serialized_areas)
        return Response(serialized_areas, status=status.HTTP_200_OK)

    # 2. Create
    def post(self, request, *args, **kwargs):
        '''
        Create the Todo with given todo data
        '''
        visitor = None
        now = datetime.datetime.now()
        tarjeton = request.data.get('tarjeton')
        precaptura = request.data.get('precaptura',False)

        if  precaptura:
            now = None

        visitor = Visitante.objects.filter(metadatos__contains={'tarjeton':tarjeton},salida__isnull=True).last()
        data = {}

        for key in request.data.keys():
            data[key] = request.data.get(key)        
        if visitor is None:
             data = {
                 'metadatos': request.data,
                 'ingreso': now ,
             }
             serializer = VisitanteSerializer(data=data)
             if serializer.is_valid():
                 serializer.save()
                 return Response(serializer.data, status=status.HTTP_201_CREATED)
             else:
                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        else:

            return Response({'error':'Ingreso de tarjetón ya registrado'},status=status.HTTP_400_BAD_REQUEST)

class SalidaApiView(APIView):
    permission_classes = (AllowAny,)
    def get(self,request,*args,**kargs):

        inicio = request.query_params.get("inicio", None)
        fin = request.query_params.get("fin", None)
        print(inicio)

        if fin is not None:
            inicio = datetime.strptime(inicio, '%Y-%m-%d').replace(hour=23,minute=59,second=59)
            fin = datetime.strptime(fin, '%Y-%m-%d').replace(hour=0,minute=0,second=0)
            q = Visitante.objects.filter(salida__gt=inicio,salida__lt=fin )
        else:
            q = Visitante.objects.filter(salida__isnull=True)
        serializer = VisitanteSerializer(q, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self,request,*args,**kargs):
        tarjeton = request.data.get('tarjeton')
        visitante = Visitante.objects.filter(metadatos__contains={'tarjeton':tarjeton},salida__isnull=True).last()
        if visitante is None:
            return Response({'error':'Tarjetón ya retirado o sin ingreso'},status=status.HTTP_400_BAD_REQUEST)
        else:
            visitante.salida = datetime.datetime.now()
            visitante.save()
            serializer = VisitanteSerializer(visitante,many=False)
            return Response(serializer.data,status = status.HTTP_200_OK)




class TipoEquipoViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = TipoEquipo.objects.all()
    serializer_class = TipoEquipoSerializer

class TipoIngresoViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = TipoIngreso.objects.all()
    serializer_class = TipoIngresoSerializer

class EquipoViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = Equipo.objects.all()
    serializer_class = EquipoSerializer

class AsignacionEquipoViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = AsignacionEquipo.objects.all()
    serializer_class = AsignacionEquipoSerializer

class EntradaSalidaEquipoViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = EntradaSalidaEquipo.objects.all()
    serializer_class = EntradaSalidaEquipoSerializer



class LDAPDjangoAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
       
        result = get_attributes(username,password)
        if result['error']:
            return Response({'error':'Usuario y/o contraseña incorrecto'},status.HTTP_404_NOT_FOUND)
        user = User.objects.filter(username=username).last()
        if user is None:
           user = User.objects.create_user(username,username+"@credenciale.aprende.gob.mx",password)
           user.name = result["nombre"]
           user.lasname=result["apellidos"]
           user.save()
        else:
           user.set_password(password)
           user.save()

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username':user.username
        })

    

