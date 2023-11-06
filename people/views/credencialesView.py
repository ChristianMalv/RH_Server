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
from people.models import AreaOrganigrama, Compensacion, Compensaciones, Person, Incidencia, Bajas, AreaInterna, CausaIncidencia, ServicioSocial
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
from reportlab.lib.pagesizes import letter
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
from pyreportjasper import PyReportJasper
from django.http import FileResponse, Http404
#import vlc

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
       
        


    def drawName(self, pdf, texto, size):
        pdf.setFont("Montserrat-Bold", size)
        pdf.setFillColorRGB(1,1,1)   
        y = 750
        wrapper = textwrap.TextWrapper(width=13)
        word_list = wrapper.wrap(text=texto)
        for element in word_list:
            print(element)
            pdf.drawCentredString(42, y, element)
            y -= (2 +size)    

    def drawMatricula(self, pdf, texto, ad):
        pdf.setFont("Montserrat-Bold", 10)
        pdf.setFillColorRGB(1,1,1)   
        pdf.drawCentredString(80, 610, texto)
        #
        pdf.setFillColorRGB(166/255,30/255,61/255)   
        pdf.setFont("Montserrat-Bold", 12)
        if ad == None:
            pdf.drawCentredString(40, 782, 'GAFETE')   
        else:
            pdf.setFont("Montserrat-Bold", 10)
            pdf.drawCentredString(40, 682, ad)    
    def drawArea(self, pdf, texto, offset):
        pdf.setFont("Montserrat-Bold", 10)
        pdf.setFillColorRGB(1,1,1) 
        y = 670 + offset
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
        if 'sersoc' in kwargs:
            sersoc= self.kwargs['sersoc']
        else: 
            sersoc= None
        #response = HttpResponse(content_type='application/pdf')
        if sersoc:
            sersoc = ServicioSocial.objects.get(pk=sersoc)
            CreateJsonCredencial(person, sersoc)
            json_to_Credencialpdf(sersoc)
        else:
            CreateJsonCredencial(person, None)
            json_to_Credencialpdf(None)
        buffer = BytesIO()
        #
        pdfTexto = settings.MEDIA_ROOT+ '/Formatos/Credencial/CredencialFinal.pdf'
        # pdf = canvas.Canvas(pdfTexto)
        # pdf.setFont("Montserrat", 10)
        #pdf = canvas.Canvas(buffer)
        #self.foto(pdf, person)
        #self.cabecera(pdf)
        # if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
        #     self.drawName(pdf, person.nombres + ' ' + person.apellido1 + ' ' + person.apellido2, 10)
        #     self.drawArea(pdf, person.puesto, 0)
        #     self.drawMatricula(pdf, person.matricula, None)
        # else:
        #     self.drawName(pdf, 'Prestador(a) de Servicios Profesionales por Honorarios', 8)
        #     self.drawArea(pdf, 'Dirección General @prende.mx', 0)
        #     self.drawMatricula(pdf, person.matricula, 'De Control de Acceso a las Instalaciones de la SEP')    
       
        #self.drawSubarea(pdf, person.cat_area_org.nombre )
        #Con show page hacemos un corte de página para pasar a la siguiente
        # pdf.save()
        
        # pdf = canvas.Canvas(settings.MEDIA_ROOT+ '/Formatos/Credencial/CredencialReverso.pdf')
        # self.codigoQr(pdf, person.matricula)
        # if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
        #     self.firma(pdf, 'Agradecemos a las autoridades civiles y militares, otorguen a la persona portadora del presente, todas las facilidades para el mejor desempeño de sus funciones. Esta credencial es propiedad de la Dirección General @prende.mx, es intrasferible y tendrá vigencia en el periodo estipulado.', 6)
        # else:
        #     self.firma(pdf, 'Agradecemos a las autoridades civiles y militares, otorguen a la persona portadora del presente, todas las facilidades para la prestación de sus servicios por honorarios. Este gafete de control de acceso a las instalaciones de la SEP es propiedad de la Dirección General @prende.mx, es intransferible y será responsabilidad de la persona prestadora de servicios profesionales por honorarios impedir o evitar su divulgación, sustracción, destrucción, ocultamiento o inutilización indebidos.', 4)
        # pdf.save()

        rev_pdf = PdfFileReader(settings.MEDIA_ROOT+ '/Formatos/Credencial/CredencialReverso.pdf')
       # new_pdf = PdfFileReader(pdfTexto)
        existing_pdf = PdfFileReader(settings.MEDIA_ROOT+ '/Formatos/Credencial/Credencial.pdf' )
        page = existing_pdf.getPage(0)
        page1 = rev_pdf.getPage(0)
        output = PdfFileWriter()
       # page.mergePage( new_pdf.getPage(0))
        #page1.mergePage(new_pdf.getPage(1))
        output.addPage(page)
        output.addPage(page1)
        outputStream = open(pdfTexto, "wb")
        output.write(outputStream)
        outputStream.close()    

        #pdf = buffer.getvalue()
        # buffer.close()
        #response.write(pdfTexto)
        return pdf_view(pdfTexto, 'credencial')
   
   
    def codigoQr(self, pdf, texto):
        img = qrcode.make(texto)
        f = open(settings.MEDIA_ROOT+'/imagenes/Matricula_'+ texto +'.png', "wb")
        img.save(f)
        f.close()
        pdf.drawImage(settings.MEDIA_ROOT+'/imagenes/Matricula_'+ texto +'.png', 30, 750, 100, 94,preserveAspectRatio=True)

    def firma(self, pdf, texto, size):
        pdf.setFont("Montserrat", 8)
        pdf.setFillColorRGB(0,0,0) 
        pdf.drawCentredString(80, 742, 'AUTORIZA')
        pdf.drawImage(settings.MEDIA_ROOT+'/imagenes/firma.png', 55, 680, 70, 70,preserveAspectRatio=True) 
        pdf.setFont("Montserrat", size)
        wrapper = textwrap.TextWrapper(width=55-size)
        word_list = wrapper.wrap(text=texto)
        y = 680
        for element in word_list:
            print(element)
            pdf.drawCentredString(81, y, element)
            y -= (1 +size)  
        pdf.setFont("Montserrat", 6)  
        pdf.drawCentredString(80, 620, 'VIGENCIA: DICIEMBRE 2024')

    def foto(self, pdf, person):
        archivo_imagen_fondo = settings.MEDIA_ROOT+'/imagenes/fondoverdeconcorte.png'
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


    
def CreateJsonCredencial(person, sersoc):
    data = {}
    data['credencial']=[]
    imagen = person.imagen_base64
    if not len(imagen) == 0:
        filename = settings.MEDIA_ROOT+'/Formatos/Credencial/matricula.jpg'
        imagen = imagen.replace('data:image/png;base64,','')
        image_64_decode = base64.b64decode(imagen) 
        image_result = open(filename, 'wb') # create a writable image and write the decoding result
        image_result.write(image_64_decode)
    else :
        filename=settings.MEDIA_ROOT+'/imagenes/nofoto.png'
    img = qrcode.make(person.matricula)
    f = open(settings.MEDIA_ROOT+'/Formatos/Credencial/qr.png', "wb")
    img.save(f)
    f.close()
    if person.cat_contratacion.pk == 5:
        cargo = person.puesto + '\n'+ 'Prestador(a) de Servicios Profesionales por Honorarios'
        gafete = 'Gafete de control de acceso a las instalaciones de la SEP'
        frase =  'Agradecemos a las autoridades civiles y militares, otorguen a la persona portadora del presente, todas las facilidades para la prestación de sus servicios por honorarios. Este gafete de control de acceso a las instalaciones de la SEP es propiedad de la Dirección General @prende.mx, es intransferible y será responsabilidad de la persona prestadora de servicios profesionales por honorarios impedir o evitar su divulgación, sustracción, destrucción, ocultamiento o inutilización indebidos.'
        vigencia = ''
    elif person.cat_contratacion.pk == 6:
        cargo = 'Servicio Social en '+ person.cat_area_org.nombre
        vigencia = sersoc.periodo
        gafete = ''
        frase = ''
        
    else:
        cargo = person.puesto
        gafete = 'GAFETE'
        frase = 'Agradecemos a las autoridades civiles y militares, otorguen a la persona portadora del presente, todas las facilidades para el mejor desempeño de sus funciones. Esta credencial es propiedad de la Dirección General @prende.mx, es intrasferible y tendrá vigencia en el periodo estipulado.'
        vigencia = 'VIGENCIA: DICIEMBRE 2025'
    
    data['credencial'].append({'Photo': filename,
                               'Nombre': person.nombres + ' ' + person.apellido1 + ' ' + person.apellido2,
                               'cargo':cargo,
                               'Matricula': person.matricula,
                               'gafete': gafete,
                  'qr': settings.MEDIA_ROOT+'/Formatos/Credencial/qr.png' ,
                'firma': settings.MEDIA_ROOT+'/imagenes/firma.png', 
                'frase': frase,
                'logoaprende': settings.MEDIA_ROOT+'/imagenes/LogoFull.png',
                'bg': settings.MEDIA_ROOT+'/imagenes/fondoguinda.png',
                'firma': settings.MEDIA_ROOT+'/imagenes/FirmaR.png',
                'vigencia': vigencia,
                })
    
        
    with open(settings.MEDIA_ROOT+ '/Formatos/Credencial/dataCredencial.json', 'w', encoding='utf8') as file:
        json.dump(data, file, ensure_ascii=False) 



def pdf_view(file, texto):
    with open(file, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename='+texto+'.pdf'
    return response


@csrf_exempt      
def json_to_Credencialpdf(sersoc):
    if sersoc: 
        input_file = settings.MEDIA_ROOT+ '/Formatos/Credencial/Credencialss.jasper'
    else:
        input_file = settings.MEDIA_ROOT+ '/Formatos/Credencial/Credencial.jasper'
    conn = {
      'driver': 'json',
      'data_file': settings.MEDIA_ROOT+ '/Formatos/Credencial/dataCredencial.json',
      'json_query': 'credencial'
   }
    outputFile= settings.MEDIA_ROOT+ '/Formatos/Credencial/Credencial.pdf' 
    pyreportjasper = PyReportJasper()
    pyreportjasper.config(
      input_file,
      output_file=outputFile,
      output_formats=["pdf"],
      db_connection=conn
   )
    
    
    pyreportjasper.process_report()

    if sersoc: 
        input_file = settings.MEDIA_ROOT+ '/Formatos/Credencial/Credencial1ss.jasper'
    else:
        input_file = settings.MEDIA_ROOT+ '/Formatos/Credencial/Credencial1.jasper'
    conn = {
      'driver': 'json',
      'data_file': settings.MEDIA_ROOT+ '/Formatos/Credencial/dataCredencial.json',
      'json_query': 'credencial'
   }
    outputFile= settings.MEDIA_ROOT+ '/Formatos/Credencial/CredencialReverso.pdf' 
    pyreportjasper = PyReportJasper()
    pyreportjasper.config(
      input_file,
      output_file=outputFile,
      output_formats=["pdf"],
      db_connection=conn
   )
    
    
    pyreportjasper.process_report()


    print('Result is the file below.')
    if os.path.isfile(outputFile):
        print('Report generated successfully!')
    #     with open(outputFile, 'rb') as pdf:
    #        response = HttpResponse(pdf.read(),content_type='application/pdf')
    #        response['Content-Disposition'] = 'filename=Credencial.pdf'
  #     return response




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
    queryset = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6)).order_by('created_at')
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
    def form_valid(self, form):
        self.object = form.save()
        if self.object.vacaciones_extra == True:
            now = datetime.datetime.now()
            self.object.date_update_vacaciones = now
            self.object.save()
        else:
            self.object.save()
        
        return HttpResponseRedirect(self.get_success_url())


        
   

class PersonCheckView(CreateView):
    model = Incidencia
    form_class = IncidenciaForm
    template_name = 'people/person_form_incidencia.html'
    success_url = reverse_lazy('person_list')
   



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