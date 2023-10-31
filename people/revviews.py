from asyncio.windows_events import NULL
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

from django.http import FileResponse, Http404
#import vlc




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

def showImage(request):
    year= request.GET('year')
    month=request.GET('month')
    day= request.GET('day')
    photo = request.GET('photo')
#############################
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


class PersonDirectoryUpdateView(UpdateView):
    model = Person
    form_class = DirectorioUpdateForm
    template_name = 'people/directorio/person_form_update.html'
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
                comp_data={"id":person.pk,"matricula": person.matricula, "nombre":person.nombres +" " +person.apellido1+ " " + person.apellido2, "compensacion":compensacion.nombre,"error":False,"errorMessage":"Compensación registrada"}
            else:
                 comp_data={"id":person.pk,"matricula": person.matricula, "nombre":person.nombres +" " +person.apellido1+ " " + person.apellido2, "compensacion":compensacion.nombre,"error":True,"errorMessage":"Se alcanzo el máximo de registros"}
        
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

#@method_decorator(login_required, name='dispatch')
@csrf_exempt
def PersonCompListView(request):
    #model = Compensaciones
    #context_object_name = 'people'
    #template_name = 'people/comp/comp_list.html'
    queryset =Compensaciones.objects.all()
    querysetComp = Compensacion.objects.all()
    #paginate_by = 50

    #def get_queryset(self, *args, **kwargs):
     #   qs = super().get_queryset(*args, **kwargs)
     #   q = self.request.GET.get('q')
     #   if q:
     #       q =q.split(" ")
     #       query = reduce(operator.and_, ((Q(info_person__nombres__unaccent__icontains=item) | Q(info_person__apellido1__unaccent__icontains=item) | Q(info_person__apellido2__unaccent__icontains=item) | Q(info_person__matricula__icontains=item) ) for item in q))
     #       return qs.filter(query)
     #   return qs
    t  = get_template('people/comp/comp_list.html')
    content = t.render(
    {
        'people': queryset, 
        'compensacion' : querysetComp,

       
    })
    return HttpResponse(content)
        


@method_decorator(login_required, name='dispatch')
class PersonInciListView(ListView):
    template_name = 'people/inci/inci_list.html'
    model = Person
    context_object_name = 'people'
    queryset = Person.objects.filter( Q(activo=True) )
    paginate_by = 50

class ReporteIncidenciasPDF(View):

    pdfmetrics.registerFont(TTFont('Montserrat', settings.MEDIA_ROOT+'/montserrat/Montserrat-Light.ttf'))
    pdfmetrics.registerFont(TTFont('Montserrat-Bold', settings.MEDIA_ROOT+'/montserrat/Montserrat-Bold.ttf'))  
    

    def pdf_return(self,nombre):
        filename = settings.MEDIA_ROOT+"/"+"Formatos/Reporte de Asistencia"+nombre+".pdf"
        with open(filename, 'rb') as pdf:
            response = HttpResponse(pdf.read(),content_type='application/pdf')
            response['Content-Disposition'] = 'filename=some_file.pdf'
            return response

    def create_pdf(self, nombre, person, dateInicio, dateFin, rangoFecha):
            ruta =  settings.MEDIA_ROOT+"/"
            can = canvas.Canvas(nombre) 
            can.setFillColorRGB(0, 0, 0)
            can.setFont("Montserrat", 12)
            #can.drawCentredString(320, 666, "Reporte de Asistencia")
            can.drawString(150, 671, rangoFecha)
            can.drawString(150, 653, person.nombres+" "+person.apellido1+" "+person.apellido2)
            can.drawString(150, 634, person.rfc)
            can.drawString(150, 616, person.matricula)
            if person.cat_horario :
                can.drawString(150, 597, person.cat_horario.nombre) 
            else:
                can.drawString(150, 597, "-----") 
            #can.setFillColorRGB(0, 1, 1)
            can.setLineWidth(0.5)    

            if dateFin: #'fechaFin' in kwargs:
                incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin+ timedelta(1)]))
                numPages=0
                y=0
                rango=0
                for i in range(int((dateFin - dateInicio).days)+1):
                    if y>=( 375 - (60*rango)):
                        numPages+=1
                        can.showPage()
                        can.setFont("Montserrat", 12)
                    if numPages>0:
                        rango=1
                    
                    y = ((25*i)-(375*numPages)) - (180*rango)

                    can.rect(74, (515 - (y)), 109.5, 25, fill=0, stroke=1)
                    can.rect(183.5, (515 - (y)), 89, 25, fill=0, stroke=1)
                    can.rect(272.5, (515 - (y)), 90, 25, fill=0, stroke=1)
                    can.rect(362.5, (515 - (y)), 159, 25, fill=0, stroke=1)
                    
                    can.drawString(94, 523-(y), (dateInicio + timedelta(i)).strftime("%d-%m-%Y") )
                    incidencia = incidencias.filter(created_at__day=(dateInicio + timedelta(i)).day, created_at__month = (dateInicio + timedelta(i)).month, created_at__year = (dateInicio + timedelta(i)).year)
                    if incidencia :
                        observacion =" "
                        incidenciaOut = incidencia.latest('created_at')
                        print(incidenciaOut)
                        if incidenciaOut.causa_incidencia:
                            observacion +=   incidenciaOut.causa_incidencia.nombre +" / "
                        if incidencia.count()>1:
                            can.drawString(292, 523-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                            incidenciaIn = incidencia.earliest('created_at')
                        
                            can.drawString(204, 523-(y), incidenciaIn.created_at.strftime("%H:%M:%S") )
                            if incidenciaIn.causa_incidencia:
                                observacion += incidenciaIn.causa_incidencia.nombre +" / "
                        else:
                            if person.cat_horario and person.cat_horario.pk !=14:
                                fechaRevisada = revisarFecha(person.cat_horario.nombre,incidenciaOut.created_at)
                                if fechaRevisada == 1:
                                    can.drawString(204, 523-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                else:
                                    can.drawString(292, 523-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                            else:
                                    can.drawString(204, 523-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                            
                           
                        if len(observacion)>25:
                            can.setFont("Montserrat", 7)   
                        can.drawString(368, 523-(y), observacion)
                        can.setFont("Montserrat", 12)      
                      
                    
            else:
                incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=dateInicio.day, created_at__month = dateInicio.month, created_at__year = dateInicio.year) )
                incidenciaOut = incidencias.latest('created_at')
                can.drawString(292, 523, incidenciaOut.created_at.strftime("%H:%M:%S") )
               
                if incidencias.count()>1:
                    incidenciaIn = incidencias.earliest('created_at')
                    can.drawString(94, 523, incidenciaIn.created_at.strftime("%d-%m-%Y") )
                    can.drawString(204, 523, incidenciaIn.created_at.strftime("%H:%M:%S") )
                    can.rect(74, 515 , 109.5, 25, fill=0, stroke=1)
                    can.rect(183.5, 515 , 89, 25, fill=0, stroke=1)
                    can.rect(272.5, 515, 90, 25, fill=0, stroke=1)
                    can.rect(362.5, 515, 159, 25, fill=0, stroke=1)
               
            firmay = y
            if(y<320):
                can.line(200, 450 -y, 400, 450 -y)
                can.drawCentredString(300, 430-y, person.nombres+" "+person.apellido1+" "+person.apellido2)
            else:
                numPages+=1
                can.showPage()
                can.setFont("Montserrat", 12)
                can.line(200, 600 , 400, 600)
                can.drawCentredString(300, 585, person.nombres+" "+person.apellido1+" "+person.apellido2)
            
            can.save()
           
            new_pdf = PdfFileReader(nombre)
          
            #existing_pdf = PdfFileReader(ruta+"Formatos\\Reporte de Asistencia.pdf")
            #page = existing_pdf.getPage(0)
            #page.mergePage( new_pdf.getPage(0))
            output = PdfFileWriter()
            for i in range(numPages+1):
                if i==0:
                    existing_pdf = PdfFileReader(ruta+"Formatos/Reporte de Asistencia.pdf")
                else:
                    existing_pdf = PdfFileReader(ruta+"Formatos/Reporte de Asistencia Vacio.pdf")
                page = existing_pdf.getPage(0)
                page.mergePage( new_pdf.getPage(i))
                output.addPage(page)
            
            outputStream = open(nombre, "wb")
            output.write(outputStream)
            outputStream.close()
          
                 

    def get(self, request, *args, **kwargs):
        ruta =  settings.MEDIA_ROOT+"/"

        if 'bases' in kwargs:
            people = Person.objects.filter(Q(activo=True) & (Q(cat_contratacion__pk =1) | Q(cat_contratacion__pk =2)))
            dateInicio = datetime.datetime.strptime(self.kwargs['fechaInicio'], "%d-%m-%Y")
            merger = PdfFileMerger() 
            nombreReporteArchivo = "_General"   
            if 'fechaFin' in kwargs:
                dateFin = datetime.datetime.strptime(self.kwargs['fechaFin'], "%d-%m-%Y")
                #nombreReporteArchivo = person.matricula+"_"+person.nombres+" "+person.apellido1+" "+person.apellido2+"_"+dateInicio.strftime("%Y-%m-%d")+"__"+dateFin.strftime("%Y-%m-%d")
                rangoFecha = "Del día "+ dateInicio.strftime("%d-%m-%Y")+" al "+dateFin.strftime("%d-%m-%Y")
            
            else:
                #nombreReporteArchivo = person.matricula+"_"+person.nombres+" "+person.apellido1+" "+person.apellido2+"_"+dateInicio.strftime("%Y-%m-%d")
                rangoFecha = "Día "+dateInicio.strftime("%d-%m-%Y")
            #nombre= ruta+"Formatos\\Reporte de Asistencia"+nombreReporteArchivo+".pdf"
            for i, person in enumerate(people):
                self.create_pdf(ruta+"Formatos/Reporte de Asistencia"+str(i)+".pdf", person, dateInicio, dateFin, rangoFecha)
                merger.append(ruta+"Formatos/Reporte de Asistencia"+str(i)+".pdf")
            merger.write(ruta+"Formatos/Reporte de Asistencia"+nombreReporteArchivo+".pdf")
            merger.close()   

        else:
            person = Person.objects.get(pk=self.kwargs['pk'])
            dateInicio = datetime.datetime.strptime(self.kwargs['fechaInicio'], "%d-%m-%Y")
            if 'fechaFin' in kwargs:
                dateFin = datetime.datetime.strptime(self.kwargs['fechaFin'], "%d-%m-%Y")
                nombreReporteArchivo = person.matricula+"_"+person.nombres+" "+person.apellido1+" "+person.apellido2+"_"+dateInicio.strftime("%Y-%m-%d")+"__"+dateFin.strftime("%Y-%m-%d")
                rangoFecha = "Del día "+ dateInicio.strftime("%d-%m-%Y")+" al "+dateFin.strftime("%d-%m-%Y")
            
            else:
                nombreReporteArchivo = person.matricula+"_"+person.nombres+" "+person.apellido1+" "+person.apellido2+"_"+dateInicio.strftime("%Y-%m-%d")
                rangoFecha = "Día "+dateInicio.strftime("%d-%m-%Y")

            nombre= ruta+"Formatos/Reporte de Asistencia"+nombreReporteArchivo+".pdf"
            self.create_pdf(nombre, person, dateInicio, dateFin, rangoFecha) 
           
        return self.pdf_return(nombreReporteArchivo)

def revisarFecha(horario, fecha):
    try:
        result = horario.find(':')
        if  result != -1:
            horarioIn = horario[: 2].strip()
            print(horarioIn)
            if int(horarioIn) - fecha.hour  >= 0 :
                return 1
    except:
        return 0

def searchPerson(request):
    try:
        if request.is_ajax():
            now = datetime.datetime.now()
            person = Person.objects.get(matricula = request.POST['matricula'] )
            if person.activo == False:
                incidencia_data={"error":False,"welcome":"Baja","errorMessage":"Este usuario se encuentra dado de baja de la Institución" ,"base": False }
            else:    
                #&&  _lt Q(created_at__gt= now-timedelta(hours=4)) 
                incidenciaPrev = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=now.day, created_at__month = now.month, created_at__year = now.year)) 
                incidencia = Incidencia()
                incidencia.matriculaCredencial = person
                
                if not incidenciaPrev:
                    ni = person.matricula+ "_"+ person.nombres +" "+person.apellido1 + " "+ person.apellido2
                    img= savePhoto(request.POST['photo'] )
                    incidencia.created_at = now
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
                        incidencia.created_at = now
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

class IncidenciaToShow:  
    def __init__(self, fecha, idIn, Entrada, idOut, Salida, observacion):
        self.fecha = fecha  
        self.idIn = idIn  
        self.Entrada = Entrada
        self.idOut = idOut
        self.Salida = Salida 
        self.observacion= observacion 

class DetalleIncidencias(View):

    def get(self, request, *args, **kwargs):
        causaIncidencia = CausaIncidencia.objects.all()
        person = Person.objects.get(pk=self.kwargs['pk'])
        dateInicio = datetime.datetime.strptime(self.kwargs['fechaInicio'], "%d-%m-%Y")
        t = get_template('people/Incidencias/persona_modif_inci.html')
        list = []  
       
        if 'fechaFin' in kwargs:
            dateFin = datetime.datetime.strptime(self.kwargs['fechaFin'], "%d-%m-%Y")
            incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin+ timedelta(days = 1)]))
            i=0
            for n in range(int((dateFin - dateInicio).days)+1):
                incidencia = incidencias.filter(created_at__day=(dateInicio + timedelta(n)).day, created_at__month = (dateInicio + timedelta(n)).month, created_at__year = (dateInicio + timedelta(n)).year)
                observacion = " "
                if incidencia :
                    incidenciaOut = incidencia.latest('created_at')
                    if incidenciaOut.causa_incidencia:
                        observacion += incidenciaOut.causa_incidencia.nombre +" / "
                    print(incidenciaOut)
                    if incidencia.count()>1:
                        incidenciaIn = incidencia.earliest('created_at')
                        if incidenciaIn.causa_incidencia:
                            observacion += incidenciaIn.causa_incidencia.nombre +" / "
                        list.append( IncidenciaToShow(incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), observacion )) 
                    else:
                        fechaRevisada = 0
                        if person.cat_horario:
                            fechaRevisada = revisarFecha(person.cat_horario.nombre,incidenciaOut.created_at)
                       
                      
                        if fechaRevisada == 1:
                            list.append( IncidenciaToShow(incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", observacion )) 
                        else:
                            list.append(IncidenciaToShow(incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), observacion ) ) 
                        i+=1
            content = t.render(
            {
                'person': person, 
                'list': list,
                'fechaInicio': dateInicio.strftime("%d/%m/%Y"), 
                'fechaFin': dateFin.strftime("%d/%m/%Y"),
                'causaIncidencia': causaIncidencia,    
            })

           
        else:
            incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=dateInicio.day, created_at__month = dateInicio.month, created_at__year = dateInicio.year) )
            if incidencias.count()>1:
                incidenciaOut = incidencias.latest('created_at').created_at
                incidenciaIn = incidencias.earliest('created_at').created_at
                list.append( IncidenciaToShow( incidenciaIn.pk, incidenciaIn.created_at, incidenciaOut.pk, incidenciaOut.created_at) ) 
            elif incidencias.count()==0:
                print("NO hay información")
            else:
                incidenciaOut = incidencias.latest('created_at').created_at
                fechaRevisada = revisarFecha(person.cat_horario.nombre, incidenciaOut)  
                if fechaRevisada == 1:
                   list.append( IncidenciaToShow("null", "null", incidenciaOut.pk, incidenciaOut.created_at))
                else:
                    list.append( IncidenciaToShow( incidenciaOut.pk, incidenciaOut.created_at, "null", "null" ))  
            
            content = t.render(
            {
                'person': person, 
                'list': list,
                'fechaInicio': dateInicio.strftime("%d/%m/%Y"), 
                'causaIncidencia': causaIncidencia,    
            })
        return HttpResponse(content)

@csrf_exempt
def UpdateIncidencia(request):
    person =  Person.objects.get(pk=request.POST.get("person"))
    data=request.POST.get("data")
    dict_data=json.loads(data)
    if person:
        try:
            for dic_single in dict_data:
                fecha = dic_single['fecha']
                idEntrada = dic_single['idEntrada']
                idSalida = dic_single['idSalida']
                entrada = dic_single['entrada']
                salida = dic_single['salida']
                if idSalida != "null":
                    incidenciaSalida = Incidencia.objects.get(pk=idSalida)
                    if incidenciaSalida.created_at.strftime("%H:%M:%S") !=salida:
                        incidenciaSalida.created_at = datetime.datetime.strptime(fecha+" "+salida, "%d/%m/%Y %H:%M:%S")
                        incidenciaSalida.save()
                elif salida :
                    dateS = datetime.datetime.strptime(fecha+" "+salida, "%d/%m/%Y %H:%M")
                    incidenciaSalida=Incidencia( matriculaCredencial = person, modificacion= True, created_at = dateS)
                    incidenciaSalida.save()
                if idEntrada != "null" :
                    incidenciaEntrada = Incidencia.objects.get(pk=idEntrada)
                    if incidenciaEntrada.created_at.strftime("%H:%M:%S") !=entrada:
                        incidenciaEntrada.created_at = datetime.datetime.strptime(fecha+" "+entrada, "%d/%m/%Y %H:%M:%S")
                        incidenciaEntrada.save()
                elif entrada:
                    dateE = datetime.datetime.strptime(fecha+" "+entrada, "%d/%m/%Y %H:%M")
                    incidenciaEntrada=Incidencia( matriculaCredencial = person, modificacion= True, created_at = dateE)
                    incidenciaEntrada.save()
                stuent_data={"error":False,"errorMessage":"Updated Successfully"}
            return JsonResponse(stuent_data,safe=False)
        except:
            stuent_data={"error":True,"errorMessage":"Failed to Update Data"}
            return JsonResponse(stuent_data,safe=False)
   
@csrf_exempt
def AddIncidencia(request):
    person =  Person.objects.get(pk=request.POST.get("person"))
    fecha=  datetime.datetime.strptime(request.POST.get("fechaIncidencia"), "%Y-%m-%dT%H:%M")
    tipo = CausaIncidencia.objects.get(id=request.POST.get("tipoIncidencia"))
    if person:
        try:
            incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=fecha.day, created_at__month = fecha.month, created_at__year = fecha.year) )
            newIncidencia = Incidencia(matriculaCredencial=person, created_at=fecha, causa_incidencia= tipo)
            newIncidencia.save()
            if incidencias.count()>1:
                incidenciaOut = incidencias.latest('created_at')
                incidenciaIn = incidencias.earliest('created_at')
                resultadoHtml= "<tr><td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>"+ str(incidenciaIn.pk) +"</td><td class='editable' data-type='entrada'>" + incidenciaIn.created_at.strftime("%H:%M:%S") + " </td><td style='display:none' >"+ str(incidenciaOut.pk) + "</td> <td class='editable' data-type='salida'>"+ incidenciaOut.created_at.strftime("%H:%M:%S")+"</td><td>"+tipo.nombre+"</td><td><button class='btn btn-default btn-xs' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
            else:
                if tipo.pk ==1:
                    resultadoHtml= "<tr><td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>"+ str(newIncidencia.pk) +"</td><td class='editable' data-type='entrada'>" + newIncidencia.created_at.strftime("%H:%M:%S") + " </td><td style='display:none' >null</td> <td class='editable' data-type='salida'>Sin Registro</td><td>"+tipo.nombre+"</td><td><button class='btn btn-default btn-xs' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
                else:
                    resultadoHtml= "<tr><td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>null</td><td class='editable' data-type='entrada'>Sin Registro</td><td style='display:none' >"+ str(newIncidencia.pk) + "</td> <td class='editable' data-type='salida'>"+ newIncidencia.created_at.strftime("%H:%M:%S")+"</td><td>"+tipo.nombre+"</td><td><button class='btn btn-default btn-xs' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
          
            stuent_data={"error":False,"errorMessage":"Updated Successfully", "tabla":resultadoHtml}
            return JsonResponse(stuent_data,safe=False)
        except Exception as e:
            print(e)
            stuent_data={"error":True,"errorMessage":"Failed to Update Data"}
            return JsonResponse(stuent_data,safe=False)

@csrf_exempt
def DeleteIncidencia(request):
    try:
        if(request.POST.get("idHrEntrada")!="null"):
            incidencia1 = Incidencia.objects.get(pk=request.POST.get("idHrEntrada"))
            incidencia1.delete()
        if(request.POST.get("idHrSalida")!="null"):
            incidencia2 = Incidencia.objects.get(pk=request.POST.get("idHrSalida"))
            incidencia2.delete()
        incidencia_data={"error":False,"errorMessage":"Deleted Successfully"}
        return JsonResponse(incidencia_data,safe=False)
    except Exception as e:
        print(e)
        incidencia_data={"error":True,"errorMessage":"Failed to Delete Data"}
        return JsonResponse(incidencia_data,safe=False)

        

@csrf_exempt
def GetPersonasIncidencia(request):
  
    q=request.GET.get("q")
    queryset = Person.objects.filter(activo=True).order_by('apellido1')
    if q and q !=" ":
        q =q.split(" ")
        query = reduce(operator.and_, ((Q(nombres__unaccent__icontains=item) | Q(apellido1__unaccent__icontains=item) | Q(apellido2__unaccent__icontains=item) | Q(matricula__icontains=item) ) for item in q))
        queryset = queryset.filter(query)     
   
    t = get_template('people/Incidencias/incidencia_search.html')
    content = t.render(
    {
        'people': queryset,
          
    })
    return HttpResponse(content)       

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