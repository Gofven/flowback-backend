from rest_framework.exceptions import ValidationError

from flowback.comment.models import CommentSection, Comment
from flowback.common.services import model_update


def comment_section_create(*, allow_replies: bool) -> CommentSection:
    comments = CommentSection(allow_replies=allow_replies)
    comments.full_clean()
    comments.save()

    return comments


def comment_section_delete(*, comments_id: int):
    CommentSection.objects.get(comments_id=comments_id).delete()


def comment_create(*, author_id: int, comment_section_id: int, message: str, parent_id: int) -> Comment:
    comment = Comment(author_id=author_id, comment_section_id=comment_section_id,
                      message=message, parent_id=parent_id)
    comment.full_clean()
    comment.save()

    return comment


def comment_update(*, fetched_by: int, comment_section_id: int,  comment_id: int, data) -> Comment:
    comment = Comment.objects.get(comment_section_id=comment_section_id, id=comment_id)
    if fetched_by != comment.author_id:
        raise ValidationError("Comment doesn't belong to User")

    data['edited'] = True
    non_side_effect_fields = ['message', 'edited']
    comment, has_updated = model_update(instance=comment,
                                        fields=non_side_effect_fields,
                                        data=data)

    return comment


def comment_delete(*, fetched_by: int, comment_section_id: int, comment_id: int):
    comment = Comment.objects.get(comment_section_id=comment_section_id, id=comment_id)
    if fetched_by != comment.author_id:
        raise ValidationError("Comment doesn't belong to User")

    comment.delete()
