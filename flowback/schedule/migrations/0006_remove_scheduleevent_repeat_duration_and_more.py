# Generated by Django 4.2.16 on 2024-12-29 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0018_improve_crontab_helptext'),
        ('schedule', '0005_scheduleevent_repeat_duration_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduleevent',
            name='repeat_duration',
        ),
        migrations.AddField(
            model_name='scheduleevent',
            name='repeat_next_run',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scheduleevent',
            name='repeat_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_celery_beat.periodictask'),
        ),
        migrations.AlterField(
            model_name='scheduleevent',
            name='repeat_frequency',
            field=models.IntegerField(blank=True, choices=[(1, 'Daily'), (2, 'Weekly'), (3, 'Monthly'), (4, 'Yearly')], null=True),
        ),
    ]
