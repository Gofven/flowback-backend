from drf_spectacular.utils import extend_schema

from ..selectors.comment import poll_comment_list, poll_delegate_comment_list
from ..services.comment import (poll_comment_create,
                                poll_comment_update,
                                poll_comment_delete,
                                poll_delegate_comment_create,
                                poll_delegate_comment_update,
                                poll_delegate_comment_delete)

from flowback.comment.views import CommentListAPI, CommentCreateAPI, CommentUpdateAPI, CommentDeleteAPI


@extend_schema(tags=['poll'])
class PollCommentListAPI(CommentListAPI):
    list_function = poll_comment_list


@extend_schema(tags=['poll'])
class PollCommentCreateAPI(CommentCreateAPI):
    create_function = poll_comment_create


@extend_schema(tags=['poll'])
class PollCommentUpdateAPI(CommentUpdateAPI):
    update_function = poll_comment_update


@extend_schema(tags=['poll'])
class PollCommentDeleteAPI(CommentDeleteAPI):
    delete_function = poll_comment_delete


@extend_schema(tags=['poll'])
class PollDelegateCommentListAPI(CommentListAPI):
    list_function = poll_delegate_comment_list


@extend_schema(tags=['poll'])
class PollDelegateCommentCreateAPI(CommentCreateAPI):
    create_function = poll_delegate_comment_create


@extend_schema(tags=['poll'])
class PollDelegateCommentUpdateAPI(CommentUpdateAPI):
    update_function = poll_delegate_comment_update


@extend_schema(tags=['poll'])
class PollDelegateCommentDeleteAPI(CommentDeleteAPI):
    delete_function = poll_delegate_comment_delete
