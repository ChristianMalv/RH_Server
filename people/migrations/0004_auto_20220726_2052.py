# Generated by Django 2.1 on 2022-07-26 20:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0003_person_horario_finde'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='compensaciones',
            options={'permissions': (('asignar_comp', 'Puede asignar compensaciones'),), 'verbose_name': 'Compensacion', 'verbose_name_plural': 'Compensaciones'},
        ),
    ]
