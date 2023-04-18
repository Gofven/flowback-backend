from django.contrib import admin
from .models import Poll

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'poll_type', 'active', 'public', 'start_date', 'end_date')
    list_filter = ('poll_type', 'active', 'public')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    fieldsets = (
        (None, {
            'fields': ('created_by', 'title', 'description', 'poll_type', 'tag')
        }),
        ('Visibility', {
            'fields': ('active', 'public')
        }),
        ('Dates', {
            'fields': ('start_date', 'proposal_end_date', 'vote_start_date', 'delegate_vote_end_date', 'vote_end_date', 'end_date')
        }),
        ('Optional Dynamic Counting Support', {
            'fields': ('dynamic',)
        }),
    )
    ordering = ('-created_by', 'created_by')