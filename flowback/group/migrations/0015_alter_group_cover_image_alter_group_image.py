# Generated by Django 4.0.8 on 2023-07-27 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0014_group_default_quorum_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='group/cover_image'),
        ),
        migrations.AlterField(
            model_name='group',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='group/image'),
        ),
    ]
