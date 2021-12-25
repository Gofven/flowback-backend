
# Generated by Django 3.1.2 on 2021-01-30 00:11

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('users', '0008_group_cover_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='group',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='group',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='group',
            name='direct_join',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='group',
            name='needs_moderation',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='group',
            name='private',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='group',
            name='public',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='group',
            name='tag',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='group',
            name='updated_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='updated_by', to='users.user'),
            preserve_default=False,
        ),
    ]