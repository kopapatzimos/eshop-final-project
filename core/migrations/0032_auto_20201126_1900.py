# Generated by Django 2.2 on 2020-11-26 17:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_itemreview'),
    ]

    operations = [
        migrations.RenameField(
            model_name='itemreview',
            old_name='review_date',
            new_name='date_added',
        ),
    ]