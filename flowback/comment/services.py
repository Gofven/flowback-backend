from math import sqrt

from rest_framework.exceptions import ValidationError

from flowback.comment.models import CommentSection, Comment
from flowback.common.services import model_update, get_object
from flowback.files.services import upload_collection
from flowback.user.models import User


def comment_section_create(*, active: bool = True) -> CommentSection:
    comments = CommentSection(active=active)
    comments.full_clean()
    comments.save()

    return comments


def comment_section_create_model_default() -> int:
    comment_section = CommentSection()
    comment_section.full_clean()
    comment_section.save()

    return comment_section.id


def comment_section_delete(*, comments_id: int):
    CommentSection.objects.get(comments_id=comments_id).delete()


def comment_create(*,
                   author_id: int,
                   comment_section_id: int,
                   message: str = None,
                   parent_id: int,
                   attachments: list = None,
                   attachment_upload_to="",
                   attachment_upload_to_include_timestamp=True) -> Comment:

    if attachments:
        collection = upload_collection(user_id=author_id,
                                       file=attachments,
                                       upload_to=attachment_upload_to,
                                       upload_to_include_timestamp=attachment_upload_to_include_timestamp)

    else:
        collection = None

    comment = Comment(author_id=author_id, comment_section_id=comment_section_id,
                      message=message, parent_id=parent_id, attachments=collection)

    if parent_id:
        parent = get_object(Comment, id=parent_id)

        if not parent.active:
            raise ValidationError("Parent has already been removed")

    comment.full_clean()
    comment.save()

    return comment


def comment_update(*, fetched_by: int, comment_section_id: int,  comment_id: int, data) -> Comment:
    comment = get_object(Comment, comment_section_id=comment_section_id, id=comment_id)

    if not comment.active:
        raise ValidationError("Parent has already been removed")

    if fetched_by != comment.author_id:
        raise ValidationError("Comment doesn't belong to User")

    data['edited'] = True
    non_side_effect_fields = ['message', 'edited']
    comment, has_updated = model_update(instance=comment,
                                        fields=non_side_effect_fields,
                                        data=data)

    return comment


def comment_delete(*, fetched_by: int, comment_section_id: int, comment_id: int, force: bool = False):
    comment = get_object(Comment, comment_section_id=comment_section_id, id=comment_id)
    if (fetched_by != comment.author_id) and not force:
        raise ValidationError("Comment doesn't belong to User")

    if not comment.active:
        raise ValidationError("Comment has already been removed")

    if comment.attachments:
        comment.attachments.delete()

    comment.active = False
    comment.message = '[Deleted]'
    comment.save()


def comment_vote(*, user_id: int, comment_section_id: int, comment_id: int, vote: bool = None):
    up_votes = 1
    down_votes = 1

    n = up_votes + down_votes

    if n == 0:
        return 0

    z = 1.281551565545
    p = float(up_votes) / n

    left = p + 1 / (2 * n) * z * z
    right = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    under = 1 + 1 / n * z * z

    return (left - right) / under
