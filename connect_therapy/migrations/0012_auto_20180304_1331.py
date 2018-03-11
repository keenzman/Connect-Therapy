# Generated by Django 2.0.2 on 2018-03-04 13:31

import connect_therapy.models
import django.contrib.auth.base_user
from django.db import migrations, models
import django.db.models.deletion
import functools


class Migration(migrations.Migration):

    dependencies = [
        ('connect_therapy', '0011_auto_20180301_2200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='session_id',
            field=models.CharField(default=functools.partial(connect_therapy.models.generate_session_id, *(), **{'date_time': models.DateTimeField(), 'patient': models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='connect_therapy.Patient'), 'practitioner': models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='connect_therapy.Practitioner'), 'salt': models.CharField(default=functools.partial(django.contrib.auth.base_user.BaseUserManager.make_random_password, *(10,), **{}), editable=False, max_length=255)}), editable=False, max_length=255),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='session_salt',
            field=models.CharField(default=functools.partial(django.contrib.auth.base_user.BaseUserManager.make_random_password, *(10,), **{}), editable=False, max_length=255),
        ),
    ]
