
# Generated by Django 3.1.2 on 2021-02-02 01:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_group_website'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='website',
        ),
    ]