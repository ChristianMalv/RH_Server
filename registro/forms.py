from django import forms
from django.core.exceptions import ValidationError
from registro import models

class SaveEmployee(forms.ModelForm):
    employee_code = forms.CharField(max_length=250, label="Company ID")
    first_name = forms.CharField(max_length=250, label="First Name")
    middle_name = forms.CharField(max_length=250, label="Middle Name", required=False)
    last_name = forms.CharField(max_length=250, label="Last Name")
    department = forms.CharField(max_length=250, label="Department")
    tipo = forms.CharField(max_length=250, label="Tipo")
    matricula = forms.CharField(max_length=250, label="Matrícula", required=False)  # Sin acento, consistente con el modelo
    avatar = forms.ImageField(label="Avatar")

    class Meta:
        model = models.Employee
        fields = ('employee_code', 'first_name', 'middle_name', 'last_name', 'department', 'tipo', 'matricula', 'avatar')

    def clean_employee_code(self):
        employee_code = self.cleaned_data['employee_code']
        if models.Employee.objects.filter(employee_code=employee_code).exclude(id=self.instance.id if self.instance else None).exists():
            raise ValidationError(f"El visitante {employee_code} ya existe.")
        return employee_code