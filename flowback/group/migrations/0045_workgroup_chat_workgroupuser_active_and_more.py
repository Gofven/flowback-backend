# Generated by Django 4.2.16 on 2025-03-10 11:23

from django.db import migrations, models
import django.db.models.deletion


def pre_populate_fields(apps, schema_editor):
    MessageChannel = apps.get_model('chat', 'messagechannel')
    WorkGroup = apps.get_model('group', 'workgroup')

    for work_group in WorkGroup.objects.all():
        work_group.chat = MessageChannel.objects.create(origin_name='workgroup', title=work_group.name)
        work_group.save()


def pre_populate_fields_two(apps, schema_editor):
    MessageChannelParticipant = apps.get_model('chat', 'messagechannelparticipant')
    WorkGroupUser = apps.get_model('group', 'workgroupuser')

    for work_group_user in WorkGroupUser.objects.all():
        work_group_user.chat_participant = MessageChannelParticipant.objects.create(channel=work_group_user.work_group.chat, user=work_group_user.group_user.user)
        work_group_user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_messagechannel_users'),
        ('group', '0044_groupthread_work_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='workgroup',
            name='chat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='chat.messagechannel', null=True)
        ),
        migrations.RunPython(pre_populate_fields),
        migrations.AlterField(
            model_name='workgroup',
            name='chat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='chat.messagechannel')
        ),
        migrations.AddField(
            model_name='workgroupuser',
            name='chat_participant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='chat.messagechannelparticipant',
                                    null=True)
        ),
        migrations.RunPython(pre_populate_fields_two),
        migrations.AddField(
            model_name='workgroupuser',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='workgroupuser',
            name='chat_participant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='chat.messagechannelparticipant')
        )
    ]
