# Generated by Django 4.2.2 on 2024-05-10 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crede_api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitante',
            name='clave',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='visitante',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='visitante',
            name='salida',
            field=models.DateTimeField(null=True),
        ),
    ]
