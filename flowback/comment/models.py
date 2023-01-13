from django.db import models
from flowback.common.models import BaseModel
from flowback.user.models import User


class CommentSection(BaseModel):
    allow_replies = models.BooleanField()


class Comment(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=10000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE)
    score = models.IntegerField()
