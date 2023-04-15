from flowback.comment.models import Comment
from flowback.common.services import get_object
from flowback.group.selectors import group_user_permissions
from flowback.poll.models import Poll
from flowback.comment.services import comment_create, comment_update, comment_delete


def poll_comment_create(*, author_id: int, poll_id: int, message: str, parent_id: int = None):
    poll = get_object(Poll, id=poll_id)
    group_user_permissions(group=poll.created_by.group.id, user=author_id)

    return comment_create(author_id=author_id,
                          comment_section_id=poll.comment_section.id,
                          message=message,
                          parent_id=parent_id)


def poll_comment_update(*, fetched_by: int, poll_id: int, comment_id: int, data) -> Comment:
    poll = get_object(Poll, id=poll_id)
    group_user_permissions(group=poll.created_by.group.id, user=fetched_by)

    return comment_update(fetched_by=fetched_by,
                          comment_section_id=poll.comment_section.id,
                          comment_id=comment_id,
                          data=data)


def poll_comment_delete(*, fetched_by: int, poll_id: int, comment_id: int):
    poll = get_object(Poll, id=poll_id)
    group_user_permissions(group=poll.created_by.group.id, user=fetched_by)

    return comment_delete(fetched_by=fetched_by,
                          comment_section_id=poll.comment_section.id,
                          comment_id=comment_id)
