# Generated by Django 4.2.7 on 2024-06-04 13:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comment', '0008_alter_tempcomment_score'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vote', models.BooleanField()),
            ],
        ),
        migrations.AlterField(
            model_name='tempcomment',
            name='score',
            field=models.DecimalField(decimal_places=10, default=0, max_digits=11),
        ),
        migrations.AddConstraint(
            model_name='tempcomment',
            constraint=models.CheckConstraint(check=models.Q(('attachments__isnull', False), ('message__isnull', False), _connector='OR'), name='temp_comment_data_check'),
        ),
        migrations.AddField(
            model_name='commentvote',
            name='comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='comment.tempcomment'),
        ),
        migrations.AddField(
            model_name='commentvote',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='commentvote',
            constraint=models.UniqueConstraint(fields=('comment', 'created_by'), name='comment_vote_unique'),
        ),
    ]
