import json

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate, APITransactionTestCase
from .factories import PollFactory, PollProposalFactory

from .utils import generate_poll_phase_kwargs
from ..models import PollProposal, Poll
from ..views.proposal import PollProposalListAPI, PollProposalCreateAPI, PollProposalDeleteAPI
from ...files.tests.factories import FileSegmentFactory
from ...group.tests.factories import GroupFactory, GroupUserFactory, GroupTagsFactory
from ...user.models import User


class ProposalTest(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.group = GroupFactory()
        self.group_tag = GroupTagsFactory(group=self.group)
        self.group_user_creator = GroupUserFactory(group=self.group, user=self.group.created_by)
        (self.group_user_one,
         self.group_user_two,
         self.group_user_three) = GroupUserFactory.create_batch(3, group=self.group)
        self.poll_schedule = PollFactory(created_by=self.group_user_one, poll_type=Poll.PollType.SCHEDULE)
        self.poll_ranking = PollFactory(created_by=self.group_user_one, poll_type=Poll.PollType.RANKING)
        group_users = [self.group_user_one, self.group_user_two, self.group_user_three]
        (self.poll_schedule_proposal_one,
         self.poll_schedule_proposal_two,
         self.poll_schedule_proposal_three) = [PollProposalFactory(created_by=x,
                                                                   poll=self.poll_schedule) for x in group_users]
        (self.poll_ranking_proposal_one,
         self.poll_ranking_proposal_two,
         self.poll_ranking_proposal_three) = [PollProposalFactory(created_by=x,
                                                                  poll=self.poll_ranking) for x in group_users]

    def test_proposal_list(self):
        factory = APIRequestFactory()
        user = self.group_user_one.user
        view = PollProposalListAPI.as_view()
        request = factory.get('')
        force_authenticate(request, user=user)

        response = view(request, poll=self.poll_schedule.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count, 3)
