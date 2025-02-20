# Generated by Django 4.2.16 on 2024-12-06 11:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0004_scheduleevent_meeting_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleevent',
            name='repeat_duration',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(86400)]),
        ),
        migrations.AddField(
            model_name='scheduleevent',
            name='repeat_frequency',
            field=models.IntegerField(blank=True, choices=[(1, 'Daily'), (2, 'Weekly'), (3, 'Monthly')], null=True),
        ),
    ]
