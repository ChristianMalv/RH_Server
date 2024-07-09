from base64 import b64decode
import time
from typing import Reversible
from django.http.response import HttpResponse, JsonResponse
from io import BytesIO
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.urls.base import reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.views.generic import View
from people.models import  Person, ServicioSocial,Contratacion, Incidencia, DocumentosSS
from people.forms import  PersonForm, ServicioSocialForm, ServicioSocialInlineFormset
from .sharepoint import GetDirectoryInfo
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import timedelta
from functools import reduce
import textwrap, operator, base64, json, datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.db.models import Max, Min
from .sharepoint import UploadFile, DownloadFiles
@method_decorator(login_required, name='dispatch')
class SersocListView(ListView):
    model = ServicioSocial
    context_object_name = 'people'
    #querysetBajas = Bajas.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    #querysetPersons = Person.objects.all().values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    #queryset = querysetPersons.difference(querysetBajas)  
    queryset = ServicioSocial.objects.filter(info_person__activo=True).order_by('info_person__created_at')
    paginate_by = 50

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        q = self.request.GET.get('q')
        if q:
            q =q.split(" ")
            query = reduce(operator.and_, ((Q(info_person__nombres__unaccent__icontains=item) | Q(info_person__apellido1__unaccent__icontains=item) | Q(info_person__apellido2__unaccent__icontains=item)  ) for item in q))
            return qs.filter(query)
        return qs 


def CreateSersocPerson(request, pk=None):
    if request.method == 'POST':
        my_form = PersonForm(request.POST, request.FILES)
        sersoc_form = ServicioSocialForm(request.POST, request.FILES)
       
        if all([my_form.is_valid(), sersoc_form.is_valid()]):
            if pk:
                person = Person.objects.get(pk=pk)
                sersoc = ServicioSocial.objects.get(info_person = person)
                my_form = PersonForm(request.POST or None, instance=person)
                sersoc_form = ServicioSocialForm(request.POST or None, instance=sersoc)
            form = my_form.save()
            valor = form.pk
            valor = str(valor).zfill(4)
            code= "S"+ form.fecha_ingreso.strftime('%y') + valor
            form.matricula = code
            form.save()
            sersoc = sersoc_form.save(commit=False)
            sersoc.info_person = form
            sersoc.save()
            return redirect('sersoc_list')
    else:
        if pk:
            person = Person.objects.get(pk=pk)
            sersoc = ServicioSocial.objects.get(info_person = person)
            my_form = PersonForm(instance=person)
            sersoc_form = ServicioSocialForm(instance=sersoc)
            documentos = DocumentosSS.objects.filter(info_person = person)
            return render(request, 'people/sersoc/serviciosocial_form.html', {'form': my_form, 'sersoc_form': sersoc_form, "files": documentos, "person":person})
        else:
            my_form = PersonForm()
            my_form.fields["puesto"].initial = 'Servicio Social'
            my_form.fields["cat_area_org"].initial = '1'
            my_form.fields["email_institucional"].initial = 'ss@serviciosocial.com'
            my_form.fields["fecha_ingreso"].initial = datetime.datetime.now()
            my_form.fields["cat_contratacion"].initial = 6
            sersoc_form = ServicioSocialForm()
       # print(getDirectoryItems(person.matricula))
    return render(request, 'people/sersoc/serviciosocial_form.html', {'form': my_form, 'sersoc_form': sersoc_form })


class IncidenciaToShowSS:  
    def __init__(self, dia,  fecha, idIn, Entrada, idOut, Salida, horas):
        self.dia = dia
        self.fecha = fecha  
        self.idIn = idIn  
        self.Entrada = Entrada
        self.idOut = idOut
        self.Salida = Salida 
        self.horas = horas

@method_decorator(login_required, name='dispatch')
class SersocAsistListView(ListView):
    model = ServicioSocial
    def get(self, request, *args, **kwargs):
        horas = 0
        person = Person.objects.get(pk=self.kwargs['person'])
        nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
        list = []  
        sersoc = ServicioSocial.objects.get(info_person = person)
        dateInicio = Incidencia.objects.filter(Q(matriculaCredencial = person)).aggregate(min_date=Min('created_at'))['min_date']
        if dateInicio:
            dateFin = Incidencia.objects.filter(Q(matriculaCredencial = person)).aggregate(max_date=Max('created_at'))['max_date']
            incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin+ timedelta(days = 1)]))
            i=0
            for n in range(int((dateFin - dateInicio).days)+1):
                incidencia = incidencias.filter(created_at__day=(dateInicio + timedelta(n)).day, created_at__month = (dateInicio + timedelta(n)).month, created_at__year = (dateInicio + timedelta(n)).year)
                if incidencia :
                    incidenciaOut = incidencia.latest('created_at')
                    #print(incidenciaOut)
                    if incidencia.count()>1:
                        incidenciaIn = incidencia.earliest('created_at')
                        if  incidenciaIn.causa_incidencia != None : 
                            diferencia_tiempo = (incidenciaOut.created_at - incidenciaIn.created_at).Hours
                            horas += diferencia_tiempo
                            list.append( IncidenciaToShowSS( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S") , diferencia_tiempo  )) 
                        else:
                            list.append( IncidenciaToShowSS( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), diferencia_tiempo)) 
                        
                    else:
                        incicenciaFirst = incidencia.first()
                        if  incicenciaFirst.causa_incidencia != None :
                            list.append( IncidenciaToShowSS(nombreDias[int( incicenciaFirst.created_at.strftime("%w"))] ,  incicenciaFirst.created_at.strftime("%d/%m/%Y"),  incicenciaFirst.pk, "--:--",  incicenciaFirst.pk, "--:--" ), "-") 
                    
                else:
                    list.append( IncidenciaToShowSS( nombreDias[int(  (dateInicio + timedelta(n)).strftime("%w")  )], (dateInicio + timedelta(n)).strftime("%d/%m/%Y"),  "null" , "--:--",  "null", "--:--"), "-") 
            content =  {
                'list': list,
                'person': person,
                'sersoc': sersoc,
                'fechaInicio': dateInicio, 
                'fechaFin': dateFin,
                'horas' : horas,
            } 
        else:
            content =  {
                'list': list,
                'person': person,
                'sersoc': sersoc,
                'horas': None,
            }          
       
        return render(request, 'people/sersoc/detalle_incidencia.html' , content)



def GetAsistencia(request, person):
    person = Person.objects.get(pk=person)
    nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
    list = []  
    sersoc = ServicioSocial.objects.get(info_person = person)
    dateInicio = Incidencia.objects.filter(Q(matriculaCredencial = person)).aggregate(max_date=Max('created_at'))['max_date']
    if dateInicio:
        dateFin = Incidencia.objects.filter(Q(matriculaCredencial = person)).aggregate(min_date=Min('created_at'))['min_date']
        incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin+ timedelta(days = 1)]))
        i=0
        for n in range(int((dateFin - dateInicio).days)+1):
            incidencia = incidencias.filter(created_at__day=(dateInicio + timedelta(n)).day, created_at__month = (dateInicio + timedelta(n)).month, created_at__year = (dateInicio + timedelta(n)).year)
            if incidencia :
                incidenciaOut = incidencia.latest('created_at')
                #print(incidenciaOut)
                if incidencia.count()>1:
                    incidenciaIn = incidencia.earliest('created_at')
                    if  incidenciaIn.causa_incidencia != None : 
                        list.append( IncidenciaToShowSS( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S")  )) 
                    else:
                        list.append( IncidenciaToShowSS( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ")) 
                    
                else:
                    incicenciaFirst = incidencia.first()
                    if  incicenciaFirst.causa_incidencia != None :
                        list.append( IncidenciaToShowSS(nombreDias[int( incicenciaFirst.created_at.strftime("%w"))] ,  incicenciaFirst.created_at.strftime("%d/%m/%Y"),  incicenciaFirst.pk, "--:--",  incicenciaFirst.pk, "--:--" )) 
                
            else:
                list.append( IncidenciaToShowSS( nombreDias[int(  (dateInicio + timedelta(n)).strftime("%w")  )], (dateInicio + timedelta(n)).strftime("%d/%m/%Y"),  "null" , "--:--",  "null", "--:--")) 
                
    t = get_template('people/sersoc/detalle_incidencia.html')
    content =  t.render({
                'list': list,
                'person': person,
                'sersoc': sersoc,
            } )
    return HttpResponse(content)
   


class SersocCreateView(CreateView):
    form_class = PersonForm
    template_name = 'people/sersoc/serviciosocial_form.html'
    def get_initial(self):
        # You can set initial values for the form fields here
        initial = super().get_initial()
        initial['puesto'] = 'Servicio Social'
        initial['cat_area_org']= '1'
        initial['email_institucional']= 'ss@serviciosocial.com'
        initial['fecha_ingreso']= datetime.datetime.now()
        initial['cat_contratacion']=6
        return initial
    def get_context_data(self, **kwargs):
        context = super(SersocCreateView, self).get_context_data(**kwargs)
        context['sersocFormset'] = ServicioSocialInlineFormset()
        return context
    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
       
        
        sersoc_meta_formset = ServicioSocialInlineFormset(self.request.POST)
        if form.is_valid(): #and sersoc_meta_formset.is_valid():
            return self.form_valid(form, sersoc_meta_formset)
        else:
            return self.form_invalid(form, sersoc_meta_formset)
    def form_valid(self, form, sersoc_meta_formset):
        self.object = form.save(commit=False)
        self.object.save()
        # saving ProductMeta Instances
        sersocs = sersoc_meta_formset.save(commit=False)
        for meta in sersocs:
            meta.info_person_id = self.object
            meta.save()
        return redirect(reverse("sersoc_list"))
    def form_invalid(self, form, sersoc_meta_formset):
        return self.render_to_response(
            self.get_context_data(form=form,
                                  sersocFormset=sersoc_meta_formset
                                  )
        )

class SersocFileListView(ListView):
    model = ServicioSocial
    def get(self, request, *args, **kwargs):
       
       
        return render(request, 'people/sersoc/file_detail.html')

class FilesToShow:  
    def __init__(self, name,  isDirectory, size, link):
        self.name = name
        self.isDirectory = isDirectory 
        self.size = size
        self.link = link
    def to_dict(self):
        return {
            'name': self.name,
            'isDirectory': self.isDirectory,
            'size': self.size,
           
        }
       
def getDirectoryItems(matricula):
    directory_info = GetDirectoryInfo(matricula)
    files = []
    if 'value' in directory_info:
        for file in directory_info['value']:
            files.append(FilesToShow(file['name'], False, file['size'],file['webUrl']))
    return files

@csrf_exempt 
def SaveDocumento(request):
    try:
        if request.method == 'POST':
            file = request.FILES['myfile']
            pk = request.POST.get('pk')
            matricula = request.POST.get('matricula')
            person = Person.objects.get(matricula = matricula)
            file_name = UploadFile(file, None,  person.matricula)
            json_data = DownloadFiles(person.matricula, file_name)
            try:
                doc = DocumentosSS.objects.get(Q(nombre=file_name) & Q(info_person = person))
                doc.metadatos = json_data  
            except DocumentosSS.DoesNotExist:
                print("Doc not exist")
                documento = DocumentosSS( info_person = person, nombre= file_name, metadatos = json_data)
                documento.save()
        documento_data={"error":False,"errorMessage":"Documento Agregado!", "documento": json_data }
        return JsonResponse(documento_data,safe=False)
    except Exception as e:
        print(e)
        capacitacion_data={"error":True,"errorMessage":"Error al cargar evidencia"}
        return JsonResponse(documento_data,safe=False)