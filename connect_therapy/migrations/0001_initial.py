# Generated by Django 2.0.3 on 2018-03-24 13:23

import datetime
from decimal import Decimal
from django.conf import settings
import django.contrib.auth.base_user
from django.db import migrations, models
import django.db.models.deletion
import functools


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date_and_time', models.DateTimeField()),
                ('length', models.DurationField(default=datetime.timedelta(0, 1800))),
                ('practitioner_notes', models.TextField(blank=True)),
                ('patient_notes_by_practitioner', models.TextField(blank=True)),
                ('patient_notes_before_meeting', models.TextField(blank=True)),
                ('session_id', models.CharField(default=functools.partial(django.contrib.auth.base_user.BaseUserManager.make_random_password, *(50,), **{}), editable=False, max_length=255)),
                ('price', models.DecimalField(decimal_places=2, default=Decimal('50'), max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('X', 'Other')], max_length=1)),
                ('mobile', models.CharField(max_length=20)),
                ('email_confirmed', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Practitioner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_line_1', models.CharField(max_length=100)),
                ('address_line_2', models.CharField(blank=True, max_length=100, null=True)),
                ('postcode', models.CharField(max_length=10)),
                ('mobile', models.CharField(max_length=20)),
                ('is_approved', models.BooleanField(default=False)),
                ('email_confirmed', models.BooleanField(default=False)),
                ('bio', models.TextField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='connect_therapy.Patient'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='practitioner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='connect_therapy.Practitioner'),
        ),
    ]
