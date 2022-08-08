from django.db import models
from flowback.base.models import TimeStampedModel
from flowback.users.models import User


class Todo(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.IntegerField()
    content = models.TextField()
