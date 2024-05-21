# Generated by Django 4.2.13 on 2024-05-20 17:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('people', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Evaluacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.CharField(max_length=10)),
                ('nombre', models.CharField(max_length=100)),
                ('archivo', models.FileField(upload_to='evaluacion')),
                ('renderizable', models.BooleanField()),
                ('intentos', models.IntegerField()),
                ('aprobatorio', models.DecimalField(decimal_places=3, max_digits=5)),
                ('inicio', models.DateTimeField()),
                ('cierre', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='EvaluacionPersona',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intentos', models.IntegerField()),
                ('porcentaje', models.DecimalField(decimal_places=3, max_digits=5)),
                ('archivo', models.FileField(upload_to='evaluacion')),
                ('modified', models.DateField(auto_now=True)),
                ('evaluacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evaluacion.evaluacion')),
                ('persona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.person')),
            ],
        ),
    ]
