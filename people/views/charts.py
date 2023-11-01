from base64 import b64decode
import time
from platform import python_version
from tokenize import String
from typing import Reversible
from django.http.response import HttpResponse, JsonResponse
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from people.models import AreaOrganigrama, Compensacion, Compensaciones, Person, Incidencia, Bajas, AreaInterna, CausaIncidencia, PersonaAyuda, Ayudas
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
import  operator
from django.db.models import Q
from functools import reduce
import textwrap, operator, base64, json, datetime
from json import dumps
from django.db.models import Count
from django.core import serializers

class ChartToShow():  
    def __init__(self, area,  personIn, personOut):
        self.area = area
        self.personIn = personIn  
        self.personOut = personOut  
    def to_dict(self):
      return {"area": self.area, "personIn": self.personIn, "personOut": self.personOut} 

@method_decorator(login_required, name='dispatch')
class DashboardCheck(ListView):
    def get(self, request, *args, **kwargs):
        now = datetime.datetime.now()
        #queryset =AreaInterna.objects.all()
        #incidencias = Incidencia.objects.all().filter(created_at__day=now.day, created_at__month = now.month, created_at__year = now.year).distinct('matriculaCredencial')
        #querysetIncidencias = incidencias.values('matriculaCredencial__areaInterna').annotate(total=Count('matriculaCredencial__areaInterna'))
        listName, listCheck, listPerson, totalCheck, totalNoCheck = getDataDashboard(now)
        content = {#t.render(
            'listName':   dumps(listName, ensure_ascii= False), 
            'listChecked' : dumps( listCheck), 
            'listPerson' : dumps( listPerson), 
            'totalCheck' : dumps(totalCheck),
            'totalNoCheck' : dumps(totalNoCheck),
            'fecha': dumps(now.strftime("%d/%m/%Y")),
        }#)
        return render(request, 'people/inci/administradores/panel_personal.html' , content) 

def getDataDashboard(now):
    querysetPersonas = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6) ).values('areaInterna').annotate(total=Count('areaInterna'))
    listName = []  
    listCheck = [] 
    listPerson =[]
    totalCheck = 0
    totalNoCheck = 0
    for persona in querysetPersonas:
        incidencias = Incidencia.objects.all().filter(Q(created_at__day=now.day, created_at__month = now.month, created_at__year = now.year) & Q(matriculaCredencial__areaInterna__pk = persona['areaInterna']) & Q(causa_incidencia = None) ).distinct('matriculaCredencial')
        #incidencia = Incidencia.objects.filter(Q(created_at__day=now.day, created_at__month = now.month, created_at__year = now.year) & Q(matriculaCredencial__areaInterna__pk = persona['areaInterna']) ).values('matriculaCredencial__areaInterna', 'matricula').distinct('matriculaCredencial').annotate(total=Count('matriculaCredencial__areaInterna'))
        
        area = AreaInterna.objects.get(pk =persona['areaInterna'] )
        listName.append(area.nombre)
        listCheck.append(incidencias.count())
        listPerson.append( (int(persona['total'])-(incidencias.count())) *-1 )
        totalCheck += incidencias.count() 
        totalNoCheck += int(persona['total'])
    totalNoCheck = totalNoCheck - totalCheck
    return listName, listCheck, listPerson, totalCheck, totalNoCheck
@csrf_exempt
def UpdateDashboard(request):
    try:
        fecha = request.GET.get("fecha")
        listName, listCheck, listPerson, totalCheck, totalNoCheck = getDataDashboard(datetime.datetime.strptime(fecha, "%d/%m/%Y"))
        dashboard_data={"error":False, "listName":listName , "listCheck":listCheck , "listPerson":listPerson , "totalCheck":totalCheck , "totalNoCheck":totalNoCheck }
        return JsonResponse(dashboard_data,safe=False)
    except Exception as e:
        print(e)
        dashboard_data={"error":True,"errorMessage":"Failed to Update Chart"}
        return JsonResponse(dashboard_data,safe=False)