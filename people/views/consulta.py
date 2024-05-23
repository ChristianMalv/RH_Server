from people.models import  Person
from django.http.response import JsonResponse
from django.db.models import Q
def ValidateRFC(request, rfc):
    status = 200
    if request.method == 'GET':
        try:
            person = Person.objects.get(Q(rfc__unaccent__icontains=rfc) & Q(activo=True))
            person_data={"nombre": person.nombres, "apellido1": person.apellido1, "apellido2": person.apellido2,"matricula":person.matricula, "curp":person.curp } 
        except Person.DoesNotExist:
          status = 400 
          person_data={"error":"RFC no encontrado"}
    return JsonResponse(person_data,status=status)    