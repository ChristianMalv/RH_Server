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

class PersonDirectoryUpdateView(UpdateView):
    model = Person
    form_class = DirectorioUpdateForm
    template_name = 'people/directorio/person_form_update.html'
    success_url =  reverse_lazy('activos_list')
   




class DirectoryListView(ListView):
 

    model = Person
    context_object_name = 'people'
    template_name = 'people/person_directory.html'
    #querysetBajas = Bajas.objects.all().values("info_person__pk", "info_person__matricula", "info_person__nombres","info_person__apellido1", "info_person__apellido2")
    #querysetPersons = Person.objects.all().values("pk", "matricula", "nombres", "apellido1", "apellido2")    
    #queryset = querysetPersons.difference(querysetBajas)  
    queryset = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6)).order_by('apellido1')
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
    queryset = Person.objects.filter(Q(activo=True) & ~Q(cat_contratacion__pk =6)).order_by('apellido1')
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