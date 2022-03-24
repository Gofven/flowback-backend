from django.db import models
from django.core.exceptions import ValidationError
from flowback.base.models import TimeStampedModel
from flowback.users.models import User, Group


class GroupMessage(TimeStampedModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()


class DirectMessage(TimeStampedModel):
    user_one = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_one')
    user_two = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_two')
    message = models.TextField()

    def clean(self):
        if self.user_one == self.user_two:
            raise ValidationError("user_one and user_two cannot be the same")

    class Meta:
        unique_together = "user_one", "user_two"
