# Generated by Django 2.2 on 2019-11-22 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20191122_1733'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(choices=[('S', 'DILDOS'), ('C', 'CONDOMS'), ('P', 'PLUGS')], max_length=2),
        ),
    ]
