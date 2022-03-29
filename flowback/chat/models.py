from django.db import models
from django.core.exceptions import ValidationError
from flowback.base.models import TimeStampedModel
from flowback.users.models import User, Group


class GroupMessage(TimeStampedModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()


class DirectMessage(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direct_user')
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direct_target')
    message = models.TextField()

    def clean(self):
        if self.user == self.target:
            raise ValidationError("user_one and user_two cannot be the same")
