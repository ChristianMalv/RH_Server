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
from django.urls.base import reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.views.generic import View
from people.models import AreaOrganigrama, Compensacion, Compensaciones, Person, Incidencia, Bajas, AreaInterna, CausaIncidencia, PeriodosVacaciones
from people.forms import IncidenciaForm, PersonForm, DirectorioUpdateForm
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import qrcode
import textwrap, operator, base64, json, datetime
from django.db.models import Q
from datetime import timedelta
from functools import reduce
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import math
from django.template.loader import get_template
from django.template import Context
from django.core.files.storage import FileSystemStorage

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
import os 
import errno
from django.db.models import Count
from django.db.models.aggregates import Max
from decimal import Decimal
from django.http import FileResponse, Http404
#import vlc
from pyreportjasper import PyReportJasper
import json 
from .incidenciasView import getDiasEconomicos, getVacaciones

class VacacionesToShow:  
    def __init__(self, pk,  matricula, nombre,  area, eco, vaca1, vaca2, extra):
        self.pk = pk 
        self.matricula= matricula 
        self.nombre = nombre
        self.area = area  
        self.eco = eco  
        self.vaca1 = vaca1
        self.vaca2 = vaca2
        self.extra = extra 
      


@method_decorator(login_required, name='dispatch')
class PersonVacacionesListView(ListView):
    model = Incidencia
    paginate_by = 50
    def get(self, request, *args, **kwargs):
        list = []  
        people = Person.objects.filter( Q(activo=True) & ~Q(cat_contratacion__pk =6) & (Q(cat_contratacion__pk =1) | Q(cat_contratacion__pk =2)| Q(cat_contratacion__pk =3) ))
        periodo1 = PeriodosVacaciones.objects.get(idPeriodo=1).periodo
        periodo2= PeriodosVacaciones.objects.get(idPeriodo=2).periodo
        causas = CausaIncidencia.objects.filter(Q(pk=periodo1.pk) | Q(pk = periodo2.pk) | Q(pk = 6) | Q(pk = 3 ))
       
        for i, person in enumerate(people):
            list.append( VacacionesToShow(person.pk, person.matricula, person.nombres+' '+person.apellido1+' '+person.apellido2, person.areaInterna.nombre, 
                        str(getDiasEconomicos(person)),
                        str(getVacaciones(person, periodo1.pk)), 
                        str(getVacaciones(person, periodo2.pk)), 
                        str(10 - getVacaciones(person, 6)) )) 
                          
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
                'people': list, 
                'periodo1': periodo1, 
                'periodo2': periodo2,
                'causaIncidencia': causas,
            }
        
        return render(request, 'people/vacaciones/vaca_list.html' , content)


@csrf_exempt
def GetPersonasVacacion(request):
    periodo1 = PeriodosVacaciones.objects.get(idPeriodo=1).periodo
    periodo2= PeriodosVacaciones.objects.get(idPeriodo=2).periodo
    q=request.GET.get("q")
    people = Person.objects.filter( Q(activo=True) & (Q(cat_contratacion__pk =1) | Q(cat_contratacion__pk =2) | Q(cat_contratacion__pk =3)) & Q(comision_sindical=False) & ~Q(cat_contratacion__pk =6) )
    if q and q !=" ":
        q =q.split(" ")
        query = reduce(operator.and_, ((Q(nombres__unaccent__icontains=item) | Q(apellido1__unaccent__icontains=item) | Q(apellido2__unaccent__icontains=item) | Q(matricula__icontains=item) ) for item in q))
        people = people.filter(query)    

    list = []  
    for i, person in enumerate(people):
            list.append( VacacionesToShow(person.pk, person.matricula, person.nombres+' '+person.apellido1+' '+person.apellido2, person.areaInterna.nombre, 
                        str(getDiasEconomicos(person)),
                        str(getVacaciones(person, periodo1.pk)), 
                        str(getVacaciones(person, periodo2.pk)), 
                        str(10 - getVacaciones(person, 6)) )) 

    t = get_template('people/vacaciones/vaca_search.html')
    content = t.render(
    {
        'people': list, 
        'periodo1': PeriodosVacaciones.objects.get(idPeriodo=1).nombre, 
        'periodo2': PeriodosVacaciones.objects.get(idPeriodo=2).nombre,
          
    })
    return HttpResponse(content)


@csrf_exempt
def GetDetalleVacacion(request):
    q=request.GET.get("q")