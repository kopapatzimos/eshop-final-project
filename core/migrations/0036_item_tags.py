# Generated by Django 2.2 on 2020-11-30 10:56

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('core', '0035_delete_itemreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
