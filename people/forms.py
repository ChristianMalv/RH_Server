from dataclasses import field
from django import forms
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from people.models import AreaOrganigrama, Incidencia, Person, ServicioSocial
from django.forms.widgets import NumberInput
from multi_email_field.forms import MultiEmailField
import datetime
from django.forms.models import inlineformset_factory
class PersonForm(forms.ModelForm):
    rfc = forms.CharField(max_length=13, label="RFC CON HOMOCLAVE", required=False, validators=[
        RegexValidator('^([A-Z,Ñ,&]{3,4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])[A-Z|\d]{3})$',
                       message="Introduzca un RFC válido")])
    curp = forms.CharField(max_length=20, label="CURP ", required=False, validators=[RegexValidator(
        '^[A-Z]{1}[AEIOU]{1}[A-Z]{2}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])[HM]{1}(AS|BC|BS|CC|CS|CH|CL|CM|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[B-DF-HJ-NP-TV-Z]{3}[0-9A-Z]{1}[0-9]{1}$',
        message="Introduzca un CURP válido")])
    telefono1 =  forms.CharField(max_length=15, required=False, label="Teléfono 1",
                               validators=[RegexValidator('^\d{4,}$', message="Introduzca un Teléfono válido")])
    telefono2 =  forms.CharField(max_length=15, required=False, label="Teléfono 2",
                               validators=[RegexValidator('^\d{4,}$', message="Introduzca un Teléfono válido")])
    emergencia_telefono =  forms.CharField(max_length=15, required=False, label="Teléfono Emergencia",
                               validators=[RegexValidator('^\d{4,}$', message="Introduzca un Teléfono válido")])
    email_personal = forms.EmailField(required=True)
    email_institucional = MultiEmailField()

    fecha_ingreso = forms.DateField(input_formats=['%d/%m/%Y'])

    imagen_base64 = forms.HiddenInput()
    class Meta:
        model = Person
        fields = '__all__'
        


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save person'))
        #self.fields['fecha_ingreso'].widget.attrs['class'] = 'datepicker'
        self.fields['curp'].widget.attrs['onkeyup'] = 'javascript:this.value=this.value.toUpperCase();'
        self.fields['rfc'].widget.attrs[' onkeyup'] = 'javascript:this.value=this.value.toUpperCase();'
       
class IncidenciaForm(forms.ModelForm):
    class Meta:
        model = Incidencia
        fields = '__all__'


class DirectorioUpdateForm(forms.ModelForm):
    class Meta:
        model = Person
        fields= ('email_institucional', 'extension_telefonica', 'nombres', 'apellido1', 'apellido2', 'areaInterna', 'cat_area_org', 'puesto', )
    
class AreaForm(forms.ModelForm):
    class Meta:
        model = AreaOrganigrama
        fields = '__all__'

class ConsultaIncidenciaForm(forms.ModelForm):
    class Meta:
        model = Person
        fields= ('matricula', 'rfc', )

class ServicioSocialForm(forms.ModelForm):
    telefono_escuela =  forms.CharField(max_length=15, required=False, label="Teléfono escuela",
                               validators=[RegexValidator('^\d{4,}$', message="Introduzca un Teléfono válido")])
    class Meta:
        model = ServicioSocial
        exclude = ['info_person'] 


ServicioSocialInlineFormset = inlineformset_factory(
    Person,
    ServicioSocial,
    form=ServicioSocialForm,
    extra=1,
    # max_num=5,
    # fk_name=None,
    # fields=None, exclude=None, can_order=False,
    # can_delete=True, max_num=None, formfield_callback=None,
    # widgets=None, validate_max=False, localized_fields=None,
    # labels=None, help_texts=None, error_messages=None,
    # min_num=None, validate_min=False, field_classes=None
)
   