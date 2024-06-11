from django.views.generic import ListView, CreateView, UpdateView, View
from people.models import Capacitacion, EvidenciaCurso, Person
from people.forms import CapacitacionForm
from django.urls import reverse_lazy
from django.core.files.base import ContentFile
from base64 import b64decode
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, JsonResponse
from .incidenciasView import get_attributes
from PIL import Image
from .sharepoint import UploadFile, DownloadFiles
from django.template.loader import get_template
@method_decorator(login_required, name='dispatch')
class CapacitacionCreateView(CreateView):
    model = Capacitacion
    form_class = CapacitacionForm
    success_url = reverse_lazy('capacitacion_list')
    def form_valid(self, form):
        self.object = form.save()
        try:
            format, img = form.cleaned_data["imagen_base64"].split(';base64,')
            img = ContentFile(b64decode(img.encode()))

            self.object.imagen.save("imagen.png", img, save=True)
        except Exception as e:
            print(e)
            pass
        return HttpResponseRedirect(self.get_success_url())


#@method_decorator(login_required, name='dispatch')
class CapacitacionListView(ListView):
    model = Capacitacion
    paginate_by = 50
    queryset = Capacitacion.objects.filter( Q(activo=True) )
    def get(self, request, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
                'capacitacion': qs, 
            }
        return render(request, 'people/capacitacion/capacitacion_list.html' , content)
    
@csrf_exempt    
def SaveCapacitacion(request):
    nombre=request.POST.get('nombre')
    imagen=request.POST.get('imagen')
    ruta = request.POST.get('ruta')
    try:
        addCapacitacion=Capacitacion(nombre= nombre)
        addCapacitacion.imagen_base64 = imagen
        addCapacitacion.enlace = ruta
        addCapacitacion.save()
        capacitacionData={"nombre":nombre,"error":False,"errorMessage":"Capacitación registrada" , "html_data": GetTableCursos()}
        return JsonResponse(capacitacionData, safe=False )
    except  Exception as e:
        raise e
        ayudaData={"error":True,"errorMessage":"Error al querer dar de alta Capacitación"}
    return JsonResponse(ayudaData,safe=False)



class CapacitacionView(View):
    def get(self, request, *args, **kwargs):
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
            }
        return render(request, 'people/capacitacion/admin/login.html' , content)

@csrf_exempt
def loginUsers(request):
    try:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            user = request.GET['usuario'] 
            pwd = request.GET['password']
            response = get_attributes(user, pwd)
            if response['error'] == False:
                nombre = response['nombre']
                apellidos = response['apellidos']
                company = response['company']
                if company:
                    login_data={"error":False,"data": company}
                    request.session['username'] = nombre + ' ' + apellidos

                else:
                    login_data={"error":True,"errorMessage": "Acceso no permitido"}    
            else: 
                login_data={"error":True,"errorMessage": "Error al iniciar sesión, verifique sus datos"}
            return JsonResponse(login_data,safe=False)    
    except Exception as e:
        print(e)          
    return HttpResponse(status=404)

class CapacitacionesxPersona(View):
    model = EvidenciaCurso
    
    def get(self, request, *args, **kwargs):
        queryset = Capacitacion.objects.filter( Q(activo=True) ).values('pk', 'nombre',  'imagen_base64', 'fecha_limite', 'enlace')
        querysetPersona = EvidenciaCurso.objects.filter(info_person__matricula = self.kwargs['matricula'] ).values('curso_tomado__pk', 'curso_tomado__nombre', 'curso_tomado__imagen_base64',  \
                                                                                                                    'curso_tomado__fecha_limite', 'curso_tomado__enlace')
        person_cursos = queryset.difference(querysetPersona)  
        person = Person.objects.get(matricula =self.kwargs['matricula'] )
        entregadas = EvidenciaCurso.objects.filter(Q(info_person__matricula = self.kwargs['matricula']) & ~Q(aprobado = 1)).values('curso_tomado__pk', 'curso_tomado__nombre', 'curso_tomado__imagen_base64',  \
                                                                                                                    'curso_tomado__fecha_limite', 'curso_tomado__enlace', 'metadatos', 'aprobado')
        rechazos = EvidenciaCurso.objects.filter( Q(info_person__matricula = self.kwargs['matricula']) & Q(aprobado = 1) ).values('pk', 'curso_tomado__pk', 'curso_tomado__nombre', 'curso_tomado__imagen_base64',  \
                                                                                                                    'curso_tomado__fecha_limite', 'curso_tomado__enlace', 'metadatos', 'observaciones')
        content = {
            'pendientes': person_cursos, 
            'entregadas': entregadas,
            'person': person,
            'rechazos': rechazos,
            }
        return render(request, 'people/capacitacion/personal/panel.html' , content)
    
@csrf_exempt 
def SaveCapacitacionEvidencia(request):
    try:
        if request.method == 'POST':
            file = request.FILES['myfile'] #returns a dict-like object
            pk = request.POST.get('pk')
            matricula = request.POST.get('matricula')
            remplazar = request.POST.get('remplazar')
            curso = Capacitacion.objects.get(pk = pk)
            person = Person.objects.get(matricula = matricula)
            file_name = UploadFile(file, matricula, curso)
            print("File Uploaded OK")
            json_data = DownloadFiles(curso, file_name)
            print("Getting information about the file"+ file_name)
            if remplazar == 'true':
                pk_evidencia= request.POST.get('pk_evidencia')
                evidencia = EvidenciaCurso.objects.get(pk=pk_evidencia)
                evidencia.metadatos = json_data
                evidencia.aprobado = 0
                evidencia.save()
            else:
                evidencia = EvidenciaCurso( info_person = person, curso_tomado = curso, metadatos = json_data, aprobado = 0)
                evidencia.save()
        capacitacion_data={"error":False,"errorMessage":"Evidencia de Capacitación Agregada!", "entregadas": GetTableEntregadas(matricula), "pendientes": GetTablePendientes(matricula), "rechazos":GetTableRechazos(matricula)  }
        return JsonResponse(capacitacion_data,safe=False)
    except Exception as e:
        print(e)
        capacitacion_data={"error":True,"errorMessage":"Error al cargar evidencia"}
        return JsonResponse(capacitacion_data,safe=False)

@csrf_exempt
def GetTableCursos():
    queryset = Capacitacion.objects.filter( Q(activo=True) )
    t = get_template('people/capacitacion/cursos.html')
    content = t.render(
    {
        'capacitacion': queryset,
    })  
    return content

@csrf_exempt
def GetTablePendientes(matricula):
    queryset = Capacitacion.objects.filter( Q(activo=True) ).values('pk', 'nombre',  'imagen_base64', 'fecha_limite', 'enlace')
    querysetPersona = EvidenciaCurso.objects.filter(info_person__matricula = matricula ).values('curso_tomado__pk', 'curso_tomado__nombre', 'curso_tomado__imagen_base64',  \
                                                                                                                    'curso_tomado__fecha_limite', 'curso_tomado__enlace')
    person_cursos = queryset.difference(querysetPersona)  
    #persons_data= Person.objects.all()  
    t = get_template('people/capacitacion/personal/pendientes.html')
    content = t.render(
    {
        'pendientes': person_cursos, 
    })  
    return content

@csrf_exempt
def GetTableEntregadas(matricula):
    entregadas = EvidenciaCurso.objects.filter(Q(info_person__matricula = matricula) & ~Q(aprobado = 1)).values('curso_tomado__pk', 'curso_tomado__nombre', 'curso_tomado__imagen_base64',  \
                                                                                                                    'curso_tomado__fecha_limite', 'curso_tomado__enlace', 'metadatos', 'aprobado')
    t = get_template('people/capacitacion/personal/entregadas.html')
    content = t.render(
    {
        'entregadas': entregadas,
    })  
    return content

@csrf_exempt
def GetTableRechazos(matricula):
    rechazos = EvidenciaCurso.objects.filter( Q(info_person__matricula = matricula) & Q(aprobado = 1) ).values('pk', 'curso_tomado__pk', 'curso_tomado__nombre', 'curso_tomado__imagen_base64',  \
                                                                                                                    'curso_tomado__fecha_limite', 'curso_tomado__enlace', 'metadatos', 'observaciones')
    t = get_template('people/capacitacion/personal/rechazos.html')
    content = t.render(
    {
        'rechazos': rechazos,
    })  
    return content

class CapacitacionXCursoView(View):
    def get(self, request, *args, **kwargs):
        #t = get_template('people/Incidencias/inci_list.html')
        evidencias = EvidenciaCurso.objects.filter(curso_tomado__pk = self.kwargs['pk'] ).values('pk', 'info_person__nombres', 'info_person__apellido1', 'info_person__apellido2', 'info_person__matricula', 'created_at', 'aprobado', 'metadatos').order_by('info_person__apellido1')
        curso = Capacitacion.objects.get(pk = self.kwargs['pk'])
        content = {
            'evidencias': evidencias,
            'curso': curso,
            }
        return render(request, 'people/capacitacion/admin/capacitacion_list_person.html' , content)  

@csrf_exempt
def UpdateStatusEvidencia(request):
    try: 
        curso = EvidenciaCurso.objects.get(pk = request.GET.get('pk'))
        curso.aprobado = request.GET.get('status')
        if request.GET.get('obs'):
            curso.observaciones = request.GET.get('obs')
        curso.save()
        update_data={"error":False}
        return JsonResponse(update_data,safe=False)
    except Exception as e:
        print(e)
        update_data={"error":True,"errorMessage":"Error al cargar evidencia"}
        return JsonResponse(update_data,safe=False)
