from django.contrib import admin

from flowback.poll.models import Poll


# Register your models here.
@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'title', 'poll_type', 'status')

    fieldsets = [('General Information', {'fields': ['created_by', 'title', 'description', 'poll_type',
                                                     'dynamic', 'quorum', 'phases']}),
                 ('Visibility', {'fields': ['pinned', 'active', 'public']}),
                 ('Advanced options', {'fields': ['attachments', 'blockchain_id', 'allow_fast_forward']}),
                 ('Debug', {'fields': ['status', 'tag']})]
