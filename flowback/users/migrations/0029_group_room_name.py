
# Generated by Django 3.1.2 on 2021-03-08 00:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0028_auto_20210223_0110'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='room_name',
            field=models.CharField(default='default', max_length=100),
        ),
    ]