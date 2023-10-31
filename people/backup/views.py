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
from people.models import AreaOrganigrama, Compensaciones, Person, Incidencia, Bajas, AreaInterna
from people.forms import IncidenciaForm, PersonForm
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

from django.template.loader import get_template
from django.template import Context
from django.core.files.storage import FileSystemStorage
import os 
import errno
#import vlc

def searchPerson(request):
    try:
        if request.is_ajax():
            now = datetime.datetime.now()
            fecha2 = now - timedelta(hours=0, minutes=10)
            person = Person.objects.get(matricula = request.POST['matricula'] )
            #&&  _lt Q(created_at__gt= now-timedelta(hours=4)) 
            incidenciaPrev = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=now.day, created_at__month = now.month, created_at__year = now.year)) 
            incidencia = Incidencia()
            incidencia.created_at= now
            incidencia.matriculaCredencial = person
            
            if not incidenciaPrev:
                ni = person.matricula+ "_"+ person.nombres +" "+person.apellido1 + " "+ person.apellido2
                img= savePhoto(request.POST['photo'] )
                incidencia.imagen.save(ni+"_IN.png",img)
                incidencia.save()
                if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
                    incidencia_data={"error":False,"welcome":"Bienvenid@", "errorMessage":"Registro de asistencia "+ str(now.strftime("%Y-%m-%d %H:%M")), "persona": person.nombres +" "+person.apellido1 + " "+ person.apellido2, "imagen" : person.imagen_base64, "base": True }
                else:
                    incidencia_data={"error":False,"welcome":"Bienvenid@","errorMessage":"Acceso visitante " + str(now.strftime("%Y-%m-%d %H:%M")) ,"base": False }
            
            else :
                inandout = incidenciaPrev.count()
                prevDate = incidenciaPrev.latest('created_at').created_at
                time = now - prevDate.replace(tzinfo=None)
                timeSeconds = time.total_seconds() 
                difTime = divmod(timeSeconds, 60)[0]
                if difTime > 120 :
                    ni = person.matricula+ "_"+ person.nombres +" "+person.apellido1 + " "+ person.apellido2
                    img= savePhoto(request.POST['photo'] )
                    incidencia.imagen.save(ni+"_OUT.png",img)
                    incidencia.save()
                    if person.cat_contratacion.pk == 1 or person.cat_contratacion.pk == 2 :
                        incidencia_data={"error":False,"welcome":"Hasta pronto","errorMessage":"Registro de asistencia "+ str(now.strftime("%Y-%m-%d %H:%M")), "persona": person.nombres +" "+person.apellido1 + " "+ person.apellido2, "imagen" : person.imagen_base64, "base": True }
                    else:
                        incidencia_data={"error":False,"welcome":"Vuelva pronto","errorMessage":"Salida visitante " + str(now.strftime("%Y-%m-%d %H:%M")), "base": False }
                    return JsonResponse(incidencia_data,safe=True)
                if inandout == 1:    
                    incidencia_data={"error":True,"errorMessage":"Entrada Registrada anteriormente con fecha y hora: "+ str(prevDate.strftime("%Y-%m-%d %H:%M"))}
                else:
                     incidencia_data={"error":True,"errorMessage":"Salida Registrada anteriormente con fecha y hora: "+ str(prevDate.strftime("%Y-%m-%d %H:%M"))}
        return JsonResponse(incidencia_data,safe=True, status=200)
    except Exception:            
        return HttpResponse(status=404)


def getDifference(then, interval = "secs"):
    duration = now - then
    duration_in_s = duration.total_seconds() 
    #Date and Time constants
    yr_ct = 365 * 24 * 60 * 60 #31536000
    day_ct = 24 * 60 * 60 			#86400
    hour_ct = 60 * 60 					#3600
    minute_ct = 60 
    
    def yrs():
      return divmod(duration_in_s, yr_ct)[0]

    def days():
      return divmod(duration_in_s, day_ct)[0]

    def hrs():
      return divmod(duration_in_s, hour_ct)[0]

    def mins():
      return divmod(duration_in_s, minute_ct)[0]

    def secs(): 
      return duration_in_s

    return {
        'yrs': int(yrs()),
        'days': int(days()),
        'hrs': int(hrs()),
        'mins': int(mins()),
        'secs': int(secs())
    }[interval]


def savePhoto( image_data):
    #makeDir(folder)
    format, imgstr = image_data.split(';base64,')
    data = ContentFile(base64.b64decode(imgstr))
    return data


def saveCheckedPerson(request):
    if request.is_ajax():
        now = datetime.datetime.now()
        fecha2 = now - timedelta(hours=0, minutes=50)
        print(fecha2)
        print(request.POST['matricula'])
        person = Person.objects.get(matricula = request.POST['matricula'] )
        incidenciaPrev = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__lt=now) & Q(created_at__gt=fecha2) )
        
        if not incidenciaPrev:
            incidencia = Incidencia()
            incidencia.matriculaCredencial = person
         
            incidencia.save()
            incidencia_data={"error":False,"errorMessage":"Incidencia Registrada "+ str(now)}
            #return HttpResponse(status=201)
            return JsonResponse(incidencia_data,safe=True)
        else :
            for date in incidenciaPrev:
                #print(date.created_at)
                #print(now)
                prevDate = date.created_at
                #prevTime = datetime.datetime.strptime(str(date.created_at), '%Y/%m/%d %H:%M:%S.%f')
                time = now - prevDate.replace(tzinfo=None)
                timeSeconds = time.total_seconds() 
                #print(timeSeconds)
                difTime = divmod(timeSeconds, 60)[0]
                #print(difTime)
                #return HttpResponse(status=404)"%H:%M:%S"
                incidencia_data={"error":True,"errorMessage":"Incidencia Registrada anteriormente "+ str(date.created_at)}
        return JsonResponse(incidencia_data,safe=True)
            
    else:
        return HttpResponse(status=404)

#@login_required(login_url='/accounts/login/')
@method_decorator(login_required, name='dispatch')
class PersonListView(ListView):
    model = Person
    context_object_name = 'people'
    #querysetBajas = Bajas.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    #querysetPersons = Person.objects.all().values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    #queryset = querysetPersons.difference(querysetBajas)  
    queryset = Person.objects.filter(activo=True).order_by('created_at')
    paginate_by = 50

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        q = self.request.GET.get('q')
        if q:
            q =q.split(" ")
            query = reduce(operator.and_, ((Q(nombres__unaccent__icontains=item) | Q(apellido1__unaccent__icontains=item) | Q(apellido2__unaccent__icontains=item) | Q(matricula__icontains=item) ) for item in q))
            return qs.filter(query)
        return qs      



class PersonCreateView(CreateView):
    model = Person
    form_class = PersonForm
    success_url = reverse_lazy('person_list')
    def form_valid(self, form):
        self.object = form.save()
        code=""
        valor = Person.objects.all().last().pk
        valor = str(valor).zfill(4)
        if self.object.cat_contratacion.nombre == "Honorarios":
            code= "H"+ self.object.fecha_ingreso.strftime('%y') + valor
        if self.object.cat_contratacion.nombre == "Eventuales":
            code= "E"+ self.object.fecha_ingreso.strftime('%y')  + valor
        if self.object.cat_contratacion.nombre == "Confianza Mandos Medios":
            code= "M"+ self.object.fecha_ingreso.strftime('%y') + valor
        if self.object.cat_contratacion.nombre == "Operativo Confianza":
            code= "C"+ self.object.fecha_ingreso.strftime('%y') + valor
        if self.object.cat_contratacion.nombre == "Operativo Base":
            code= "B"+ self.object.fecha_ingreso.strftime('%y') + valor
        self.object.matricula = code
        self.object.save()
        
        try:
            format, img = form.cleaned_data["imagen_base64"].split(';base64,')
            img = ContentFile(b64decode(img.encode()))

            self.object.imagen.save("imagen.png", img, save=True)
        except Exception as e:
            print(e)
            pass
        return HttpResponseRedirect(self.get_success_url())


class PersonUpdateView(UpdateView):
    model = Person
    form_class = PersonForm
    template_name = 'people/person_form_update.html'
    success_url =  reverse_lazy('activos_list')
   
    
        
   

class PersonCheckView(CreateView):
    model = Incidencia
    form_class = IncidenciaForm
    template_name = 'people/person_form_incidencia.html'
    success_url = reverse_lazy('person_list')
   

class ReportePersonasPDF(View):  
     
    def cabecera(self,pdf):
        archivo_imagen = settings.MEDIA_ROOT+'/imagenes/fondo.png'
        pdf.setLineWidth(1)
        pdf.setStrokeColorRGB(0.73,0.58,0.36)
        pdf.setFillColorRGB(0.73,0.58,0.36)
        pdf.rect(1,700,77,60, fill=1, stroke=0)
        pdf.rect(153,700,5,60, fill=1, stroke=0)
        pdf.setFillColor(colors.black) #sets Line/Rectangle Colors
        pdf.roundRect(78, 695, 75, 75, 5, 1, 0)
        pdf.drawImage(archivo_imagen, 0, 780, 155, 90,preserveAspectRatio=True)
        #pdf.rect(1,595,160,245, fill=0, stroke=1)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColorRGB(64/255,120/255,105/255)
        pdf.drawCentredString(40, 782, 'GAFETE')
        


    def drawName(self, pdf, texto):
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColorRGB(0,0,0)   
        y = 743
        wrapper = textwrap.TextWrapper(width=12)
        word_list = wrapper.wrap(text=texto)
        for element in word_list:
            print(element)
            pdf.drawCentredString(42, y, element)
            y -= 12    

    def drawMatricula(self, pdf, texto):
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColorRGB(0,0,0)   
        pdf.drawCentredString(80, 610, texto)
           

    def drawArea(self, pdf, texto):
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColorRGB(1,1,1) 
        y = 670
        wrapper = textwrap.TextWrapper(width=26)
        word_list = wrapper.wrap(text=texto)
        for element in word_list:
            print(element)
            pdf.drawCentredString(78, y, element)
            y -= 12     

    def drawSubarea(self, pdf, texto):
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColorRGB(1,1,1) 
        y = 640
        wrapper = textwrap.TextWrapper(width=26)
        word_list = wrapper.wrap(text=texto)
        for element in word_list:
            print(element)
            pdf.drawCentredString(84, y, element)
            y -= 12     

    def get(self, request, *args, **kwargs):
        person = Person.objects.get(pk=self.kwargs['pk'])
        response = HttpResponse(content_type='application/pdf')
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        self.foto(pdf, person)
        self.cabecera(pdf)
        self.drawName(pdf, person.nombres + ' ' + person.apellido1 + ' ' + person.apellido2)
        self.drawMatricula(pdf, person.matricula)
        self.drawArea(pdf, person.puesto)
        #self.drawSubarea(pdf, person.cat_area_org.nombre )
        #Con show page hacemos un corte de página para pasar a la siguiente
        pdf.showPage()
        #pdf.rect(1,595,160,245, fill=0, stroke=1)
        self.codigoQr(pdf, person.matricula)
        self.firma(pdf, 'Agradecemos a las autoridades civiles y militares, otorguen al portador de la presente, todas las facilidades para el mejor desempeño de sus funciones. '
                        'Esta credencial es propiedad de la Coordinación '
                        'General @prende.mx, es intransferible y tendrá '
                        'vigencia en el período estipulado.')
        pdf.save()

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
    
    def codigoQr(self, pdf, texto):
        img = qrcode.make(texto)
        f = open(settings.MEDIA_ROOT+'/imagenes/Matricula_'+ texto +'.png', "wb")
        img.save(f)
        f.close()
        pdf.drawImage(settings.MEDIA_ROOT+'/imagenes/Matricula_'+ texto +'.png', 30, 750, 100, 94,preserveAspectRatio=True) 

    def firma(self, pdf, texto):
        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0,0,0) 
        pdf.drawCentredString(80, 742, 'AUTORIZA')
        pdf.drawImage(settings.MEDIA_ROOT+'/imagenes/firma.png', 55, 680, 70, 70,preserveAspectRatio=True) 
        pdf.setFont("Helvetica", 6)
        wrapper = textwrap.TextWrapper(width=49)
        word_list = wrapper.wrap(text=texto)
        y = 680
        for element in word_list:
            print(element)
            pdf.drawCentredString(81, y, element)
            y -= 7  
        pdf.setFont("Helvetica-Bold", 6)  
        pdf.drawCentredString(80, 620, 'VIGENCIA: DICIEMBRE 2024')

    def foto(self, pdf, person):
        archivo_imagen_fondo = settings.MEDIA_ROOT+'/imagenes/fondoverdeconcorte.png'
        
       # try:
       #     conexion  = pyodbc.connect("DSN=PERSONALFOT_IB")
        #    print("\n"*2)
         #   print("conexión exitosa")
          #  cursor = conexion.cursor()
          #  cursor.execute('select ID_MATRICULA, IMAGEN from FOTOS where ID_MATRICULA = 20002') # Se genera el cursor con el criterio
          #  for fila in cursor.fetchall():
           #     print(fila[0])
         
        imagen = person.imagen_base64
        if not len(imagen) == 0:
            filename = settings.MEDIA_ROOT+'/fotos/foto'+person.matricula+'.jpg'
            imagen = imagen.replace('data:image/png;base64,','')
            image_64_decode = base64.b64decode(imagen) 
            image_result = open(filename, 'wb') # create a writable image and write the decoding result
            image_result.write(image_64_decode)
            pdf.drawImage(filename, 65, 690, 115, 90,preserveAspectRatio=True)
        else :
            pdf.drawImage(settings.MEDIA_ROOT+'/imagenes/nofoto.png', 57, 690, 115, 90,preserveAspectRatio=True)
        pdf.setLineWidth(17.2)
        pdf.setStrokeColorRGB(1,1,1)
        pdf.setFillColorRGB(1,1,1)
        pdf.rect(160,690,90,90, fill=1, stroke=0)
        pdf.roundRect(70.5, 685, 90, 93, 13, 1, 0)
        pdf.drawImage(archivo_imagen_fondo, 1, 549, 155.5, 200,preserveAspectRatio=True, mask='auto') 

@method_decorator(login_required, name='dispatch')
class PersonBajaListView(ListView):
    model = Bajas
    context_object_name = 'people'
    template_name = 'people/bajas/baja_list.html'
    queryset =Bajas.objects.all()
    paginate_by = 50

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        q = self.request.GET.get('q')
        if q:
            q =q.split(" ")
            query = reduce(operator.and_, ((Q(info_person__nombres__unaccent__icontains=item) | Q(info_person__apellido1__unaccent__icontains=item) | Q(info_person__apellido2__unaccent__icontains=item) | Q(info_person__matricula__icontains=item) ) for item in q))
            return qs.filter(query)
        return qs


@csrf_exempt
def GetPersonas(request):
    querysetBajas = Bajas.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    querysetPersons = Person.objects.all().values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    persons_data = querysetPersons.difference(querysetBajas)  
    #persons_data= Person.objects.all()  
    t = get_template('people/bajas/persona_baja_list.html')
    content = t.render(
    {
        'people': persons_data, 
       
    })
    return HttpResponse(content)

@csrf_exempt
def InsertBaja(request):
    id=request.POST.get("id")
    try:
        baja=Person.objects.get(pk=id)
        if baja.activo:
            baja.activo=False
            baja.save()
            bajaPersona=Bajas(info_person= baja)
            bajaPersona.save()
            baja_data={"id":baja.pk,"matricula": baja.matricula, "nombre":baja.nombres +" " +baja.apellido1+ " " + baja.apellido2, "created_at":bajaPersona.created_at.strftime('%c'),"error":False,"errorMessage":"Baja registrada"}
        return JsonResponse(baja_data,safe=False)
    except:
        baja_data={"error":True,"errorMessage":"Error al querer dar de baja Empleado"}
        return JsonResponse(baja_data,safe=False)

@csrf_exempt
def InsertComp(request):
    id=request.POST.get("id").strip()
    try:
        person=Person.objects.get(pk=id)
        comp= Compensaciones.objects.filter(info_person__pk=id)
        if not comp:
            compPersona=Compensaciones(info_person= person)
            compPersona.save()
            comp_data={"id":person.pk,"matricula": person.matricula, "nombre":person.nombres +" " +person.apellido1+ " " + person.apellido2, "created_at":compPersona.created_at.strftime('%c'),"error":False,"errorMessage":"Compensación registrada"}
        return JsonResponse(comp_data,safe=False)
    except:
        comp_data={"error":True,"errorMessage":"Error al querer dar de alta Compensación"}
        return JsonResponse(comp_data,safe=False)


@csrf_exempt
def GetCompPersonas(request):
    querysetComp = Compensaciones.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    querysetPersons = Person.objects.filter(activo=True).values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    persons_data = querysetPersons.difference(querysetComp)  
    #persons_data= Person.objects.all()  
    t = get_template('people/bajas/persona_baja_list.html')
    content = t.render(
    {
        'people': persons_data, 
       
    })
    return HttpResponse(content)

@method_decorator(login_required, name='dispatch')
class PersonCompListView(ListView):
    model = Compensaciones
    context_object_name = 'people'
    template_name = 'people/comp/comp_list.html'
    queryset =Compensaciones.objects.all()
    paginate_by = 50

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        q = self.request.GET.get('q')
        if q:
            q =q.split(" ")
            query = reduce(operator.and_, ((Q(info_person__nombres__unaccent__icontains=item) | Q(info_person__apellido1__unaccent__icontains=item) | Q(info_person__apellido2__unaccent__icontains=item) | Q(info_person__matricula__icontains=item) ) for item in q))
            return qs.filter(query)
        return qs


class DirectoryListView(ListView):
 

    model = Person
    context_object_name = 'people'
    template_name = 'people/person_directory.html'
    #querysetBajas = Bajas.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    #querysetPersons = Person.objects.all().values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    #queryset = querysetPersons.difference(querysetBajas)  
    queryset = Person.objects.filter(activo=True).order_by('apellido1')
    paginate_by = 50

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
     
        q = self.request.GET.get('q')
        a = self.request.GET.get('a')
        if q:
            q =q.split(" ")
            query = reduce(operator.and_, ((Q(nombres__unaccent__icontains=item) | Q(apellido1__unaccent__icontains=item) | Q(apellido2__unaccent__icontains=item) | Q(email_institucional__icontains=item)  | Q(extension_telefonica__icontains=item) | Q(cat_area_org__nombre__unaccent__icontains=item) | Q(puesto__unaccent__icontains=item) ) for item in q))
            return qs.filter(query)
        elif a:
            #a = a.split(" ")
            query = Q(apellido1__startswith=a)
            return qs.filter(query)
        return qs  
    def get_context_data(self, **kwargs):
        context = super(DirectoryListView, self).get_context_data(**kwargs)
        context['areas'] =  querysetAreas = AreaInterna.objects.all()
        return context  
    

@csrf_exempt
def GetPersonasDirectory(request):
    q=request.GET.get("q")
    a=request.GET.get("a")
    area = request.GET.get("area")
    queryset = Person.objects.filter(activo=True).order_by('apellido1')
    if q and q !=" ":
        q =q.split(" ")
        query = reduce(operator.and_, ((Q(nombres__unaccent__icontains=item) | Q(apellido1__unaccent__icontains=item) | Q(apellido2__unaccent__icontains=item) | Q(email_institucional__icontains=item)  | Q(extension_telefonica__icontains=item) | Q(cat_area_org__nombre__unaccent__icontains=item) | Q(puesto__unaccent__icontains=item) ) for item in q))
        queryset = queryset.filter(query)     
    elif a:
            #a = a.split(" ")
        query = Q(apellido1__startswith=a)
        queryset = queryset.filter(query)
    elif area:  
        query = Q(areaInterna__id=area)
        queryset = queryset.filter(query) 
    t = get_template('people/directorio/directorio.html')
    content = t.render(
    {
        'people': queryset,        
    })
    return HttpResponse(content)