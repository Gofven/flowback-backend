import json
import random

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate, APITransactionTestCase
from .factories import PollFactory

from .utils import generate_poll_phase_kwargs
from ..views.poll import PollListApi, PollCreateAPI
from ...files.tests.factories import FileSegmentFactory
from ...group.tests.factories import GroupFactory, GroupUserFactory, GroupTagsFactory


class PollTest(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.group = GroupFactory()
        self.group_tag = GroupTagsFactory(group=self.group)
        self.group_user_creator = GroupUserFactory(group=self.group)
        (self.poll_one,
         self.poll_two,
         self.poll_three) = [PollFactory(created_by=self.group_user_creator) for x in range(3)]
        segment = FileSegmentFactory()
        self.poll_three.attachments = segment.collection
        self.poll_three.save()

    def test_list_polls(self):
        factory = APIRequestFactory()
        user = self.group_user_creator.user
        view = PollListApi.as_view()

        request = factory.get('')
        force_authenticate(request, user)
        response = view(request, group_id=self.group.id)

        print(json.loads(response.rendered_content))

    def test_create_poll(self):
        factory = APIRequestFactory()
        user = self.group_user_creator.user
        view = PollCreateAPI.as_view()

        data = dict(title='test title', description='test description', poll_type=4, public=True, tag=self.group_tag.id,
                    pinned=False, dynamic=False, attachments=[SimpleUploadedFile('test.jpg', b'test')],
                    **generate_poll_phase_kwargs('base'))
        request = factory.post('', data=data)
        force_authenticate(request, user)
        response = view(request, group_id=self.group.id)  # Success

    def test_create_failing_poll(self):
        factory = APIRequestFactory()
        user = self.group_user_creator.user
        view = PollCreateAPI.as_view()

        data = dict(title='test title', description='test description', poll_type=3, public=True, tag=self.group_tag.id,
                    pinned=False, dynamic=False, attachments=[SimpleUploadedFile('test.jpg', b'test')],
                    **generate_poll_phase_kwargs('base'))
        request = factory.post('', data=data)
        force_authenticate(request, user)

        response = view(request, group_id=self.group.id)  # Success

        self.assertTrue(json.loads(response.rendered_content).get('detail')[0] == 'Schedule poll must be dynamic')
