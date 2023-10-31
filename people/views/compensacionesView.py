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
from people.models import AreaOrganigrama, Compensacion, Compensaciones, Person, Incidencia, Bajas, AreaInterna, CausaIncidencia
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
from .incidenciasView import calculoIncidenciasPersona, revisarFecha
from PyPDF2 import PdfMerger
@csrf_exempt
def InsertComp(request):
    id=request.POST.get("id").strip()
    compensaId = request.POST.get("compen").strip()
    try:
        person=Person.objects.get(pk=id)
        compensacion = Compensacion.objects.get(pk=compensaId)
        comp= Compensaciones.objects.filter(info_person__pk=id)
        if not comp:
            compensaciones = Compensaciones.objects.filter(compensacion=compensacion)
            if len(compensaciones) < compensacion.numero :
                compPersona=Compensaciones(info_person= person, compensacion=compensacion)
                compPersona.save()
                comp_data={"id":compPersona.pk,"matricula": person.matricula, "nombre":person.nombres +" " +person.apellido1+ " " + person.apellido2, "compensacion":compensacion.nombre,"error":False,"errorMessage":"Compensación registrada"}
            else:
                comp_data={"message":True, "error":True,"errorMessage":"Se alcanzo el máximo de registros"}
        
        return JsonResponse(comp_data,safe=False)
    except  Exception as e:
        raise e
        comp_data={"error":True,"errorMessage":"Error al querer dar de alta Compensación"}
        return JsonResponse(comp_data,safe=False)


@csrf_exempt
def GetCompPersonas(request):
   
    querysetComp = Compensaciones.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    querysetPersons = Person.objects.filter(activo=True).values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    persons_data = querysetPersons.difference(querysetComp)  
     #persons_data= Person.objects.all()  
    t = get_template('people/comp/add_compensacion.html')
    content = t.render(
    {
        'people': persons_data, 
       
    })
    return HttpResponse(content)

class CompToShow:  
    def __init__(self, nombre,  id):
        self.nombre = nombre
        self.id = id  
       


@method_decorator(login_required, name='dispatch')
class PersonCompListView(ListView):
    model = Compensaciones
    def get(self, request, *args, **kwargs):
        queryset =Compensaciones.objects.all()
        querysetComp = Compensacion.objects.all()
        list = []  
        for comp in querysetComp:
            consulta=Compensaciones.objects.filter(Q(compensacion = comp))
            list.append(CompToShow(comp.nombre + " (" + str(comp.numero -consulta.count()) +")", comp.pk ))
        content = {#t.render(
            'people': queryset, 
            'compensacion' : list,
        }#)
        return render(request, 'people/comp/comp_list.html' , content)    

@csrf_exempt
def GetPersonasCompensacion(request):
  
    q=request.GET.get("q")
    queryset =Compensaciones.objects.all()
    querysetComp = Compensacion.objects.all()
    if q and q !=" ":
        q =q.split(" ")
        query = reduce(operator.and_, ((Q(info_person__nombres__unaccent__icontains=item) | Q(info_person__apellido1__unaccent__icontains=item) | Q(info_person__apellido2__unaccent__icontains=item) | Q(info_person__matricula__icontains=item) ) for item in q))
        queryset = queryset.filter(query)    

    list = []  
    for comp in querysetComp:
        consulta=Compensaciones.objects.filter(Q(compensacion = comp))
        list.append(CompToShow(comp.nombre + " (" + str(comp.numero -consulta.count()) +")", comp.pk ))    

    t = get_template('people/comp/comp_search.html')
    content = t.render(
    {
        'people': queryset, 
        'compensacion' : list,
          
    })
    return HttpResponse(content)


@csrf_exempt
def DeleteComp(request):
    id=request.POST.get("id").strip()
    try:
        comp= Compensaciones.objects.get(pk=id)
        print(comp.compensacion.pk)
        #compensacion = Compensacion.objects.get(pk=comp.compensacion)
        comp.delete()
        comp_data={"error":False,"errorMessage":"Compensación eliminada", "compensacion": str(comp.compensacion.pk) }
        return JsonResponse(comp_data,safe=False)
    except  Exception as e:
        raise e
        comp_data={"error":True,"errorMessage":"Error al querer dar de baja Compensación"}
        return JsonResponse(comp_data,safe=False)

@csrf_exempt      
def compensacionesArea(request,fechaInicio,fechaFin, folio ):
    dateInicio = datetime.datetime.strptime(fechaInicio, "%d-%m-%Y")
    dateFin = datetime.datetime.strptime(fechaFin, "%d-%m-%Y")
    input_file = settings.MEDIA_ROOT+ '/Formatos/Compensacion_v2.jrxml'
    areas = AreaOrganigrama.objects.all()
    i=0
    for area in areas:
        y=CreateJson(dateInicio, dateFin, area.pk, folio, "Area")
        folio+=y
        if y>0: 
            conn = {
                'driver': 'json',
                'data_file': settings.MEDIA_ROOT+ '/Formatos/dataArea.json',
                'json_query': 'compensacion'
            }
            outputFile= settings.MEDIA_ROOT+ '/Formatos/Compensacion/Area/ReporteCompensacion '+ str(i) +'.pdf' 
            i=i+1 
            pyreportjasper = PyReportJasper()
            pyreportjasper.config(
            input_file,
            output_file=outputFile,
            output_formats=["pdf"],
            db_connection=conn
            )
            pyreportjasper.process_report()
            print('Result is the file below.')
    merger = PdfMerger()
    for x in range(i):
        existing_pdf = settings.MEDIA_ROOT+ '/Formatos/Compensacion/Area/ReporteCompensacion '+ str(x) +'.pdf' 
        outputfinal = settings.MEDIA_ROOT+ '/Formatos/Compensacion/Area/ReporteCompensacionGeneral '+fechaInicio+' al '+fechaFin+'.pdf'
        merger.append(existing_pdf)
    merger.write(outputfinal)
    merger.close()
    if os.path.isfile(outputfinal):
    #    print('Report generated successfully!')
        with open(outputfinal, 'rb') as pdf:
            response = HttpResponse(pdf.read(),content_type='application/pdf')
            response['Content-Disposition'] = 'filename=ReporteCompensacionAreaGeneral '+fechaInicio+' al '+fechaFin+'.pdf'
        return response
        
@csrf_exempt      
def json_to_pdf(request,fechaInicio,fechaFin,folio  ):
    dateInicio = datetime.datetime.strptime(fechaInicio, "%d-%m-%Y")
    dateFin = datetime.datetime.strptime(fechaFin, "%d-%m-%Y")
 
    
    input_file = settings.MEDIA_ROOT+ '/Formatos/Compensacion_v1.jrxml'
    CreateJson(dateInicio, dateFin, None, folio, 'General')
    conn = {
      'driver': 'json',
      'data_file': settings.MEDIA_ROOT+ '/Formatos/dataGeneral.json',
      'json_query': 'compensacion'
   }
    outputFile= settings.MEDIA_ROOT+ '/Formatos/ReporteCompensacion '+fechaInicio+' al '+fechaFin+'.pdf' 
    pyreportjasper = PyReportJasper()
    pyreportjasper.config(
      input_file,
      output_file=outputFile,
      output_formats=["pdf"],
      db_connection=conn
   )
    pyreportjasper.process_report()
    print('Result is the file below.')
   # output_file = output_file + '.pdf'
    if os.path.isfile(outputFile):
    #    print('Report generated successfully!')
        with open(outputFile, 'rb') as pdf:
            response = HttpResponse(pdf.read(),content_type='application/pdf')
            response['Content-Disposition'] = 'filename=ReporteCompensacion.pdf'
        return response


def CreateJson(dateInicio, dateFin, condicion, folio, archivo):
    data = {}
    horas = 0
    total = 0
    data['compensacion']=[]
    if condicion == None:
        compensaciones = Compensaciones.objects.all().order_by('info_person__rfc')
    else:
        compensaciones = Compensaciones.objects.all().filter(Q(info_person__cat_area_org__pk = condicion))
    if compensaciones.count() > 0:
        j=0
        for i, compen in enumerate(compensaciones):
            print(compen.info_person.apellido1 +" "+ compen.info_person.apellido2 +" "+ compen.info_person.nombres)
            horas = calculoIncidenciasPersona(dateInicio, dateFin, compen.info_person)
            horas = math.floor(horas)
            if horas <= 90:
                importe = Decimal(horas) * (compen.compensacion.montoUnitario / 90)
            elif horas == 0:
                importe = 0
            else:
                horas = 90
                importe = compen.compensacion.montoUnitario 
            total += importe
            if horas != 0:
                data['compensacion'].append({'Folio': j+1,
                'NoFolio': folio+j,
                'Area': compen.info_person.cat_area_org.nombre,
                'RFC': compen.info_person.rfc,
                'Nombre':  compen.info_person.apellido1.upper() +" "+ compen.info_person.apellido2.upper() +" "+ compen.info_person.nombres.upper() ,
                'ClaveP':  compen.info_person.clave_presupuestal,
                'Categoria': compen.compensacion.nombre,
                'Codigo': compen.compensacion.codigo,
                'Compensacion': '$ '+ str(compen.compensacion.montoUnitario),
                'CostoHora': str(round(compen.compensacion.montoUnitario / 90, 4) ),
                'HorasXMes': str(horas),
                'Importe': '$ ' +str("{:,}".format(round(importe, 2))),
                'Fecha': str(dateInicio.strftime("%d-%m-%Y")) + ' al ' +str(dateFin.strftime("%d-%m-%Y")), 
                'Total': '$ ' + str("{:,}".format(round( total, 2))), 
                'Logo1': settings.MEDIA_ROOT+ '/Formatos/logo-sep.png', 
                'Logo2':  settings.MEDIA_ROOT+ '/Formatos/logo-aprendemx.png' })
                j+=1
        with open(settings.MEDIA_ROOT+ '/Formatos/data'+archivo+'.json', 'w',  encoding='utf8') as file:
            json.dump(data, file, ensure_ascii=False) 
    return compensaciones.count()

def CreateJsonReport(dateInicio, dateFin, incidencia):
    data = {}
    data['incidencia']=[]
    incidencias = Incidencia.objects.filter(Q(causa_incidencia = incidencia) & Q(created_at__range=[dateInicio, dateFin+ timedelta(1)])).distinct('created_at', 'matriculaCredencial__rfc' )
    for incidencia in incidencias:
        data['incidencia'].append({'Fecha':  "Del día "+ dateInicio.strftime("%d-%m-%Y")+" al "+dateFin.strftime("%d-%m-%Y"),
                'Rfc': incidencia.matriculaCredencial.rfc,
                'Nombre': incidencia.matriculaCredencial.nombres + ' ' + incidencia.matriculaCredencial.apellido1 + ' '+ incidencia.matriculaCredencial.apellido2,
                'Horario': incidencia.matriculaCredencial.cat_horario.nombre,
                'FechaIncidencia': incidencia.created_at.strftime("%d-%m-%Y"),
                'Incidencia': incidencia.causa_incidencia.nombre,
                'Area': incidencia.matriculaCredencial.cat_area_org.nombre,
                'Puesto': incidencia.matriculaCredencial.puesto,
                'Clave': incidencia.matriculaCredencial.clave_presupuestal,
                'Contrato': incidencia.matriculaCredencial.cat_contratacion.nombre,
                'Matricula': incidencia.matriculaCredencial.matricula,
                'Logo1': settings.MEDIA_ROOT+ '/Formatos/logo-sep.png', 
                'Logo2':  settings.MEDIA_ROOT+ '/Formatos/logo-aprendemx.png' })
        with open(settings.MEDIA_ROOT+ '/Formatos/dataReporteIncidencias.json', 'w',  encoding='utf8') as file:
            json.dump(data, file, ensure_ascii=False) 

def CreateJsonReportNoData(dateInicio, dateFin):
    data = {}
    data['incidencia']=[]
    querysetPersons = Person.objects.filter(activo=True)    
    for i in range(int((dateFin - dateInicio).days)+1):
        for persona in querysetPersons:
            print(persona.matricula)
            incidencia = Incidencia.objects.filter(Q(created_at__day=(dateInicio + timedelta(i)).day, created_at__month = (dateInicio + timedelta(i)).month, created_at__year = (dateInicio + timedelta(i)).year) & Q(matriculaCredencial= persona)).values('matriculaCredencial', 'created_at', 'created_at_original', 'causa_incidencia')
            if incidencia.count()==1 and incidencia[0]['causa_incidencia'] == None:
                try:
                   print(incidencia.causa_incidencia)
                except AttributeError:
                 print("Attribute does not exist")
                print(incidencia[0]['created_at'])
                fechaRevisada = revisarFecha(persona.cat_horario.nombre, incidencia[0]['created_at'])
                if fechaRevisada==1:
                    tipoInci="Entrada no Registrada" 
                else:
                    tipoInci="Salida no Registrada"
                data['incidencia'].append(dataToAppend(dateInicio, dateFin, persona, tipoInci,  incidencia[0]['created_at'].strftime("%d-%m-%Y")  ) )
                with open(settings.MEDIA_ROOT+ '/Formatos/dataReporteSinRegistros.json', 'w',  encoding='utf8') as file:
                    json.dump(data, file, ensure_ascii=False) 
            elif (incidencia.count()==0) and (((persona.horario_finde) and (dateInicio + timedelta(i)).weekday() >= 5) or ((dateInicio + timedelta(i)).weekday() < 5)):
                data['incidencia'].append(dataToAppend(dateInicio, dateFin, persona, "Entrada no registrada",  (dateInicio + timedelta(i)).strftime("%d-%m-%Y") ))
                data['incidencia'].append(dataToAppend(dateInicio, dateFin, persona, "Salida no registrada",  (dateInicio + timedelta(i)).strftime("%d-%m-%Y") ))
                with open(settings.MEDIA_ROOT+ '/Formatos/dataReporteSinRegistros.json', 'w',  encoding='utf8') as file:
                    json.dump(data, file, ensure_ascii=False) 

def dataToAppend(dateInicio, dateFin, persona, incidencia, fecha  ):
    return {'Fecha':  "Del día "+ dateInicio.strftime("%d-%m-%Y")+" al "+dateFin.strftime("%d-%m-%Y"),
                'Rfc': persona.rfc,
                'Nombre': persona.nombres + ' ' + persona.apellido1 + ' '+ persona.apellido2,
                'Horario': persona.cat_horario.nombre,
                'FechaIncidencia':fecha,
                'Incidencia': incidencia,
                'Area': persona.cat_area_org.nombre,
                'Puesto': persona.puesto,
                'Clave': persona.clave_presupuestal,
                'Contrato': persona.cat_contratacion.nombre,
                'Matricula': persona.matricula,
                'Logo1': settings.MEDIA_ROOT+ '/Formatos/logo-sep.png', 
                'Logo2':  settings.MEDIA_ROOT+ '/Formatos/logo-aprendemx.png' }
             

@csrf_exempt      
def reporteIncidencias(request,fechaInicio,fechaFin, incidencia  ):
    dateInicio = datetime.datetime.strptime(fechaInicio, "%d-%m-%Y")
    dateFin = datetime.datetime.strptime(fechaFin, "%d-%m-%Y") 
    if incidencia > 0:
        tipoIncidencia= CausaIncidencia.objects.get(pk=incidencia)
        incidencia = tipoIncidencia.nombre
        CreateJsonReport(dateInicio, dateFin,incidencia)
        dataFile= '/Formatos/dataReporteIncidencias.json'
        outputFile= settings.MEDIA_ROOT+ '/Formatos/ReporteIncidencias'+ incidencia +' '+fechaInicio+' al '+fechaFin+'.xls' 
    else:
        CreateJsonReportNoData(dateInicio, dateFin)
        outputFile= settings.MEDIA_ROOT+ '/Formatos/ReporteIncidenciasSinRegistroEntradaSalida'+fechaInicio+' al '+fechaFin+'.xls' 
        dataFile = '/Formatos/dataReporteSinRegistros.json'
        incidencia = 'Entrada y Salida sin Registro'
    input_file = settings.MEDIA_ROOT+ '/Formatos/ReporteIncidencias_v1.jrxml'
    conn = {
      'driver': 'json',
      'data_file': settings.MEDIA_ROOT+ dataFile,
      'json_query': 'incidencia'
   }
    #outputFile= settings.MEDIA_ROOT+ '/Formatos/ReporteIncidencias'+ str(incidencia) +' '+fechaInicio+' al '+fechaFin+'.pdf' 
   
    pyreportjasper = PyReportJasper()
    pyreportjasper.config(
      input_file,
      output_file=outputFile,
      output_formats=["pdf", "xls"],
      db_connection=conn
   )
    pyreportjasper.process_report()
    print('Result is the file below.')
   # output_file = output_file + '.pdf'
    # Set the content disposition as attachment and provide the filename
    
    if os.path.isfile(outputFile):
        with open(outputFile, 'rb') as pdf:
            #response = HttpResponse(pdf.read(),content_type='application/pdf')
            response = HttpResponse(pdf.read(),  content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename='+ incidencia +' '+fechaInicio+' al '+fechaFin+'.xls'
            return response