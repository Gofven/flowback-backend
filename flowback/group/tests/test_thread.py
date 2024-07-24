from rest_framework import status
from rest_framework.test import APITestCase

from flowback.common.tests import generate_request
from flowback.group.models import GroupThreadVote
from flowback.group.tests.factories import GroupThreadFactory, GroupUserFactory
from flowback.group.views.thread import GroupThreadVoteUpdateAPI
from flowback.user.models import User


class TestGroupThreadVote(APITestCase):
    def setUp(self):
        self.group_admin = GroupUserFactory()
        self.threads = GroupThreadFactory.create_batch(10, created_by=self.group_admin)
        self.group_user = GroupUserFactory(group=self.group_admin.group)

    @staticmethod
    def vote(thread_id: int, user: User, val: bool = None):
        return generate_request(api=GroupThreadVoteUpdateAPI,
                                data=dict(vote=val) if val is not None else None,
                                url_params=dict(thread_id=thread_id),
                                user=user)

    def test_vote(self):
        thread_id = self.threads[0].id
        user = self.group_user.user

        # Vote is True
        response = self.vote(thread_id, user, True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vote = GroupThreadVote.objects.get(thread_id=thread_id, created_by=self.group_user)

        # Vote is False
        response = self.vote(thread_id, user, False)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vote = GroupThreadVote.objects.get(thread_id=thread_id, created_by=self.group_user)

        # Vote is None
        response = self.vote(thread_id, user, None)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with self.assertRaises(GroupThreadVote.DoesNotExist):
            GroupThreadVote.objects.get(thread_id=thread_id, created_by=self.group_user)

        # Vote is None and still cast None
        response = self.vote(thread_id, user, None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
