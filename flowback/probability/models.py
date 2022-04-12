from django.db import models

from flowback.base.models import TimeStampedModel
from settings.base import AUTH_USER_MODEL
from django.core.validators import MinValueValidator, MaxValueValidator


class ProbabilityUser(TimeStampedModel):
    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
    trust = models.IntegerField(default=50,
                                validators=[MinValueValidator(1),
                                            MaxValueValidator(100)])


class ProbabilityPost(TimeStampedModel):
    title = models.CharField(max_length=255)
    description = models.TextField()

    active = models.BooleanField()
    finished = models.BooleanField()
    result = models.BooleanField()


class ProbabilityVote(TimeStampedModel):
    user = models.ForeignKey(ProbabilityUser, on_delete=models.CASCADE)
    post = models.ForeignKey(ProbabilityPost, on_delete=models.CASCADE)
    vote = models.PositiveSmallIntegerField(validators=[MinValueValidator(0),
                                                        MaxValueValidator(5)])

    class Meta:
        unique_together = 'user', 'post'
