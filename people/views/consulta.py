
from people.models import  Person
from django.http.response import JsonResponse
def ValidateRFC(request, rfc):
    if request.method == 'GET':
        try:
            person = Person.objects.get(rfc__unaccent__icontains=rfc)
            person_data={"nombre": person.nombres, "apellido1": person.apellido1, "apellido2": person.apellido2,"matricula":person.matricula, "curp":person.curp } 
        except Person.DoesNotExist:
          person_data={"error":"RFC no encontrado"}
    return JsonResponse(person_data)    
      