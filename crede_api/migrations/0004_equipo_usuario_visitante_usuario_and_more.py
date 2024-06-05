# Generated by Django 4.2.2 on 2024-05-30 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crede_api', '0003_tipoequipo_tipoingreso_equipo_entradasalidaequipo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipo',
            name='usuario',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='visitante',
            name='usuario',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='asignacionequipo',
            name='usuario',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
