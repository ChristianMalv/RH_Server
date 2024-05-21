from django.shortcuts import redirect, render
import json
from django.contrib import messages
# from django.contrib.auth.models import User
from django.http import HttpResponse
from registro import models, forms
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import requests
from django.http import HttpResponse
from django.contrib import messages
import json
from .forms import SaveEmployee  # Asegúrate de tener la importación correcta
from .models import Employee  # Verifica que la importación del modelo es correcta
from django.http import JsonResponse

from django.shortcuts import render, get_object_or_404
import requests
from django.utils import timezone


def context_data():
    context = {
        'page_name' : '',
        'page_title' : 'Chat Room',
        'system_name' : 'Registro de Visitantes por QR',
        'topbar' : True,
        'footer' : True,
    }

    return context


# # Create your views here.
# def login_page(request):
#     context = context_data()
#     context['topbar'] = False
#     context['footer'] = False
#     context['page_name'] = 'login'
#     context['page_title'] = 'Login'
#     return render(request, 'registro/login.html', context)

# def login_user(request):
#     logout(request)
#     resp = {"status":'failed','msg':''}
#     username = ''
#     password = ''
#     if request.POST:
#         username = request.POST['username']
#         password = request.POST['password']

#         user = authenticate(username=username, password=password)
#         if user is not None:
#             if user.is_active:
#                 login(request, user)
#                 resp['status']='success'
#             else:
#                 resp['msg'] = "Incorrect username or password"
#         else:
#             resp['msg'] = "Incorrect username or password"
#     return HttpResponse(json.dumps(resp),content_type='application/json')


# def home(request):
#     context = context_data()
#     context['page'] = 'home'
#     context['page_title'] = 'Home'
#     context['employees'] = models.Employee.objects.count()
#     return render(request, 'registro/home.html', context)

def logout_user(request):
    logout(request)
    return redirect('login-page')



def employee_list(request):
    context =context_data()
    context['page'] = 'employee_list'
    context['page_title'] = 'Lista de visitantes'
    context['employees'] = models.Employee.objects.all().order_by('-id')

    return render(request, 'registro/employee_list.html', context)


 
def manage_employee(request, pk=None):
    # Suponiendo que context_data() es una función que prepara datos generales para el contexto
    context = context_data()
    
    try:
        response = requests.get("https://credenciales.aprende.gob.mx/personal/api")
        direcciones = response.json() if response.status_code == 200 else []
    except requests.RequestException:
        direcciones = []  # En caso de fallo, envía una lista vacía

    if pk:
        employee = get_object_or_404(models.Employee, id=pk)
        context.update({
            'page': 'edit_employee',
            'page_title': 'Editar Visitante',
            'employee': employee,
            'direcciones': direcciones  
        })
    else:
        context.update({
            'page': 'add_employee',
            'page_title': 'Agregar Visitante',
            'employee': {},
            'direcciones': direcciones 
        })

    return render(request, 'registro/manage_employee.html', context)




def save_employee(request):
    resp = {'status': 'failed', 'msg': ''}
    employee_id = None
    employee = None  # Inicializamos employee con None

    if not request.method == 'POST':
        resp['msg'] = "No data has been sent into the request."
    else:
        if request.POST['id'] == '':
            form = forms.SaveEmployee(request.POST, request.FILES)
        else:
            employee = models.Employee.objects.get(id=request.POST['id'])
            form = forms.SaveEmployee(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save()
            employee_id = employee.id
            if request.POST['id'] == '':
                messages.success(request, f"El visitante {request.POST['employee_code']} ha ingresado correctamente.")
            else:
                messages.success(request, f"El visitante {request.POST['employee_code']} ha sido actualizado correctamente.")
            resp['status'] = 'success'
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str("<br />")
                    resp['msg'] += str(f"[{field.label}] {error}")

    resp['employee_id'] = employee_id

    return JsonResponse(resp)


def view_card(request, pk =None):
    if pk is None:  
        return HttpResponse("El ID del visitante es invalido")
    else:
        context = context_data()
        context['employee'] = models.Employee.objects.get(id=pk)
        return render(request, 'registro/view_id.html', context)


def view_scanner(request):
    context = context_data()
    return render(request, 'registro/scanner.html', context)


def view_details(request, code = None):
    if code is None:
        return HttpResponse("El ID del visitante es invalido")
    else:
        context = context_data()
        context['employee'] = models.Employee.objects.get(pk=code)
        return render(request, 'registro/view_details.html', context)
    

def end_visit(request, code=None):
    resp = {'status': 'failed', 'msg': ''}
    
    if code is None:
        resp['msg'] = "No se ha recibido ninguna información."
    else:
        employee = models.Employee.objects.filter(pk=code).first()
        if employee is None:
            resp['msg'] = "El empleado no existe."
        else:
            Employee.objects.filter(pk=code).update(date_end=timezone.now())
            messages.success(request, f"La visita del empleado {employee.first_name} {employee.middle_name} {employee.last_name} ha sido finalizada correctamente.")
            resp['status'] = 'success'

    return JsonResponse(resp)


def delete_employee(request, pk=None):
    resp = { 'status' : 'failed', 'msg' : '' }
    if pk is None:
        resp['msg'] = "No se ha recibido ninguna información."
    else:
        try:
            models.Employee.objects.get(id=pk).delete()
            resp['status'] = 'success'
            messages.success(request, 'El visitante ha sido borrado correctamente.')
        except:
            resp['msg'] = "Hubo un error al eliminar al visitante."

    return HttpResponse(json.dumps(resp), content_type="application/json")