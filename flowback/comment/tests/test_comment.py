from rest_framework.test import APITransactionTestCase

from flowback.comment.models import TempComment
from flowback.comment.tests.factories import CommentSectionFactory, TempCommentFactory


class CommentSectionTest(APITransactionTestCase):
    def setUp(self):
        self.comment_section = CommentSectionFactory()

    def test_comment_tree(self):
        # Floor 0
        comment: TempComment = TempCommentFactory()

        # Floor 1
        comment_1: TempComment = TempCommentFactory(parent=comment)
        comment_2: TempComment = TempCommentFactory(parent=comment)

        # Floor 2
        comment_11: TempComment = TempCommentFactory(parent=comment_1)
        comment_21: TempComment = TempCommentFactory(parent=comment_2)
        comment_22: TempComment = TempCommentFactory(parent=comment_2)

        # Floor 3
        comment_111: TempComment = TempCommentFactory(parent=comment_11)
        comment_112: TempComment = TempCommentFactory(parent=comment_11)

        print(comment_22.ancestors())
        print(comment.descendants())

        print(TempComment.objects.filter(id=comment_11.id).descendants().with_tree_fields().extra(where=["__tree.tree_depth <= %s"],
                                                           params=[1]))
