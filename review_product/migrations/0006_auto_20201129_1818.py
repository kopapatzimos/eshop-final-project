# Generated by Django 2.2 on 2020-11-29 16:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('review_product', '0005_auto_20201129_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='user_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.UserProfile'),
        ),
    ]
