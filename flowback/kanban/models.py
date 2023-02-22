from django.utils.translation import gettext_lazy as _

from django.db import models
from flowback.common.models import BaseModel
from flowback.user.models import User


class Kanban(BaseModel):
    name = models.CharField(max_length=255)
    origin_type = models.CharField(max_length=255)
    origin_id = models.IntegerField()

    class Meta:
        unique_together = ('origin_type', 'origin_id')


class KanbanEntry(BaseModel):
    class KanbanTag(models.IntegerChoices):
        BACKLOG = 1, _('backlog')
        CHOSEN_FOR_EXECUTION = 2, _('chosen_for_execution')
        IN_PROGRESS = 3, _('in_progress')
        EVALUATION = 4, _('evaluation')
        FINISHED = 5, _('finished')

    kanban = models.ForeignKey(Kanban, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kanban_entry_created_by')
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='kanban_entry_assignee')

    title = models.CharField(max_length=255)
    description = models.TextField()
    tag = models.IntegerField(choices=KanbanTag.choices)


class KanbanSubscription(BaseModel):
    kanban = models.ForeignKey(Kanban, on_delete=models.CASCADE, related_name='kanban_subscription_kanban')
    target = models.ForeignKey(Kanban, on_delete=models.CASCADE, related_name='kanban_subscription_target')

    class Meta:
        unique_together = ('kanban', 'target')
