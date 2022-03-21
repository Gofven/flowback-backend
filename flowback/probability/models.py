from django.db import models
from settings.base import AUTH_USER_MODEL
from django.core.validators import MinValueValidator, MaxValueValidator


class ProbabilityUser(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True)
    trust = models.IntegerField(default=50,
                                validators=[MinValueValidator(0),
                                            MaxValueValidator(100)])


class ProbabilityPost(models.Model):
    title = models.CharField()
    description = models.CharField()

    active = models.BooleanField()
    finished = models.BooleanField()
    result = models.BooleanField()


class ProbabilityVote(models.Model):
    user = models.ForeignKey(ProbabilityUser, on_delete=models.CASCADE)
    post = models.ForeignKey(ProbabilityPost, on_delete=models.CASCADE)
    vote = models.PositiveSmallIntegerField(validators=[MinValueValidator(0),
                                                        MaxValueValidator(5)])

    class Meta:
        unique_together = 'user', 'post'
