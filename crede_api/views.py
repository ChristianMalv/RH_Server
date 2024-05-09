from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from people.models import Person, AreaOrganigrama, AreaInterna
from .serializers import PersonSerializer, AreaOrganigramaSerializer, AreaInternaSerializer
from itertools import groupby
from django.db.models import Q
class PersonListApiView(APIView):
    # add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]

    # 1. List all
    def get(self, request, *args, **kwargs):
        '''
        List all the todo items for given requested user
        '''
        todos = Person.objects.filter(matricula = request.user.id)
        serializer = PersonSerializer(todos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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