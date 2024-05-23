from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from people.models import Person, AreaOrganigrama, AreaInterna
from .models import Visitante
from .serializers import PersonSerializer, AreaOrganigramaSerializer, AreaInternaSerializer, VisitanteSerializer
from itertools import groupby
from django.db.models import Q
import datetime
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

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

        #nombre = request.data.get('nombre')
        #primer_apellido = request.data.get('primer_apellido')
        #segundo_apellido = request.data.get('segundo_apellido')
        #precaptura = request.data.get('precaptura')
        # q = Q(metadatos__contains={'tarjeton':tarjeton} ) 

        #    & Q(metadatos__contains={'nombre':nombre}) \
        #    & Q(metadatos__contains={'primer_apellido':primer_apellido}) \
        #    & Q(metadatos__contains={'segundo_apellido':segundo_apellido}) \
        #    & Q(created_at__day=now.day, created_at__month = now.month, created_at__year = now.year)
        visitor = Visitante.objects.filter(metadatos__contains={'tarjeton':tarjeton}).last()
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
        q = Visitante.objects.filter(salida__isnull=True)
        serializer = VisitanteSerializer(q, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    def post(self,request,*args,**kargs):
        tarjeton = request.data.get('tarjeton')
        visitante = Visitante.objects.filter(medadatos__contains={'tarjeton':tarjeton},salida__isnull=True).last()
        if visitante is None:
            return Response("{'error':'Tarjetón ya entregado o sin ingreso'}",status=status.HTTP_400_BAD_REQUEST)
        else:
            visitante.salida = datetime.datime.now()
            visitante.save()
            serializer = VisitanteSerializer(q,many=False)
            return Response(serializer.data,status = status.HTTP_200_OK)






    

