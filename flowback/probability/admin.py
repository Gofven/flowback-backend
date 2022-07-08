from django.contrib import admin
from .models import ProbabilityPost, ProbabilityVote, ProbabilityUser

# Register your models here.
admin.site.register(ProbabilityPost)
admin.site.register(ProbabilityVote)
admin.site.register(ProbabilityUser)
