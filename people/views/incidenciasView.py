
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.views.generic import View
from people.models import AreaOrganigrama, Compensacion, Compensaciones, Person, Incidencia, Bajas, AreaInterna, CausaIncidencia, MultipleOrganigrama, Ayudas, PersonaAyuda, PeriodosVacaciones
from django.conf import settings
from reportlab.pdfgen import canvas
import textwrap, operator, base64, json, datetime
from django.db.models import Q
from datetime import timedelta
from functools import reduce
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django.template.loader import get_template
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from django.db.models import Count
from django.db.models.aggregates import Max
from django.http import FileResponse, Http404
import math
from django.core.files.base import ContentFile
from django.shortcuts import redirect
from django.core.paginator import Paginator
from .ldapView import get_attributes
#import vlc
@method_decorator(login_required, name='dispatch')
class PersonInciListView(ListView):
    model = Person
    paginate_by = 50

    def get(self, request, *args, **kwargs):
        queryset = Person.objects.filter( Q(activo=True) & ~Q(cat_contratacion__pk =6) )
        causaIncidencia = CausaIncidencia.objects.filter(isVisible = True)
        
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
                'people': queryset, 
                'causaIncidencia': causaIncidencia, 
            }
        return render(request, 'people/Incidencias/inci_list.html' , content)

class IncidenciaConsulta(View):
    def get(self, request, *args, **kwargs):
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
            }
        return render(request, 'people/inci/consulta_incidencia.html' , content)

def ValidatePersonIncidencia(request):
    try:
        now = datetime.datetime.now()
        #if request.is_ajax():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest': 
            matriculaInput = request.POST['matricula']
            person = Person.objects.get(matricula =matriculaInput.upper()  )
            if person.activo == False:
                incidencia_data={"error":False,"welcome":"Baja","errorMessage":"Este usuario no pertenece a la Dirección" ,"base": False }
            elif (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):    
                anio = int( person.curp[4:6])
                if ( anio + 2000 ) > now.year:
                    anio = anio + 1900
                else:
                    anio = anio + 2000
                print(anio)
                print(request.POST['fecha'])
                print(person.curp[8:10] + '/'+ person.curp[6:8] +'/'+ str(anio))
                if person.curp[8:10] + '/'+ person.curp[6:8] +'/'+ str(anio)  == request.POST['fecha']:
                   incidencia_data={"error":True,"welcome":"Consultando","errorMessage":"Consultando a la persona", "persona": person.matricula , "base": True }
                else :
                  incidencia_data={"error":False,"welcome":"Verificar Información","errorMessage":"Los datos ingresados son Incorrectos ", "base": True }
            else:
                incidencia_data={"error":False,"welcome":"Baja","errorMessage":"No se encontró la matrícula" ,"base": False }
              
            return JsonResponse(incidencia_data,safe=True, status=200)
    except Exception as e:
        print(e)          
        return HttpResponse(status=404)

class DetailPersonIncidencia(View):
     def get(self, request, *args, **kwargs):
        diasExtra = 0
        matriculaInput = self.kwargs['pk']
        person = Person.objects.get(matricula=  matriculaInput.upper())
        periodo1 = PeriodosVacaciones.objects.get(idPeriodo= 1)
        periodo2 = PeriodosVacaciones.objects.get(idPeriodo= 2)
        diasEco = getDiasEconomicos(person)
        diasVaca1 = getVacaciones(person, periodo1.periodo.pk)
        diasVaca2 = getVacaciones(person, periodo2.periodo.pk)
        if person.vacaciones_extra:
            diasExtra = 10 - getVacaciones(person, 6)
        content = { #t.render(
                'person': person, 
                'diasEco': diasEco,
                'diasVaca1': diasVaca1, 
                'diasVaca2': diasVaca2, 
                'diasExtra': diasExtra,
                'periodo1': periodo1.periodo,
                'periodo2': periodo2.periodo,
            } 
        return render(request, 'people/inci/detalle_incidencia.html' , content)    

class ReporteIncidenciasPDF(View):

    # pdfmetrics.registerFont(TTFont('Montserrat', settings.MEDIA_ROOT+'/montserrat/Montserrat-Light.ttf'))
    # pdfmetrics.registerFont(TTFont('Montserrat-Bold', settings.MEDIA_ROOT+'/montserrat/Montserrat-Bold.ttf'))  
    

    def pdf_return(self,nombre):
        filename = settings.MEDIA_ROOT+"/"+"Formatos/Reporte de Asistencia"+nombre+".pdf"
        with open(filename, 'rb') as pdf:
            response = HttpResponse(pdf.read(),content_type='application/pdf')
            response['Content-Disposition'] = 'filename=some_file.pdf'
            return response

    def create_pdf(self, nombre, person, dateInicio, dateFin, rangoFecha):
            ruta =  settings.MEDIA_ROOT+"/"
            nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
            can = canvas.Canvas(nombre) 
            can.setFillColorRGB(0, 0, 0)
            can.setFont("Montserrat", 12)
            #can.drawCentredString(320, 666, "Reporte de Asistencia")
            can.drawString(150, 670, person.cat_area_org.nombre)
            can.drawString(150, 653, rangoFecha)
            can.drawString(150, 634, person.nombres+" "+person.apellido1+" "+person.apellido2)
            can.drawString(150, 616, person.rfc)
            can.drawString(150, 598, person.matricula)
            if person.cat_horario :
                can.drawString(150, 579, person.cat_horario.nombre) 
            else:
                can.drawString(150, 579, "-----") 
            #can.setFillColorRGB(0, 1, 1)
            can.setLineWidth(0.5)    

            if dateFin: #'fechaFin' in kwargs:
                incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin+ timedelta(1)]))
                numPages=0
                y=0
                rango=0
                horasfinales = 0
                for i in range(int((dateFin - dateInicio).days)+1):
                    if y>=( 375 - (60*rango)):
                        numPages+=1
                        can.showPage()
                        can.setFont("Montserrat", 12)
                    if numPages>0:
                        rango=1
                    
                    y = ((25*i)-(375*numPages)) - (180*rango)
                    can.rect(18, (494 - (y)), 63, 25, fill=0, stroke=1)
                    can.rect(81, (494 - (y)), 78.5, 25, fill=0, stroke=1)
                    can.rect(159.5, (494 - (y)), 141.5, 25, fill=0, stroke=1)
                    can.rect(300.5, (494 - (y)), 128.5, 25, fill=0, stroke=1)
                    can.rect(429, (494 - (y)), 105.5, 25, fill=0, stroke=1)
                    can.rect(534.5, (494 - (y)), 60.5, 25, fill=0, stroke=1)
                    can.setFont("Montserrat", 10)
                    can.drawString(84, 507-(y), (dateInicio + timedelta(i)).strftime("%d-%m-%Y") )
                    can.drawString(20, 507-(y), nombreDias[int((dateInicio + timedelta(i)).strftime("%w"))] )
                    can.setFont("Montserrat", 12) 

                    incidencia = incidencias.filter(created_at__day=(dateInicio + timedelta(i)).day, created_at__month = (dateInicio + timedelta(i)).month, created_at__year = (dateInicio + timedelta(i)).year)
                    if incidencia :
                        observacion =" "
                        incidenciaOut = incidencia.latest('created_at')
                        print(incidenciaOut)
                        if incidenciaOut.causa_incidencia != None:
                            if incidenciaOut.causa_incidencia.pk == 1 or incidenciaOut.causa_incidencia.pk ==2: 
                               observacion = incidenciaOut.causa_incidencia.nombre
                    

                        if incidencia.count()>1:
                            incidenciaIn = incidencia.earliest('created_at')
                            if incidenciaOut.causa_incidencia != None:
                                print(observacion)
                                if incidenciaOut.causa_incidencia.pk != 1 or incidenciaOut.causa_incidencia.pk !=2 or incidenciaOut.causa_incidencia.pk !=10 : 
                                    can.drawCentredString(355, 507-(y), "--:--" )
                                    can.drawCentredString(230, 507-(y), "--:--" )
                                    can.drawCentredString(560, 507-(y), "-")
                                    observacion = incidenciaOut.causa_incidencia.nombre
                            elif incidenciaIn.causa_incidencia != None:
                                    if incidenciaIn.causa_incidencia.pk != 1 or incidenciaIn.causa_incidencia.pk !=2 or incidenciaIn.causa_incidencia.pk !=10:
                                        can.drawCentredString(355, 507-(y), "--:--" )
                                        can.drawCentredString(230, 507-(y), "--:--" )
                                        can.drawCentredString(560, 507-(y), "-")
                                        observacion = incidenciaIn.causa_incidencia.nombre
                            else:    
                                    can.drawCentredString(355, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                    can.drawCentredString(230, 507-(y), incidenciaIn.created_at.strftime("%H:%M:%S") )
                                    horas =  CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
                                   
                                    if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
                                        horasfinales += horas
                                    can.drawCentredString(560, 507-(y), str(horas))
                            
                        else:
                            incicenciaFirst = incidencia.first()
                            can.drawCentredString(560, 507-(y), "-")
                            if  incicenciaFirst.causa_incidencia != None:
                                if incidenciaOut.causa_incidencia.pk != 1 or incidenciaOut.causa_incidencia.pk !=2 or incidenciaOut.causa_incidencia.pk !=10: 
                                    can.drawCentredString(230, 507-(y), "--:--" )
                                    can.drawCentredString(355, 507-(y), "--:--")
                                    observacion = incidenciaOut.causa_incidencia.nombre
                                
                            elif person.cat_horario and person.cat_horario.pk !=14:
                                fechaRevisada = revisarFecha(person.cat_horario.nombre,incidenciaOut.created_at)
                                if fechaRevisada == 1:
                                    can.drawCentredString(230, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                    can.drawCentredString(355, 507-(y), "Sin Registro")
                                else:
                                    can.drawCentredString(230, 507-(y), "Sin Registro")
                                    can.drawCentredString(355, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                            else:
                                    can.drawCentredString(230, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                        
                        can.setFont("Montserrat", 10)      
                        can.drawString(430, 507-(y), observacion)

                        
                        can.setFont("Montserrat", 12)    
                can.rect(534.5, (469 - (y)), 60.5, 25, fill=0, stroke=1) 
                if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
                    can.setFont("Montserrat-Bold", 12) 
                    can.drawString(418, 475-(y), "Total Horas Extras")
                    can.drawCentredString(560, 475-(y), str(horasfinales))

                    
            else:
                incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=dateInicio.day, created_at__month = dateInicio.month, created_at__year = dateInicio.year) )
                incidenciaOut = incidencias.latest('created_at')
                can.drawString(292, 517, incidenciaOut.created_at.strftime("%H:%M:%S") )
               
                if incidencias.count()>1:
                    incidenciaIn = incidencias.earliest('created_at')
                    can.setFont("Montserrat", 10)
                    can.drawString(20, 507-(y), nombreDias[int((dateInicio + timedelta(i)).strftime("%w"))] )
                    can.drawString(84, 507, incidenciaIn.created_at.strftime("%d-%m-%Y") )
                    can.drawString(210, 507, incidenciaIn.created_at.strftime("%H:%M:%S") )
                    can.setFont("Montserrat", 12)
                    can.rect(18, (494 - (y)), 63, 25, fill=0, stroke=1)
                    can.rect(81, (494 - (y)), 78.5, 25, fill=0, stroke=1)
                    can.rect(159.5, (494 - (y)), 141.5, 25, fill=0, stroke=1)
                    can.rect(300.5, (494 - (y)), 128.5, 25, fill=0, stroke=1)
                    can.rect(429, (494 - (y)), 105.5, 25, fill=0, stroke=1)
                    can.rect(534.5, (494 - (y)), 60.5, 25, fill=0, stroke=1)
               
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
                    existing_pdf = PdfFileReader(ruta+"Formatos/Reporte de Asistencia v2.pdf")
                else:
                    existing_pdf = PdfFileReader(ruta+"Formatos/Reporte de Asistencia Vacio v2.pdf")
                page = existing_pdf.getPage(0)
                page.mergePage( new_pdf.getPage(i))
                output.addPage(page)
            
            outputStream = open(nombre, "wb")
            output.write(outputStream)
            outputStream.close()

    def printObs(self, can, texto, y):
        if len(texto) > 19:
            space = texto.find(' ', 15)
            if space > 0:
                subcadena = texto[0:space]
                can.drawString(430, y, subcadena)
                y -= 10
                subcadena = texto[space:]
                can.drawString(430, y,  subcadena.strip())
            else:
                can.drawString(430, y, texto ) 
        else:
            can.drawString(430, y, texto ) 
                   

    def create_pdfv2(self,nombre, person, dateInicio, dateFin, rangoFecha):
        ruta =  settings.MEDIA_ROOT+"/"
        nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
        can = canvas.Canvas(nombre) 
        can.setFillColorRGB(0, 0, 0)
        can.setFont("Montserrat", 12)
        can.drawString(150, 670, person.cat_area_org.nombre)
        can.drawString(150, 653, rangoFecha)
        can.drawString(150, 634, person.nombres+" "+person.apellido1+" "+person.apellido2)
        can.drawString(150, 616, person.rfc)
        can.drawString(150, 598, person.matricula)
        if person.cat_horario :
            can.drawString(150, 579, person.cat_horario.nombre) 
        else:
            can.drawString(150, 579, "-----") 
            #can.setFillColorRGB(0, 1, 1)
        can.setLineWidth(0.5)
        if dateFin:
            incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin+ timedelta(days = 1)]))
            numPages=0
            y=0
            rango=0
            horasfinales = 0
            for i in range(int((dateFin - dateInicio).days)+1):
                if y>=( 375 - (60*rango)):
                    numPages+=1
                    can.showPage()
                    can.setFont("Montserrat", 12)
                if numPages>0:
                    rango=1
                    
                y = ((25*i)-(375*numPages)) - (180*rango)
                if(numPages>1):
                    y-=(100)*(numPages-1)
                can.rect(18, (494 - (y)), 63, 25, fill=0, stroke=1)
                can.rect(81, (494 - (y)), 78.5, 25, fill=0, stroke=1)
                can.rect(159.5, (494 - (y)), 141.5, 25, fill=0, stroke=1)
                can.rect(300.5, (494 - (y)), 128.5, 25, fill=0, stroke=1)
                can.rect(429, (494 - (y)), 105.5, 25, fill=0, stroke=1)
                can.rect(534.5, (494 - (y)), 60.5, 25, fill=0, stroke=1)
                can.setFont("Montserrat", 10)
                can.drawString(84, 507-(y), (dateInicio + timedelta(i)).strftime("%d-%m-%Y") )
                can.drawString(20, 507-(y), nombreDias[int((dateInicio + timedelta(i)).strftime("%w"))] )
                #can.setFont("Montserrat", 12) 


                incidencia = incidencias.filter(created_at__day=(dateInicio + timedelta(i)).day, created_at__month = (dateInicio + timedelta(i)).month, created_at__year = (dateInicio + timedelta(i)).year)
                if incidencia :
                    incidenciaOut = incidencia.latest('created_at')
                    print(incidenciaOut)
                    if incidencia.count()>1:
                        incidenciaIn = incidencia.earliest('created_at')
                        if  incidenciaIn.causa_incidencia != None : 
                            if incidenciaIn.causa_incidencia.pk != 1 and incidenciaIn.causa_incidencia.pk !=2 and incidenciaIn.causa_incidencia.pk !=10 :
                                can.drawCentredString(230, 507-(y), "--:--" )
                                can.drawCentredString(355, 507-(y), "--:--" )
                                #can.drawString(430, 507-(y), incidenciaIn.causa_incidencia.nombre)
                                self.printObs(can, incidenciaIn.causa_incidencia.nombre, 507-(y))
                                can.drawCentredString(560, 507-(y), "-")
                                
                                #list.append( IncidenciaToShow(nombreDias[int( incidenciaIn.created_at.strftime("%w"))] ,  incidenciaIn.created_at.strftime("%d/%m/%Y"),  incidenciaIn.pk, "--:--",  incidenciaIn.pk, "--:--",  incidenciaIn.causa_incidencia.nombre , "-")) 
                            else:
                                #list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), incidenciaIn.causa_incidencia.nombre, CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at )  )) 
                                can.drawCentredString(230, 507-(y), incidenciaIn.created_at.strftime("%H:%M:%S") )
                                can.drawCentredString(355, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                #can.drawString(430, 507-(y), incidenciaIn.causa_incidencia.nombre )
                                self.printObs(can, incidenciaIn.causa_incidencia.nombre, 507-(y))
                                horas = CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
                                can.drawCentredString(560, 507-(y), str(horas))
                                if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
                                    horasfinales += horas
                        else:
                            #list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ", CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at ) )) 
                            can.drawCentredString(230, 507-(y), incidenciaIn.created_at.strftime("%H:%M:%S") )
                            can.drawCentredString(355, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                            can.drawString(430, 507-(y)," ")
                            horas = CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
                            can.drawCentredString(560, 507-(y), str(horas))
                            if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
                                    horasfinales += horas
                    else:
                        incicenciaFirst = incidencia.first()
                        fechaRevisada = 0
                        if person.cat_horario:
                            fechaRevisada = revisarFecha(person.cat_horario.nombre,incidenciaOut.created_at)


                        if  incicenciaFirst.causa_incidencia != None :
                            if incicenciaFirst.causa_incidencia.pk != 1 and  incicenciaFirst.causa_incidencia.pk !=2 and incicenciaFirst.causa_incidencia.pk !=10 :
                                #list.append( IncidenciaToShow(nombreDias[int( incicenciaFirst.created_at.strftime("%w"))] ,  incicenciaFirst.created_at.strftime("%d/%m/%Y"),  incicenciaFirst.pk, "--:--",  incicenciaFirst.pk, "--:--",  incicenciaFirst.causa_incidencia.nombre , "-")) 
                                can.drawCentredString(230, 507-(y), "--:--" )
                                can.drawCentredString(355, 507-(y), "--:--" )
                                #can.drawString(430, 507-(y), incicenciaFirst.causa_incidencia.nombre )
                                self.printObs(can, incicenciaFirst.causa_incidencia.nombre, 507-(y))
                                can.drawCentredString(560, 507-(y), "-")
                            elif fechaRevisada == 1:
                                #list.append( IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] , incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", incicenciaFirst.causa_incidencia.nombre,  "-" )) 
                                can.drawCentredString(230, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                can.drawCentredString(355, 507-(y), "Sin registro" )
                                #can.drawString(430, 507-(y), incicenciaFirst.causa_incidencia.nombre )
                                self.printObs(can, incicenciaFirst.causa_incidencia.nombre, 507-(y))
                                can.drawCentredString(560, 507-(y), "-")
                            else:
                                #list.append(IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] ,  incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), incicenciaFirst.causa_incidencia.nombre,  "-" ) ) 
                                can.drawCentredString(230, 507-(y), "Sin Registro" )
                                can.drawCentredString(355, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                #can.drawString(430, 507-(y), incicenciaFirst.causa_incidencia.nombre )
                                self.printObs(can, incicenciaFirst.causa_incidencia.nombre, 507-(y))
                                can.drawCentredString(560, 507-(y), "-")
                        else:
                            if fechaRevisada == 1:
                                #list.append( IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] , incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", " ",  "-" )) 
                                can.drawCentredString(230, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                can.drawCentredString(355, 507-(y), "Sin Registro" )
                                can.drawString(430, 507-(y), " " )
                                can.drawCentredString(560, 507-(y), "-")
                            else:
                                #list.append(IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] ,  incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ",  "-" ) ) 
                                can.drawCentredString(230, 507-(y), "Sin Registro" )
                                can.drawCentredString(355, 507-(y), incidenciaOut.created_at.strftime("%H:%M:%S") )
                                can.drawString(430, 507-(y), " ")
                                can.drawCentredString(560, 507-(y), "-")
                            i+=1
                    can.setFont("Montserrat", 12)
                can.rect(534.5, (469 - (y)), 60.5, 25, fill=0, stroke=1) 
            if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2):
                can.setFont("Montserrat-Bold", 12) 
                can.drawString(418, 475-(y), "Total Horas Extras")
                can.drawCentredString(560, 475-(y), str(horasfinales))


        else:
            incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=dateInicio.day, created_at__month = dateInicio.month, created_at__year = dateInicio.year) )
            if incidencias.count()>1:
                incidenciaOut = incidencias.latest('created_at').created_at
                incidenciaIn = incidencias.earliest('created_at').created_at
                #list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.pk, incidenciaIn.created_at, incidenciaOut.pk, incidenciaOut.created_at) ) 
                can.drawCentredString(230, 507-(y), incidenciaIn.created_at)
                can.drawCentredString(355, 507-(y), incidenciaOut.created_at )
                can.drawString(430, 507-(y), "" )
                can.drawCentredString(560, 507-(y), "-")
            elif incidencias.count()==0:
                print("NO hay información")
            else:
                incidenciaOut = incidencias.latest('created_at').created_at
                fechaRevisada = revisarFecha(person.cat_horario.nombre, incidenciaOut)  
                if fechaRevisada == 1:
                   #list.append( IncidenciaToShow( nombreDias[int(incidenciaOut.created_at.strftime("%w"))], "null", "null", incidenciaOut.pk, incidenciaOut.created_at))
                   can.drawCentredString(230, 507-(y), "--:--" )
                   can.drawCentredString(355, 507-(y), "--:--" )
                   can.drawString(430, 507-(y), " " )
                   can.drawCentredString(560, 507-(y), "-")
                else:
                    #list.append( IncidenciaToShow( nombreDias[int(incidenciaOut.created_at.strftime("%w"))], incidenciaOut.pk, incidenciaOut.created_at, "null", "null" ))  
                    can.drawCentredString(230, 507-(y), "--:--" )
                    can.drawCentredString(355, 507-(y), "--:--" )
                    can.drawString(430, 507-(y), " " )
                    can.drawCentredString(560, 507-(y), "-")
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
                existing_pdf = PdfFileReader(ruta+"Formatos/Reporte de Asistencia v2.pdf")
            else:
                existing_pdf = PdfFileReader(ruta+"Formatos/Reporte de Asistencia Vacio v2.pdf")
            page = existing_pdf.getPage(0)
            page.mergePage( new_pdf.getPage(i))
            output.addPage(page)
            
        outputStream = open(nombre, "wb")
        output.write(outputStream)
        outputStream.close()        
        
    def get(self, request, *args, **kwargs):
        ruta =  settings.MEDIA_ROOT+"/"

        if 'bases' in kwargs:
            people = Person.objects.filter(Q(activo=True) & (Q(cat_contratacion__pk =1) | Q(cat_contratacion__pk =2)) & Q(comision_sindical=False)  & ~Q(cat_contratacion__pk =6)  )
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
            self.create_pdfv2(nombre, person, dateInicio, dateFin, rangoFecha) 
           
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

def calculoIncidenciasPersona(dateInicio, dateFin, person):
    incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin+ timedelta(days = 1)]))
    i=0
    horas_extras=0
    for n in range(int((dateFin - dateInicio).days)+1):
        incidencia = incidencias.filter(created_at__day=(dateInicio + timedelta(n)).day, created_at__month = (dateInicio + timedelta(n)).month, created_at__year = (dateInicio + timedelta(n)).year)
        if incidencia :
            incidenciaOut = incidencia.latest('created_at')
            incidenciaIn = incidencia.earliest('created_at')
            #if incidenciaIn.causa_incidencia == None or incidenciaOut.causa_incidencia == None:
            horas_extras += CalculoHorasExtras(person.cat_horario.nombre , incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde) 
            #elif (incidenciaIn.causa_incidencia.pk == 1 or  incidenciaIn.causa_incidencia.pk ==2 ) and (incidenciaOut.causa_incidencia.pk == 1 or  incidenciaOut.causa_incidencia.pk ==2):
            #    horas_extras += CalculoHorasExtras(person.cat_horario.nombre , incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde) 
            #elif (incidenciaIn.causa_incidencia.pk == 10 or  incidenciaOut.causa_incidencia.pk ==10 ):
            #    horas_extras += CalculoHorasExtras(person.cat_horario.nombre , incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde)     
    return horas_extras
              

def CalculoHorasExtras(horario, horaIn, horaOut, horarioFinDe):
    if horario:
        result = horario.find('-')
        entrada = datetime.datetime(horaIn.year, horaIn.month, horaIn.day, horaIn.hour, horaIn.minute)
        salida = datetime.datetime(horaOut.year, horaOut.month, horaOut.day, horaOut.hour, horaOut.minute)
        tiempoEx = 0
        if  result != -1:
            horain = horario[: result].strip()
            horarioIn =   datetime.datetime.strptime(entrada.strftime("%Y-%m-%d")+"T"+horain, "%Y-%m-%dT%H:%M")
            print(horain)
            tiempoIn = entrada - horarioIn
            print(tiempoIn)
            horaout = horario[result+2:].strip()
            horarioOut =   datetime.datetime.strptime(salida.strftime("%Y-%m-%d")+"T"+ horaout, "%Y-%m-%dT%H:%M")
            print(horarioOut )
            print(salida)
            print(horaIn.weekday())
            if ( (tiempoIn.days < 0) or (horaIn.weekday() > 4)):
                tiempoEx = salida - entrada
            elif( tiempoIn.days==0 and tiempoIn.seconds < 1860 ):     
                tiempoEx = salida - horarioIn
            if tiempoEx != 0:
                horarioEx = horarioOut - horarioIn
                if (horaIn.weekday() > 4) and not horarioFinDe:
                    calcEx = tiempoEx
                else:    
                    calcEx = tiempoEx -horarioEx
                print(calcEx)
                if( not calcEx.days < 0):
                    horasEx = calcEx.seconds / 3600
                    minutosEx = (calcEx.seconds % 3600)/60
                    horasEx = math.trunc(horasEx)
                    if minutosEx > 19 and minutosEx < 50:
                        horasEx += 0.5
                    if minutosEx >=50:
                        horasEx +=1
                    return horasEx
        else:
            tiempoEx = salida - entrada
            print(tiempoEx)
            if( not tiempoEx.days < 0):
                horasEx = tiempoEx.seconds / 3600
                print(horasEx)
                minutosEx = (tiempoEx.seconds % 3600)/60
                print(minutosEx)
                if(horasEx>7):
                    horasEx = math.trunc(horasEx)
                    horasEx = horasEx-7
                    if minutosEx > 19 and minutosEx < 50:
                       horasEx += 0.5
                    if minutosEx >=50:
                        horasEx +=1
                    return horasEx
        return 0


def savePhoto( image_data):
    #makeDir(folder)
    format, imgstr = image_data.split(';base64,')
    data = ContentFile(base64.b64decode(imgstr))
    return data


def searchPerson(request):
    try:
        #if request.is_ajax():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest': 
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
                    if (person.cat_contratacion.pk == 1) or (person.cat_contratacion.pk == 2) or (person.cat_contratacion.pk == 3):
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
                        if person.cat_contratacion.pk == 1 or person.cat_contratacion.pk == 2 or (person.cat_contratacion.pk == 3):
                            incidencia_data={"error":False,"welcome":"Hasta pronto","errorMessage":"Registro de asistencia "+ str(now.strftime("%Y-%m-%d %H:%M")), "persona": person.nombres +" "+person.apellido1 + " "+ person.apellido2, "imagen" : person.imagen_base64, "base": True }
                        else:
                            incidencia_data={"error":False,"welcome":"Vuelva pronto","errorMessage":"Salida visitante " + str(now.strftime("%Y-%m-%d %H:%M")), "base": False }
                        return JsonResponse(incidencia_data,safe=True)
                    if inandout == 1:    
                        incidencia_data={"error":True,"errorMessage":"Entrada Registrada anteriormente con fecha y hora: "+ str(prevDate.strftime("%Y-%m-%d %H:%M"))}
                    else:
                        incidencia_data={"error":True,"errorMessage":"Salida Registrada anteriormente con fecha y hora: "+ str(prevDate.strftime("%Y-%m-%d %H:%M"))}
            return JsonResponse(incidencia_data,safe=True, status=200)
    except Exception as e:
        print(e)          
        return HttpResponse(status=404)

class IncidenciaToShow:  
    def __init__(self, dia,  fecha, idIn, Entrada, idOut, Salida, observacion, horas):
        self.dia = dia
        self.fecha = fecha  
        self.idIn = idIn  
        self.Entrada = Entrada
        self.idOut = idOut
        self.Salida = Salida 
        self.observacion= observacion 
        self.horas = horas




#@method_decorator(login_required, name='dispatch')
class DetalleIncidencias(View):
    def get(self, request, *args, **kwargs):
        periodo1 = PeriodosVacaciones.objects.get(idPeriodo= 1)
        periodo2 = PeriodosVacaciones.objects.get(idPeriodo= 2)
        nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
        causaIncidencia = CausaIncidencia.objects.filter(isVisible = True)
        person = Person.objects.get(pk=self.kwargs['pk'])
        dateInicio = datetime.datetime.strptime(self.kwargs['fechaInicio'], "%d-%m-%Y")
        # t = get_template('people/Incidencias/persona_modif_inci.html')
        list = []  
       
            #Detalle de la persona
        diasExtra = 0
        horasExtras = 0
        diasEco = getDiasEconomicos(person)
        diasVaca1 = getVacaciones(person, periodo1.periodo.pk)
        diasVaca2 = getVacaciones(person, periodo2.periodo.pk)
        
        if person.vacaciones_extra:
            diasExtra = 10 - getVacaciones(person, 6)
       

        if 'fechaFin' in kwargs:
            dateFin = datetime.datetime.strptime(self.kwargs['fechaFin'], "%d-%m-%Y")
           # horasExtras = calculoIncidenciasPersona(dateInicio, dateFin, person)
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
                            if incidenciaIn.causa_incidencia.pk != 1 and  incidenciaIn.causa_incidencia.pk !=2  and incidenciaIn.causa_incidencia.pk != 10:
                                list.append( IncidenciaToShow(nombreDias[int( incidenciaIn.created_at.strftime("%w"))] ,  incidenciaIn.created_at.strftime("%d/%m/%Y"),  incidenciaIn.pk, "--:--",  incidenciaIn.pk, "--:--",  incidenciaIn.causa_incidencia.nombre , "-")) 
                            else:
                                calcHorasExtras = CalculoHorasExtras( person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
                                horasExtras += calcHorasExtras
                                list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), incidenciaIn.causa_incidencia.nombre, calcHorasExtras  )) 
                        else:
                            calcHorasExtras = CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
                            horasExtras += calcHorasExtras
                            list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ", calcHorasExtras )) 
                       
                    else:
                        incicenciaFirst = incidencia.first()
                        fechaRevisada = 0
                        if person.cat_horario:
                            fechaRevisada = revisarFecha(person.cat_horario.nombre,incidenciaOut.created_at)


                        if  incicenciaFirst.causa_incidencia != None :
                            if incicenciaFirst.causa_incidencia.pk != 1 and  incicenciaFirst.causa_incidencia.pk !=2 and incicenciaFirst.causa_incidencia.pk != 10:
                                list.append( IncidenciaToShow(nombreDias[int( incicenciaFirst.created_at.strftime("%w"))] ,  incicenciaFirst.created_at.strftime("%d/%m/%Y"),  incicenciaFirst.pk, "--:--",  incicenciaFirst.pk, "--:--",  incicenciaFirst.causa_incidencia.nombre , "-")) 
                            elif fechaRevisada == 1:
                                list.append( IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] , incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", incicenciaFirst.causa_incidencia.nombre,  "-" )) 
                            else:
                                list.append(IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] ,  incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), incicenciaFirst.causa_incidencia.nombre,  "-" ) ) 
                        else:
                            if fechaRevisada == 1:
                                list.append( IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] , incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", " ",  "-" )) 
                            else:
                                list.append(IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] ,  incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ",  "-" ) ) 
                            i+=1
                else:
                    list.append( IncidenciaToShow( nombreDias[int(  (dateInicio + timedelta(n)).strftime("%w")  )], (dateInicio + timedelta(n)).strftime("%d/%m/%Y"),  "null" , "--:--",  "null", "--:--", " Sin registro" , "-")) 
                    
            content = { #t.render(
            #{
                'person': person, 
                'list': list,
                'fechaInicio': dateInicio.strftime("%d/%m/%Y"), 
                'fechaFin': dateFin.strftime("%d/%m/%Y"),
                'causaIncidencia': causaIncidencia,   
                'diasEco': diasEco,
                'diasVaca1': diasVaca1, 
                'diasVaca2': diasVaca2, 
                'diasExtra': diasExtra,
                'periodo1': PeriodosVacaciones.objects.get(idPeriodo=1).periodo,
                'periodo2': PeriodosVacaciones.objects.get(idPeriodo=2).periodo,
                'horasExtras': horasExtras,
         
            } #)

           
        else:
            incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=dateInicio.day, created_at__month = dateInicio.month, created_at__year = dateInicio.year) )
            if incidencias.count()>1:
                incidenciaOut = incidencias.latest('created_at')
                incidenciaIn = incidencias.earliest('created_at')
                list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ",  "-" ) ) 
                horasExtras = CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
            elif incidencias.count()==0:
                print("NO hay información")
            else:
                incidenciaOut = incidencias.latest('created_at')
                fechaRevisada = revisarFecha(person.cat_horario.nombre, incidenciaOut)  
                if fechaRevisada == 1:
                   list.append( IncidenciaToShow( nombreDias[int(incidenciaOut.created_at.strftime("%w"))], incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), incidenciaOut.causa_incidencia.nombre,  "-" ))
                else:
                    list.append( IncidenciaToShow( nombreDias[int(incidenciaOut.created_at.strftime("%w"))], incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", " ",  "-"  ))  
               
            content = { #t.render(
            #{
                'person': person, 
                'list': list,
                'fechaInicio': dateInicio.strftime("%d/%m/%Y"), 
                'causaIncidencia': causaIncidencia,   
                'diasEco': diasEco,
                'diasVaca1': diasVaca1, 
                'diasVaca2': diasVaca2, 
                'diasExtra': diasExtra,
                'anio': (datetime.datetime.now().year)-1,
                'horasExtras': horasExtras, 
            } #)
            
        if 'admin' in kwargs:
            template = 'people/inci/administradores/persona_modif_inci.html'
        else:
            template = 'people/Incidencias/persona_modif_inci.html'
        
        return render(request, template , content)
   

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
                stuent_data={"error":False,"errorMessage":"Incidencia Actualizada!"}
            return JsonResponse(stuent_data,safe=False)
        except:
            stuent_data={"error":True,"errorMessage":"Failed to Update Data"}
            return JsonResponse(stuent_data,safe=False)

def AddOneDate(person, fecha, tipo):
    nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
    diasEco = 0
    try:
        incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__day=fecha.day, created_at__month = fecha.month, created_at__year = fecha.year) )
        if ValidateVacations(person, fecha):
            newIncidencia = Incidencia(matriculaCredencial=person, created_at=fecha, causa_incidencia= tipo)
            newIncidencia.save()
        else:
            stuent_data={"error":True,"errorMessage":"Fecha " +  fecha.strftime("%d/%m/%Y") + " no agregada por existencia de vacaciones previas. "}
            return stuent_data   
        if incidencias.count()>1:
            incidenciaOut = incidencias.latest('created_at')
            incidenciaIn = incidencias.earliest('created_at')
            resultadoHtml= "<tr><td> "+ nombreDias[int(fecha.strftime("%w"))] +"</td>  <td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>"+ str(incidenciaIn.pk) +"</td><td class='editable' data-type='entrada'>" + incidenciaIn.created_at.strftime("%H:%M:%S") + " </td><td style='display:none' >"+ str(incidenciaOut.pk) + "</td> <td class='editable' data-type='salida'>"+ incidenciaOut.created_at.strftime("%H:%M:%S")+"</td><td>"+tipo.nombre+"</td><td>"+ str(CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )) +"</td> <td><button class='btn btn-default btn-xs eliminar' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
        else:
            if tipo.pk == 1 :
                resultadoHtml= "<tr><td> "+ nombreDias[int(fecha.strftime("%w"))] +"</td><td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>"+ str(newIncidencia.pk) +"</td><td class='editable' data-type='entrada'>" + newIncidencia.created_at.strftime("%H:%M:%S") + " <td>-</td>  </td><td style='display:none' >null</td> <td class='editable' data-type='salida'>Sin Registro</td><td>"+tipo.nombre+"</td><td><button class='btn btn-default btn-xs eliminar' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
            elif tipo.pk == 2:
                resultadoHtml= "<tr><td> "+ nombreDias[int(fecha.strftime("%w"))] +"</td><td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>null</td><td class='editable' data-type='entrada'>Sin Registro</td><td style='display:none' >"+ str(newIncidencia.pk) + "</td> <td>-</td> <td class='editable' data-type='salida'>"+ newIncidencia.created_at.strftime("%H:%M:%S")+"</td><td>"+tipo.nombre+"</td><td><button class='btn btn-default btn-xs eliminar' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
            elif tipo.pk ==3:
                diasEco = getDiasEconomicos(person)
                resultadoHtml= "<tr><td> "+ nombreDias[int(fecha.strftime("%w"))] +"</td><td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>null</td><td class='editable' data-type='entrada'>Sin Registro</td><td style='display:none' >"+ str(newIncidencia.pk) + "</td> <td>-</td> <td class='editable' data-type='salida'>"+ newIncidencia.created_at.strftime("%H:%M:%S")+"</td><td>"+tipo.nombre+"</td><td><button class='btn btn-default btn-xs eliminar' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
            else:
                resultadoHtml = "<tr><td> "+ nombreDias[int(fecha.strftime("%w"))] +"</td><td>"+ fecha.strftime("%d/%m/%Y") +"</td><td style='display:none'>"+ str(newIncidencia.pk) +"</td><td>--:--</td><td style='display:none' >"+ str( newIncidencia.pk) + "</td> <td >--:--</td><td>"+tipo.nombre+"</td><td>-</td><td><button class='btn btn-default btn-xs eliminar' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
        stuent_data={"error":False,"errorMessage":"Incidencia Agregada!", "tabla":resultadoHtml, "diasEco": diasEco}
    except Exception as e:
        print(e)
        stuent_data={"error":True,"errorMessage":"Failed to Update Data"}
    return stuent_data    

def AddTwoDate(person, fecha, fechaComp, tipo):
    periodo1 = PeriodosVacaciones.objects.get(idPeriodo= 1)
    periodo2 = PeriodosVacaciones.objects.get(idPeriodo= 2)
    nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
    if not person.vacaciones_extra and tipo.pk == 6:
        stuent_data={"error":True,"errorMessage": "La persona no cuenta con vacaciones extra"}
    else:
        try:
            resultadoHtml=""
            withErrors =""
            for n in range(int((fechaComp - fecha).days)+1):
                if ValidateVacations(person, fecha+ timedelta(n)):
                    newIncidencia = Incidencia(matriculaCredencial=person, created_at=(fecha + timedelta(n)), causa_incidencia= tipo)
                    newIncidencia.save()
                    resultadoHtml += "<tr><td> "+ nombreDias[int((fecha + timedelta(n)).strftime("%w"))] +"</td><td>"+ (fecha + timedelta(n)).strftime("%d/%m/%Y") +"</td><td style='display:none'>"+ str(newIncidencia.pk) +"</td><td>--:--</td><td style='display:none' >"+ str( newIncidencia.pk) + "</td> <td >--:--</td><td>"+tipo.nombre+"</td><td>-</td> <td><button class='btn btn-default btn-xs eliminar' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
                else:
                    withErrors += "Fecha " +   fecha+ timedelta(n).strftime("%d/%m/%Y") + " no agregada por existencia de incidencias previas. "
                if tipo.pk ==  periodo1.periodo.pk or tipo.pk == periodo2.periodo.pk  or tipo.pk == 6:
                    diasVaca1 = getVacaciones(person, periodo1.periodo.pk)
                    diasVaca2 = getVacaciones(person, periodo2.periodo.pk)  
                    diasExtra = getVacaciones(person, 6)  
                    stuent_data={"error":False,"errorMessage":"Incidencia aplicada al Personal",  "diasVaca1": diasVaca1, "diasVaca2":diasVaca2, "diasExtra": diasExtra}    
                else: 
                    stuent_data={"error":False,"errorMessage":"Incidencia Agregada!", "tabla":resultadoHtml}
                
            if withErrors != "":
                stuent_data["errorMessage"] =  withErrors

            return stuent_data
        except Exception as e:
            print(e)
            stuent_data={"error":True,"errorMessage":"Failed to Update Data"}
    return stuent_data

def AddIncidenciaPerson(person, tipo, fecha, fechaComp):
    periodo1 =PeriodosVacaciones.objects.get(idPeriodo= 1).periodo
    periodo2= PeriodosVacaciones.objects.get(idPeriodo= 2).periodo
    nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
    match tipo.pk:
        case 1 | 2 | 17: 
            #Registro de Entrada y Registro de Salida 1 dd/mm/aaa --:-- ----
            fecha=  datetime.datetime.strptime(fecha, "%Y-%m-%dT%H:%M")
            return JsonResponse(AddOneDate(person, fecha, tipo),safe=False)
        case 3 | 8 | 9 | 11| 12 | 14 | 16 | 19 | 21 | 22 | 23 | 24 | 25:
            #Permiso dia economica 1 dd/mm/aaaa
            fecha=  datetime.datetime.strptime(fecha, "%Y-%m-%d")
            return JsonResponse(AddOneDate(person, fecha, tipo),safe=False)
        #case 4:
            #borrar
        case 6 | 7 | 13 | 15 | 18 | periodo1.pk | periodo2.pk: 
            #Vacaciones extraordinarias 2 dd/mm/aaaa
            fecha=  datetime.datetime.strptime(fecha, "%Y-%m-%d")
            fechaComp =  datetime.datetime.strptime(fechaComp, "%Y-%m-%d")
            return JsonResponse(AddTwoDate(person, fecha, fechaComp, tipo), safe=False)
        case 10: 
            #extravvio gafeta 2 dd/mm/aaaa --:-- ---
            fecha=  datetime.datetime.strptime(fecha, "%Y-%m-%dT%H:%M")
            fechaComp =  datetime.datetime.strptime(fechaComp, "%Y-%m-%dT%H:%M")
            newIncidencia = Incidencia(matriculaCredencial=person, created_at=fecha, causa_incidencia= tipo)
            newIncidencia.save()
            newIncidencia1 = Incidencia(matriculaCredencial=person, created_at=fechaComp, causa_incidencia= tipo)
            newIncidencia1.save()
            resultadoHtml = "<tr><td> "+ nombreDias[int((fecha).strftime("%w"))] +"</td><td>"+ (fecha).strftime("%d/%m/%Y") +"</td><td style='display:none'>"+ str(newIncidencia.pk) +"</td><td>"+fecha.strftime('%H:%M') +"</td><td style='display:none' >"+ str( newIncidencia1.pk) + "</td> <td >"+fechaComp.strftime('%H:%M') +"</td><td>"+tipo.nombre+"</td><td>"+ str(CalculoHorasExtras(person.cat_horario.nombre, newIncidencia.created_at, newIncidencia1.created_at, person.horario_finde )) +"</td> <td><button class='btn btn-default btn-xs eliminar' type='button'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Eliminar Registro </button></td></tr>"
            stuent_data={"error":False,"errorMessage":"Incidencia Agregada!", "tabla":resultadoHtml}
            return JsonResponse(stuent_data,safe=False) 

@csrf_exempt
def AddIncidencia(request):
    tipo = CausaIncidencia.objects.get(id=request.POST.get("tipoIncidencia"))
    periodo1 = PeriodosVacaciones.objects.get(idPeriodo= 1)
    periodo2 = PeriodosVacaciones.objects.get(idPeriodo= 2)
    if not request.POST.get("person"):
        people = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6) & Q(comision_sindical=False) )
        for i, person in enumerate(people):
            fecha = request.POST.get("fechaIncidencia")
            fechaComp = request.POST.get("fechaIncidenciaComp")
            try:
                AddIncidenciaPerson(person, tipo, fecha, fechaComp)
            except Exception as e:
                print(e)
                stuent_data={"error":True,"errorMessage":"Failed to Update Data"}
                return JsonResponse(stuent_data,safe=False)    
        stuent_data={"error":False,"errorMessage":"Incidencia aplicada al Personal"}
        return JsonResponse(stuent_data,safe=False)
    else:
        person =  Person.objects.get(pk=(request.POST.get("person").strip()))
        fecha = request.POST.get("fechaIncidencia")
        fechaComp = request.POST.get("fechaIncidenciaComp")
        if request.POST.get("return"):
            variables = AddIncidenciaPerson(person, tipo, fecha, fechaComp) 
            diasEco = getDiasEconomicos(person)
            diasVaca1 = getVacaciones(person, periodo1.periodo.pk)
            diasVaca2 = getVacaciones(person, periodo2.periodo.pk)
            diasExtra = 10 - getVacaciones(person, 6)  if person.vacaciones_extra else 'No Aplica'
            stuent_data={"error":False,"errorMessage": json.loads(variables.content.decode('utf-8')).get("errorMessage", ""), "persona": person.matricula, "diasEco": diasEco, "diasVaca1":diasVaca1, "diasVaca2": diasVaca2, "diasExtra":diasExtra}
            return JsonResponse(stuent_data,safe=False)
        return AddIncidenciaPerson(person, tipo, fecha, fechaComp) 

def ValidateVacations(person, fecha):
    incidencias = Incidencia.objects.filter( Q(matriculaCredencial= person) & Q(created_at = fecha) )
    if incidencias.count() > 0:
        return False    
    return True



@csrf_exempt
def DeleteIncidencia(request):
    try:
        if(request.POST.get("idHrEntrada")!="null"):
            incidencia1 = Incidencia.objects.get(pk=request.POST.get("idHrEntrada"))
            incidencia1.delete()
        if( request.POST.get("idHrSalida")!="null" and (request.POST.get("idHrEntrada") != request.POST.get("idHrSalida")) ):
            incidencia2 = Incidencia.objects.get(pk=request.POST.get("idHrSalida"))
            incidencia2.delete()
        incidencia_data={"error":False,"errorMessage":"Incidencia Eliminada!"}
        return JsonResponse(incidencia_data,safe=False)
    except Exception as e:
        print(e)
        incidencia_data={"error":True,"errorMessage":"Failed to Delete Data"}
        return JsonResponse(incidencia_data,safe=False)

        

@csrf_exempt
def GetPersonasIncidencia(request):
    q=request.GET.get("q")
    queryset = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6)).order_by('apellido1')
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
@csrf_exempt
def GetIncidenciaTable(request):
    nombreDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sabado']
    causaIncidencia = CausaIncidencia.objects.filter(isVisible = True)
    print(request.GET.get('id'))
    person = Person.objects.get(pk=request.GET.get('id'))
    dateInicio = datetime.datetime.strptime(request.GET.get("fecha1"), "%d/%m/%Y")
    list = []  
    horasExtras = 0
    dateFin = datetime.datetime.strptime(request.GET.get("fecha2"), "%d/%m/%Y")
    if dateFin < dateInicio:
        content = '<br><dic class="col-md-12"><div class="alert alert-warning" id="alertWarning" > <label ><h4 id="alertWarningH4"> El rango de fechas seleccionado es Incorrecto </h4> </label> </div></div>'
    else:
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
                            if incidenciaIn.causa_incidencia.pk != 1 and  incidenciaIn.causa_incidencia.pk !=2 :
                                list.append( IncidenciaToShow(nombreDias[int( incidenciaIn.created_at.strftime("%w"))] ,  incidenciaIn.created_at.strftime("%d/%m/%Y"),  incidenciaIn.pk, "--:--",  incidenciaIn.pk, "--:--",  incidenciaIn.causa_incidencia.nombre , "-")) 
                            else:
                                calcHorasExtras = CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
                                horasExtras += calcHorasExtras
                                list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), incidenciaIn.causa_incidencia.nombre, calcHorasExtras  )) 
                        else:
                            calcHorasExtras = CalculoHorasExtras(person.cat_horario.nombre, incidenciaIn.created_at, incidenciaOut.created_at, person.horario_finde )
                            horasExtras += calcHorasExtras
                            list.append( IncidenciaToShow( nombreDias[int(incidenciaIn.created_at.strftime("%w"))] , incidenciaIn.created_at.strftime("%d/%m/%Y"), incidenciaIn.pk, incidenciaIn.created_at.strftime("%H:%M:%S"),  incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ", calcHorasExtras)) 
                       
                    else:
                        incicenciaFirst = incidencia.first()
                        fechaRevisada = 0
                        if person.cat_horario:
                            fechaRevisada = revisarFecha(person.cat_horario.nombre,incidenciaOut.created_at)


                        if  incicenciaFirst.causa_incidencia != None :
                            if incicenciaFirst.causa_incidencia.pk != 1 and  incicenciaFirst.causa_incidencia.pk !=2 :
                                list.append( IncidenciaToShow(nombreDias[int( incicenciaFirst.created_at.strftime("%w"))] ,  incicenciaFirst.created_at.strftime("%d/%m/%Y"),  incicenciaFirst.pk, "--:--",  incicenciaFirst.pk, "--:--",  incicenciaFirst.causa_incidencia.nombre , "-")) 
                            elif fechaRevisada == 1:
                                list.append( IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] , incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", incicenciaFirst.causa_incidencia.nombre,  "-" )) 
                            else:
                                list.append(IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] ,  incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), incicenciaFirst.causa_incidencia.nombre,  "-" ) ) 
                        else:
                            if fechaRevisada == 1:
                                list.append( IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] , incidenciaOut.created_at.strftime("%d/%m/%Y"), incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), "null", "null", " ",  "-" )) 
                            else:
                                list.append(IncidenciaToShow(nombreDias[int(incidenciaOut.created_at.strftime("%w"))] ,  incidenciaOut.created_at.strftime("%d/%m/%Y"), "null", "null", incidenciaOut.pk, incidenciaOut.created_at.strftime("%H:%M:%S"), " ",  "-" ) ) 
                            i+=1
                else:
                    list.append( IncidenciaToShow( nombreDias[int(  (dateInicio + timedelta(n)).strftime("%w")  )], (dateInicio + timedelta(n)).strftime("%d/%m/%Y"),  "null" , "--:--",  "null", "--:--", " Sin registro" , "-")) 
                        
        t = get_template('people/inci/get_incidencia.html')
        content =  t.render({
                'list': list,
                'causaIncidencia': causaIncidencia,   
                'horasExtras': horasExtras, 
            } )
   
   
    return HttpResponse(content)

def getDiasEconomicos(person):
    now = datetime.datetime.now()
    if now.month >0 and now.month < 8:
        dateInicio = datetime.datetime(now.year -1 , 8, 1, 00, 00, 00, 0) 
        dateFin = datetime.datetime(now.year, 7, 1, 00, 00, 00, 0) 
    else:
        dateInicio = datetime.datetime(now.year, 8, 1, 00, 00, 00, 0) 
        dateFin = datetime.datetime(now.year+1, 7, 1, 00, 00, 00, 0) 
    incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin]) & Q(causa_incidencia__pk=3))
    return incidencias.count()

def getVacaciones(person, tipo):
    now = datetime.datetime.now()
    periodo1 = PeriodosVacaciones.objects.get(idPeriodo= 1)
    periodo2= PeriodosVacaciones.objects.get(idPeriodo= 2)
    if tipo == 4:
        dateInicio = datetime.datetime(now.year-1, 5, 1, 00, 00, 00, 0) 
        dateFin = datetime.datetime(now.year, 5, 1, 00, 00, 00, 0) 
    # elif tipo == periodo2.periodo.pk:
    #     dateInicio = periodo2.dateInicio 
    #     dateFin = periodo2.dateFin 
    elif tipo == 3 or tipo == 6 :
        dateInicio = datetime.datetime(now.year, 1, 1, 00, 00, 00, 0) 
        dateFin = datetime.datetime(now.year, 12, 31, 00, 00, 00, 0)     
    else:
       # dateInicio = person.date_update_vacaciones
       # dateFin = datetime.datetime(dateInicio.year+1, dateInicio.month, dateInicio.day, 00,00,00,0)
        incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(causa_incidencia__pk=tipo) & Q(created_at__year__gt= 2022)) #Vacaciones Segundo Periodo
        return incidencias.count()
    incidencias = Incidencia.objects.filter(Q(matriculaCredencial = person) & Q(created_at__range=[dateInicio, dateFin]) & Q(causa_incidencia__pk=tipo)) #Vacaciones Segundo Periodo
    return incidencias.count()

class AdminConsulta(View):
    def get(self, request, *args, **kwargs):
        #t = get_template('people/Incidencias/inci_list.html')
        content = {
            }
        return render(request, 'people/inci/administradores/login.html' , content)


@csrf_exempt
def loginAdmin(request):
    try:
        #if request.is_ajax():
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
                else:
                    login_data={"error":True,"errorMessage": "Acceso no permitido"}    
            else: 
                login_data={"error":True,"errorMessage": "Error al iniciar sesión, verifique sus datos"}
            return JsonResponse(login_data,safe=False)    
    except Exception as e:
        print(e)          
    return HttpResponse(status=404)

def getAllPersonas(matricula):
    person = Person.objects.get(matricula=matricula)
    multipleAreas = MultipleOrganigrama.objects.filter(info_person = person).values('areasInternas')
    if person.areaInterna.pk ==1:
        queryset = Person.objects.filter( Q(activo=True) & ~Q(cat_contratacion__pk =6)).order_by('apellido1')
    elif multipleAreas.count() > 0:
        queryset = Person.objects.filter( Q(activo=True) & ~Q(cat_contratacion__pk =6))
        query = reduce(operator.or_, ((Q(areaInterna__pk=item['areasInternas'])) for item in multipleAreas))
        queryset = queryset.filter(query).order_by('apellido1')     
    else:
        queryset = Person.objects.filter( Q(activo=True) & Q(areaInterna=person.areaInterna) & ~Q(cat_contratacion__pk =6) ).order_by('apellido1')
        
    return queryset, person

class AyudaToShow:  
    def __init__(self, id, matricula, nombre, MontoXDia, MontoActual):
        self.id = id
        self.matricula = matricula
        self.nombre = nombre
        self.montoXDia = MontoXDia
        self.montoActual = MontoActual

class AdminInciListView(ListView):
    model = Person
   # paginate_by = 50
    import locale
    locale.setlocale(locale.LC_TIME, '')
    def get(self, request, *args, **kwargs):
        queryset, person = getAllPersonas(self.kwargs['matricula'])
        querysetPerson = queryset.values('matricula')
        query = reduce(operator.or_, ((Q(info_person__matricula=item['matricula'])) for item in querysetPerson))
        querysetAyuda = Ayudas.objects.filter(query) 
        now = datetime.datetime.now()
        list = [] 
        dashboard = False 
        if self.kwargs['matricula'] in  ('H210527' , 'M210276' , 'M210668'):
            dashboard = True
        for ayuda in querysetAyuda:
            personaConAyuda=PersonaAyuda.objects.filter(Q(ayuda = ayuda) & Q(created_at__month = now.month) & Q(created_at__year = now.year) )
            monto = (ayuda.montoXDia)*personaConAyuda.count()
            list.append(AyudaToShow(ayuda.pk, ayuda.info_person.matricula, ayuda.info_person.nombres + ' ' + ayuda.info_person.apellido1 + ' '+ ayuda.info_person.apellido2, ayuda.montoXDia,  monto ))    

        content = {
                'people': queryset, 
                'matricula': self.kwargs['matricula'],
                'area': person.areaInterna.nombre,
                'ayudas': list,
                'mes': now.strftime("%B"),
                'dashboard': dashboard,
                'periodo1_pk':  PeriodosVacaciones.objects.get(idPeriodo= 1).periodo.pk,
                'periodo2_pk':  PeriodosVacaciones.objects.get(idPeriodo= 2).periodo.pk,
                }
        return render(request, 'people/inci/administradores/inci_list.html' , content)




@csrf_exempt
def GetAdminIncidencia(request):
  
    q=request.GET.get("q")
    queryset, person = getAllPersonas(request.GET.get("matricula"))
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