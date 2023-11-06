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
from django.db.models import Count
@csrf_exempt
def InsertAyuda(request):
    servicio = request.POST.get("servicio").strip() 
    destino = request.POST.get("destino").strip()
    fechaAyuda = datetime.datetime.strptime(request.POST.get("fechaAyuda"), "%d/%m/%Y")
    if 'id' in request.POST:
        id=request.POST.get("id").strip()
        ayudaData = InsertOneAyuda(id, fechaAyuda, servicio, destino)
        return JsonResponse(ayudaData,safe=False)
    else:
        listAyudaData =[]
        persons = json.loads(request.POST.get("personas"))
        print(persons)    
        for person in persons:
            listAyudaData.append(InsertOneAyuda(person.strip(), fechaAyuda, servicio, destino) )
        return JsonResponse(listAyudaData,safe=False)
    

def InsertOneAyuda(id, fechaAyuda, servicio, destino):
    now= datetime.datetime.now()
    try:
        ayuda= Ayudas.objects.get(pk=id)
        ayudaPersona = PersonaAyuda.objects.filter(Q(created_date = fechaAyuda) & Q(ayuda = ayuda))
        if ayuda and ayudaPersona.count()==0:
            ayudaPersona =  PersonaAyuda(ayuda = ayuda, created_date = fechaAyuda, servicio = servicio, destino = destino )
            ayudaPersona.save()
            ayudasMes = PersonaAyuda.objects.filter(Q(ayuda = ayuda) & Q(created_date__month = now.month, created_date__year = now.year)).values('ayuda').annotate(total=Count('ayuda'))
            monto = (ayudasMes[0]['total'])*ayuda.montoXDia
            ayudaData={"id":ayudaPersona.pk,"matricula": ayuda.info_person.matricula, "nombre":ayuda.info_person.nombres +" " +ayuda.info_person.apellido1+ " " + ayuda.info_person.apellido2, "monto":monto,"error":False,"errorMessage":"Ayuda registrada para "+ayuda.info_person.nombres +" " +ayuda.info_person.apellido1+ " " + ayuda.info_person.apellido2}
        else :
            ayudaData={"error":True,"errorMessage":"Ya existe un registro de ayuda para "+ ayuda.info_person.nombres +" " +ayuda.info_person.apellido1+ " " + ayuda.info_person.apellido2 +" el día "+ fechaAyuda.strftime("%d-%m-%Y") }
        return ayudaData
    except  Exception as e:
        raise e
        ayudaData={"error":True,"errorMessage":"Error al querer dar de alta Compensación"}
        return ayudaData
@csrf_exempt
def AddAyuda(request):
    id=request.POST.get("id")
    monto=request.POST.get("monto")
    try:
        person= Person.objects.get(pk=id)
        addAyuda=Ayudas(info_person=person, montoXDia=monto)
        addAyuda.save()
        ayudaData={"id":addAyuda.pk,"matricula": person.matricula, "nombre":person.nombres +" " +person.apellido1+ " " + person.apellido2, "monto":monto,"error":False,"errorMessage":"Ayuda registrada"}
        return JsonResponse(ayudaData,safe=False)
    except  Exception as e:
        raise e
        ayudaData={"error":True,"errorMessage":"Error al querer dar de alta Compensación"}
    return JsonResponse(ayudaData,safe=False)
@csrf_exempt
def GetAyudaPersonas(request):
   
    querysetAyuda = Ayudas.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    querysetPersons = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6)).values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    persons_data = querysetPersons.difference(querysetAyuda)  
     #persons_data= Person.objects.all()  
    t = get_template('people/ayuda/add_ayuda.html')
    content = t.render(
    {
        'people': persons_data, 
       
    })
    return HttpResponse(content)

# class AyudaToShow:  
#     def __init__(self, nombre,  id):
#         self.nombre = nombre
#         self.id = id  
       

@method_decorator(login_required, name='dispatch')
class PersonAyudaListView(ListView):
    model = Ayudas
    def get(self, request, *args, **kwargs):
        queryset =Ayudas.objects.all()
        content = {#t.render(
            'personaayuda': queryset, 
            
        }#)
        return render(request, 'people/ayuda/ayuda_list.html' , content)    

@csrf_exempt
def GetPersonasAyuda(request):
  
    q=request.GET.get("q")
    queryset =Ayudas.objects.all()
    if q and q !=" ":
        q =q.split(" ")
        query = reduce(operator.and_, ((Q(info_person__nombres__unaccent__icontains=item) | Q(info_person__apellido1__unaccent__icontains=item) | Q(info_person__apellido2__unaccent__icontains=item) | Q(info_person__matricula__icontains=item) ) for item in q))
        queryset = queryset.filter(query)    

    t = get_template('people/ayuda/ayuda_search.html')
    content = t.render(
    {
        'personaayuda': queryset, 
       # 'compensacion' : list,
          
    })
    return HttpResponse(content)

@csrf_exempt
def GetPersonaAyuda(request):
    now= datetime.datetime.now()
    id=request.GET.get("id").strip()
    
    ayuda= Ayudas.objects.get(pk=id)
    ayudaPersona = PersonaAyuda.objects.filter(Q(created_date__month = now.month, created_date__year = now.year) & Q(ayuda = ayuda)).order_by('created_date')
    t = get_template('people/ayuda/get_ayuda.html')
    content = t.render(
    {
        'ayudaPersona': ayudaPersona, 
     })
    montomes = ayuda.montoXDia*(ayudaPersona.count())
    ayuda_data={"error":False,"content":content, "persona": ayuda.info_person.nombres + ' ' +ayuda.info_person.apellido1 +' ' +ayuda.info_person.apellido2, "montodia": ayuda.montoXDia,  "montomes": montomes }
    return JsonResponse(ayuda_data,safe=False)
@csrf_exempt
def DeleteAyuda(request):
    id=request.POST.get("id").strip()
    try:
        ayuda= Ayudas.objects.get(pk=id)
        print(ayuda.pk)
        #compensacion = Compensacion.objects.get(pk=comp.compensacion)
        ayuda.delete()
        ayuda_data={"error":False,"errorMessage":"Ayuda eliminada", "ayuda": str(ayuda.pk) }
        return JsonResponse(ayuda_data,safe=False)
    except  Exception as e:
        raise e
        ayuda_data={"error":True,"errorMessage":"Error al querer dar de baja Ayuda"}
        return JsonResponse(ayuda_data,safe=False)

@csrf_exempt
def DeleteAyudaMonto(request):
    now= datetime.datetime.now()
    id=request.POST.get("id").strip()
    try:
        ayudaPersona =  PersonaAyuda.objects.get(pk=id)
        ayudasMes = PersonaAyuda.objects.filter(Q(ayuda = ayudaPersona.ayuda) & Q(created_date__month = now.month, created_date__year = now.year)).values('ayuda').annotate(total=Count('ayuda'))
        monto = ((ayudasMes[0]['total'])-1)*ayudaPersona.ayuda.montoXDia
        ayuda_data={"error":False,"errorMessage":"Ayuda eliminada", "matricula": ayudaPersona.ayuda.info_person.matricula, "monto": monto }
        ayudaPersona.delete()
        return JsonResponse(ayuda_data,safe=False)
    except  Exception as e:
        raise e
        ayuda_data={"error":True,"errorMessage":"Error al querer dar de baja Ayuda"}
        return JsonResponse(ayuda_data,safe=False)

