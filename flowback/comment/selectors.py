import django_filters

from flowback.comment.models import Comment


class BaseCommentFilter(django_filters.FilterSet):
    order_by = django_filters.OrderingFilter(
        fields=(('created_at', 'created_at_asc'),
                ('-created_at', 'created_at_desc'),
                ('score', 'score_asc'),
                ('-score', 'score_desc'))
    )

    class Meta:
        model = Comment
        fields = dict(id=['exact'],
                      author_id=['exact'],
                      parent_id=['exact'],
                      score=['gt'])


# TODO group parents together
def comment_list(*, comment_section_id: int, filters=None):
    filters = filters or {}

    qs = Comment.objects.filter(comment_section_id=comment_section_id).all()
    return BaseCommentFilter(filters, qs).qs
