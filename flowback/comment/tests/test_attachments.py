import json

from rest_framework.test import APIRequestFactory, force_authenticate, APITransactionTestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from .factories import CommentFactory, CommentSectionFactory

from flowback.files.models import FileCollection, FileSegment
from ..models import CommentSection, Comment
from ..views import CommentListAPI
from ...files.tests.factories import FileCollectionFactory, FileSegmentFactory
from ...poll.tests.factories import PollFactory
from ...poll.views.comment import PollCommentCreateAPI


class CommentAttachmentsTest(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.collection = FileCollectionFactory()
        (self.file_one,
         self.file_two,
         self.file_three) = [FileSegmentFactory(collection=self.collection) for x in range(3)]

        self.comment = CommentFactory(attachments=self.collection)
        self.poll = PollFactory()

    def test_file_not_null(self):
        factory = APIRequestFactory()
        view = CommentListAPI.as_view()

        request = factory.get('')
        force_authenticate(request, user=self.collection.created_by)
        response = view(request, comment_section_id=self.comment.comment_section_id)

        print(json.loads(response.rendered_content))

    def test_poll_comment_create_no_attachments(self):
        factory = APIRequestFactory()
        view = PollCommentCreateAPI.as_view()
        data = dict(message='hello')

        request = factory.post('', data=data)
        force_authenticate(request, user=self.poll.created_by.user)
        response = view(request, poll=self.poll.id)

        comment_id = int(json.loads(response.rendered_content))
        comment = Comment.objects.get(id=comment_id)
        self.assertEqual(comment.attachments, None)

    def test_poll_comment_create_with_attachments(self):
        factory = APIRequestFactory()
        view = PollCommentCreateAPI.as_view()

        # request without image
        data = dict(message='hello',
                    attachments=[SimpleUploadedFile('test.txt', b'test message'),
                                 SimpleUploadedFile('test_two.txt', b'another test message')])

        request = factory.post('', data=data)
        force_authenticate(request, user=self.poll.created_by.user)
        response = view(request, poll=self.poll.id)

        comment_id = int(json.loads(response.rendered_content))
        comment = Comment.objects.get(id=comment_id)
        total_attachments = comment.attachments.filesegment_set.count()

        self.assertEqual(total_attachments, len(data['attachments']))

