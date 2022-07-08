import datetime
import hashlib
import json
import random

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.test import TestCase

from flowback.users.models import GroupMembers
from flowback.users.tests import UserFactory, GroupFactory, GroupMembersFactory

from flowback.polls.services import create_poll_receipt, check_poll
from flowback.polls.helper import PollAdapter
from flowback.polls.models import Poll, PollProposal, PollProposalEvent, PollProposalIndex, PollProposalEventIndex, \
    PollUserDelegate


class PollFactory(DjangoModelFactory):
    class Meta:
        model = Poll

    created_by = factory.SubFactory(UserFactory)
    modified_by = factory.LazyAttribute(lambda o: o.created_by)
    group = factory.SubFactory(GroupFactory, created_by=created_by)
    title = factory.Faker('company')
    description = factory.Faker('bs')

    type = Poll.Type.POLL
    voting_type = Poll.VotingType.CONDORCET

    start_time = datetime.datetime.now()
    end_time = datetime.datetime.now()


class PollProposalFactory(DjangoModelFactory):
    class Meta:
        model = PollProposal

    user = factory.SubFactory(UserFactory)
    poll = factory.SubFactory(GroupFactory, created_by=user)
    type = PollProposal.Type.DEFAULT
    proposal = factory.Faker('bs')


class PollProposalEventFactory(DjangoModelFactory):
    class Meta:
        model = PollProposalEvent

    user = factory.SubFactory(UserFactory)
    poll = factory.SubFactory(GroupFactory, created_by=user)
    type = PollProposal.Type.DEFAULT
    proposal = factory.Faker('bs')
    date = datetime.datetime.now() + datetime.timedelta(hours=1)


class PollProposalIndexFactory(DjangoModelFactory):
    class Meta:
        model = PollProposalIndex

    user = factory.SubFactory(UserFactory)
    proposal = factory.SubFactory(PollProposalFactory, user=user)
    priority = 0
    is_positive = True
    hash = 'magic_hash'


class PollProposalEventIndexFactory(DjangoModelFactory):
    class Meta:
        model = PollProposalEventIndex

    user = factory.SubFactory(UserFactory)
    proposal = factory.SubFactory(PollProposalEventFactory, user=user)
    priority = 0
    is_positive = True
    hash = 'magic_hash'


class PollTestCase(TestCase):
    def test_create_poll_receipt(self):
        owner, member1, member2, member3, delegator, \
        delegate1, delegate2, delegate3 = UserFactory.create_batch(8)

        users = [owner, member1, member2, member3, delegator]
        delegates = [delegate1, delegate2, delegate3]

        group = GroupFactory(
            created_by=owner,
            owners=[owner],
            delegators=[delegator],
            members=[member1, member2, member3, delegate1, delegate2, delegate3]
        )

        poll = PollFactory(created_by=owner, voting_type=Poll.VotingType.CARDINAL, group=group)

        proposal1, proposal2, proposal3 = [
            PollProposalFactory(poll=poll, user=user)
            for user in [member1, member2, member3]
        ]
        proposals = [proposal1, proposal2, proposal3]

        for user in users:
            GroupMembersFactory(user=user, group=group)

            for proposal in proposals:
                PollProposalIndexFactory(user=user, proposal=proposal, priority=random.randint(0, 2000))

        for delegate in delegates:
            GroupMembersFactory(user=delegate, group=group)
            PollUserDelegate.objects.create(
                user=delegate,
                group=group,
                delegator=delegator
            ).save()

        check_poll(poll)
        receipt = json.dumps(create_poll_receipt(poll=poll.id))
        final_hash = hashlib.sha512(receipt.encode('utf-8')).hexdigest()
        print(receipt)
        print(final_hash)
