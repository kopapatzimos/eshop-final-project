# Generated by Django 2.2 on 2020-12-06 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_auto_20201206_2017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(choices=[('G', 'Guitars'), ('B', 'Basses')], max_length=2),
        ),
    ]