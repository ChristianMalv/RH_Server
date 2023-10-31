
from django.shortcuts import render
from django.urls import reverse_lazy
from people.models import AreaOrganigrama, Compensacion, Compensaciones, Person, Incidencia, Bajas, AreaInterna, CausaIncidencia
from people.forms import AreaForm
from django.views.generic import ListView, CreateView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class AreasListView(ListView):
    model = AreaOrganigrama
    def get(self, request, *args, **kwargs):
        queryset =AreaOrganigrama.objects.all()
        querysetAI = AreaInterna.objects.all()

        content = {#t.render(
            'areaOrganigrama': queryset, 
            'areaInterna' : querysetAI,
        }#)
        return render(request, 'people/area/area_list.html' , content)    

class AreasUpdateView(UpdateView):
    model = AreaOrganigrama
    form_class = AreaForm
    template_name = 'people/areas/areas_form_update.html'
    success_url =  reverse_lazy('activos_list')


class AreasCreateView(CreateView):
    model = AreaOrganigrama
    form_class = AreaForm
    template_name = 'people/areas/areas_form.html'
    success_url = reverse_lazy('person_list')
   
