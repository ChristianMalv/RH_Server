from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponseRedirect
from django import forms
from people.models import Person
from .models import *
from datetime import datetime

# Create your views here.

class EvaluacionForm(forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = [
            'nombre', 'clave', 'inicio', 'cierre',
            'aprobatorio', 'archivo', 'renderizable',
            'intentos',
        ]

class ArchivoForm(forms.Form):
    archivo = forms.FileField()

class CreateEvaluacionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = EvaluacionForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'evaluacion/create.html', { 'errors': form.errors })

        ev = form.save()
        ext = ev.archivo.name.split('.')[-1]
        ev.archivo.save(f'{ev.id}/archivo.{ext}', ev.archivo)
        ev.save()
        return HttpResponseRedirect('/evaluacion/lista') # '/evaluacion'

    def get(self, request, *args, **kwargs):
        return render(request, 'evaluacion/create.html')

class ListaEvaluacionView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'evaluacion/lista.html', {
            'evaluaciones': Evaluacion.objects.all()
        })

class AnswerView(View):

    def getPerson(self, curp):
        qs = Person.objects.filter(curp=curp)
        return qs[0] if qs.exists() else None

    def getEvaluacion(self, clave):
        qs = Evaluacion.objects.filter(clave=clave)
        return qs[0] if qs.exists() else None

    def getEvaluacionPersona(self, clave, curp):
        qs = EvaluacionPersona.objects.filter(
            evaluacion__clave=clave,
            persona__curp=curp)
        return qs[0] if qs.exists() else None

    # Params: evaluacion, persona, evaluacionPersona
    def responseEvaluacion(self, request, ev, person, ep):

        if ep and ep.porcentaje >= ev.aprobatorio:
            return render(request, 'evaluacion/evaluate.html', {
                'error': 'Ya has tomado/aprobado esta evaluación'
            })

        if not ep:
            ep = EvaluacionPersona(
                evaluacion=ev, persona=person,
                intentos=0, porcentaje=0.0, archivo=None)

        ep.intentos = ep.intentos + 1
        if ep.intentos > ev.intentos:
            return render(request, 'evaluacion/evaluate.html', {
                'error': 'Has agotado todos tus intentos'
            })

        ep.save()

        contents = None
        if ev.renderizable:
            ev.archivo.open('r')
            contents = ev.archivo.read()

        return render(request, 'evaluacion/answer.html', {
            'evaluacion': ev,
            'person': person,
            'contents': contents,
        })


    # Params: evaluacion, persona, evaluacionPersona
    def responseAnswer(self, request, ev, person, ep):

        ev = self.getEvaluacion(request.POST.get('clave'))
        person = self.getPerson(request.POST.get('curp'))
        ep = self.getEvaluacionPersona(ev.clave, person.curp)

        if not ev or not person or not ep:
            return render(request, 'evaluacion/evaluate.html', {
                'error': 'Evaluación no encontrada'
            })

        if ep.intentos > ev.intentos:
            return render(request, 'evaluacion/evaluate.html', {
                'error': 'Has agotado todos tus intentos'
            })

        form = ArchivoForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'evaluacion/evaluate.html', {
                'error': 'Ha ocurrido un error inesperado',
                'errors': form.errors
            })

        ep.archivo = form.files['archivo']
        ext = ep.archivo.name.split('.')[-1]
        ep.archivo.save(f'{ev.id}/{person.curp}.{ext}', ep.archivo)
        ep.porcentaje = float(request.POST.get('porcentaje', 0.0))
        ep.save()

        return render(request, 'evaluacion/evaluate.html', {
            'ack': f'<b>{ person.nombres } { person.apellido1 } { person.apellido2 }</b> '+
                f'has tenido un porcentaje de aprobación del <b>{ ep.porcentaje * 100 }%</b><br>'+
                f'en la evaluación <b>{ ev.nombre }</b>.'
        })

    def post(self, request, *args, **kwargs):
        ev = self.getEvaluacion(request.POST.get('clave'))
        person = self.getPerson(request.POST.get('curp'))

        if not ev or not person:
            return render(request, 'evaluacion/evaluate.html', {
                'error': 'Evaluación no encontrada'
            })

        if ev.inicio > datetime.now() or ev.cierre < datetime.now():
            return render(request, 'evaluacion/evaluate.html', {
                'error': 'Evaluación fuera de tiempo'
            })
        
        ep = self.getEvaluacionPersona(ev.clave, person.curp)
        if not request.POST.get('porcentaje'):
            return self.responseEvaluacion(request, ev, person, ep)

        return self.responseAnswer(request, ev, person, ep)

    def get(self, request, *args, **kwargs):
        return render(request, 'evaluacion/evaluate.html')
