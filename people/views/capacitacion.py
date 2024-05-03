from django.views.generic import ListView, CreateView, UpdateView, View
from people.models import Capacitacion
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
    try:
        addCapacitacion=Capacitacion(nombre= nombre)
        addCapacitacion.imagen_base64 = imagen
        addCapacitacion.save()
        capacitacionData={"nombre":nombre,"error":False,"errorMessage":"Capacitación registrada"}
        return JsonResponse(capacitacionData,safe=False)
    except  Exception as e:
        raise e
        ayudaData={"error":True,"errorMessage":"Error al querer dar de alta Capacitación"}
    return JsonResponse(ayudaData,safe=False)

class Capacitacion(View):
    def get(self, request, *args, **kwargs):
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
            }
        return render(request, 'people/capacitacion/admin/login.html' , content)

@csrf_exempt
def loginUsers(request):
    try:
        if request.is_ajax():
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
    def get(self, request, *args, **kwargs):
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
            }
        return render(request, 'people/capacitacion/admin/panel.html' , content)