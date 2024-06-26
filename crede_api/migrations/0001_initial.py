# Generated by Django 4.2.2 on 2024-05-09 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Visitante',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('metadatos', models.JSONField()),
                ('ingreso', models.DateTimeField()),
                ('salida', models.DateTimeField()),
                ('clave', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
