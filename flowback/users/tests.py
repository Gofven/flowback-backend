import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.test import TestCase

from flowback.exceptions import PermissionDenied
from flowback.polls.models import PollUserDelegate
from flowback.users.models import User, Group, GroupMembers
from flowback.users.services import group_user_permitted, group_member_update

import datetime


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"person_{n}")
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    accepted_terms_condition = True


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    title = factory.Faker('company')
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.LazyAttribute(lambda o: o.created_by)

    @factory.post_generation
    def owners(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for owner in extracted:
                self.owners.add(owner)

    @factory.post_generation
    def admins(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for admin in extracted:
                self.admins.add(admin)

    @factory.post_generation
    def moderators(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for moderator in extracted:
                self.moderators.add(moderator)


    @factory.post_generation
    def delegators(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for delegator in extracted:
                self.delegators.add(delegator)

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for member in extracted:
                self.members.add(member)


class GroupMembersFactory(DjangoModelFactory):
    class Meta:
        model = GroupMembers

    user = factory.SubFactory(UserFactory)
    group = factory.SubFactory(GroupFactory)
    allow_vote = True


class UserTestCase(TestCase):
    def test_group_user_permitted(self):
        test_user = UserFactory.create()
        test_user_2 = UserFactory.create()
        guest, member, delegator, moderator, admin, owner = UserFactory.create_batch(6)

        group = GroupFactory(created_by=owner, updated_by=owner)
        group.owners.add(owner)
        group.admins.add(admin)
        group.moderators.add(moderator)
        group.delegators.add(delegator)
        group.members.add(member)
        group.save()

        permissions = ['owner', 'admin', 'moderator', 'delegator', 'member', 'guest']
        member_permissions = ((owner, 0), (admin, 1), (moderator, 2), (delegator, 3),
                              (member, 3), (guest, 5))

        for user, perms in member_permissions:
            for permission in permissions[perms:]:
                self.assertTrue(group_user_permitted(
                    user=user.id,
                    group=group.id,
                    permission=permission
                    )
                )

            for permission in permissions[:perms]:
                self.assertFalse(group_user_permitted(
                    user=user.id,
                    group=group.id,
                    permission=permission,
                    raise_exception=False
                    )
                )

    def test_group_member_update(self):
        admin, member, user = [UserFactory.create() for x in range(3)]

        group = GroupFactory(created_by=admin, updated_by=admin)
        group.admins.add(admin)
        group.members.add(member)
        group.save()

        tests = [
            [admin, member, True, True],
            [admin, user, True, False],
            [member, admin, True, False],
            [admin, member, False, True],
            [admin, user, False, False],
            [member, admin, False, False]
        ]

        for user, target, allow_vote, passing in tests:
            if passing:
                self.assertTrue(group_member_update(
                    user=user.id,
                    target=target.id,
                    group=group.id,
                    allow_vote=allow_vote
                ))

            else:
                self.assertRaises(
                    PermissionDenied,
                    group_member_update,
                    user=user.id,
                    target=target.id,
                    group=group.id,
                    allow_vote=allow_vote
                )
