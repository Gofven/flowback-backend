import json
from pprint import pprint

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate, APITransactionTestCase

from flowback.common.tests import generate_request
from flowback.group.models import GroupUser, Group, GroupUserInvite, WorkGroup, WorkGroupUser, WorkGroupUserJoinRequest
from flowback.group.tests.factories import GroupFactory, GroupUserFactory, WorkGroupUserFactory, WorkGroupFactory, \
    WorkGroupJoinRequestFactory
from flowback.group.views.group import GroupListApi, GroupCreateApi, WorkGroupCreateAPI, WorkGroupUpdateAPI, \
    WorkGroupDeleteAPI, WorkGroupUserJoinAPI, WorkGroupUserLeaveAPI, WorkGroupUserAddAPI, WorkGroupUserListAPI, \
    WorkGroupUserJoinRequestListAPI, WorkGroupListAPI
from flowback.group.views.user import GroupInviteApi, GroupJoinApi, GroupInviteAcceptApi, GroupInviteListApi, \
    GroupUserListApi
from flowback.user.models import User
from flowback.user.tests.factories import UserFactory


class GroupTest(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        (self.group_one,
         self.group_two,
         self.group_three) = [GroupFactory.create(public=True) for x in range(3)]

        (self.group_user_creator_one,
         self.group_user_creator_two,
         self.group_user_creator_three) = [GroupUserFactory.create(group=group, user=group.created_by
                                                                   ) for group in [self.group_one,
                                                                                   self.group_two,
                                                                                   self.group_three]]

        self.group_no_direct = GroupFactory.create(public=True, direct_join=False)
        self.group_no_direct_user_creator = GroupUserFactory.create(group=self.group_no_direct,
                                                                    user=self.group_no_direct.created_by)

        self.group_private = GroupFactory.create(public=False)
        self.group_private_user_creator = GroupUserFactory.create(group=self.group_private,
                                                                  user=self.group_private.created_by)

        self.groupless_user = UserFactory()

    def test_group_list(self):
        factory = APIRequestFactory()
        user = self.group_user_creator_two.user
        view = GroupListApi.as_view()

        request = factory.get('', data=dict(limit=10))
        force_authenticate(request, user=user)
        response = view(request)

        data = json.loads(response.rendered_content)
        pprint(data)

    # Also tests if work_group is being displayed in response
    def test_group_user_list(self):
        work_group_user = WorkGroupUserFactory(group_user=self.group_user_creator_one)

        response = generate_request(api=GroupUserListApi,
                                    url_params=dict(group=self.group_user_creator_one.group.id),
                                    user=self.group_user_creator_one.user)

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['work_groups'][0], work_group_user.work_group.name)

    def test_group_create(self):
        factory = APIRequestFactory()
        user = self.group_user_creator_two.user
        view = GroupCreateApi.as_view()
        data = dict(name="test",
                    description="test",
                    direct_join=True)

        request = factory.post('', data=data)
        force_authenticate(request, user=user)
        response = view(request)

        data = json.loads(response.rendered_content)
        pprint(data)

    def group_invite(self, group_user: GroupUser, to: User):
        factory = APIRequestFactory()
        view = GroupInviteApi.as_view()

        request = factory.post('', data=dict(to=to.id))
        force_authenticate(request, group_user.user)
        return view(request, group=group_user.group)

    def group_join(self, user: User, group: Group):
        factory = APIRequestFactory()
        view = GroupJoinApi.as_view()

        request = factory.post('')
        force_authenticate(request, user)
        return view(request, group=group.id)

    def test_group_invite(self):
        response = self.group_invite(self.group_no_direct_user_creator, self.groupless_user)
        pprint(response.data)

    def test_group_invite_accept(self):
        self.group_invite(self.group_no_direct_user_creator, self.groupless_user)

        factory = APIRequestFactory()
        user = self.groupless_user
        view = GroupInviteAcceptApi.as_view()
        request = factory.post('')
        force_authenticate(request, user)
        view(request, group=self.group_no_direct.id)

        self.assertTrue(GroupUser.objects.filter(user_id=self.groupless_user, group=self.group_no_direct).exists())

    def test_group_invite_accept_no_invite(self):
        factory = APIRequestFactory()
        user = self.groupless_user
        view = GroupInviteAcceptApi.as_view()
        request = factory.post('')
        force_authenticate(request, user)
        view(request, group=self.group_no_direct.id)

        self.assertFalse(GroupUser.objects.filter(user_id=self.groupless_user, group=self.group_no_direct).exists())

    def test_group_request_invite(self):
        self.group_join(self.groupless_user, self.group_no_direct)
        self.assertTrue(GroupUserInvite.objects.filter(user=self.groupless_user, group=self.group_no_direct).exists())

    def test_group_request_invite_accept(self):
        self.group_join(self.groupless_user, self.group_no_direct)

        factory = APIRequestFactory()
        user = self.group_no_direct_user_creator.user
        view = GroupInviteAcceptApi.as_view()
        request = factory.post('', data=dict(to=self.groupless_user.id))
        force_authenticate(request, user)
        view(request, group=self.group_no_direct.id)

        self.assertTrue(GroupUser.objects.filter(user_id=self.groupless_user, group=self.group_no_direct).exists())

    def test_group_request_invite_accept_no_invite(self):
        factory = APIRequestFactory()
        user = self.group_no_direct_user_creator.user
        view = GroupInviteAcceptApi.as_view()
        request = factory.post('', data=dict(to=self.groupless_user.id))
        force_authenticate(request, user)
        view(request, group=self.group_no_direct.id)

        self.assertFalse(GroupUser.objects.filter(user_id=self.groupless_user, group=self.group_no_direct).exists())

    def test_user_invite_list(self):
        self.group_invite(self.group_no_direct_user_creator, self.groupless_user)
        self.group_invite(self.group_private_user_creator, self.groupless_user)

        factory = APIRequestFactory()
        user = self.groupless_user
        view = GroupInviteListApi.as_view()

        request = factory.get('', data=dict(limit=10))
        force_authenticate(request, user=user)
        response = view(request)

        pprint(response.data)

    def test_user_group_join_request_list(self):
        self.group_join(self.groupless_user, self.group_no_direct)
        self.group_join(self.groupless_user, self.group_private)

        for group_user, allowed in [(self.group_private_user_creator, False),
                                    (self.group_no_direct_user_creator, True)]:
            factory = APIRequestFactory()
            user = group_user.user
            view = GroupInviteListApi.as_view()

            request = factory.get('', data=dict(limit=10))
            force_authenticate(request, user=user)
            response = view(request, group=group_user.group)

            self.assertTrue(bool(response.data.get('results')) == allowed)

    # Work Group Test
    def test_work_group_list(self):
        work_group_one = WorkGroupFactory(group=self.group_user_creator_one)
        work_group_two = WorkGroupFactory(group=self.group_user_creator_one)

        # Irrelevant work group, for testing purpose
        WorkGroupFactory(group=self.group_user_creator_two)

        response = generate_request(api=WorkGroupListAPI,
                                    user=self.group_user_creator_one.user,
                                    url_params=dict(group_id=self.group_user_creator_one.group.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], work_group_one.id)
        self.assertEqual(response.data['results'][1]['id'], work_group_two.id)

    def test_work_group_user_list(self):
        work_group_one = WorkGroupFactory(group=self.group_user_creator_one)
        work_group_two = WorkGroupFactory(group=self.group_user_creator_one)
        work_group_user_one = WorkGroupUserFactory(group_user__group=self.group_user_creator_one,
                                                   work_group=work_group_one)
        work_group_user_two = WorkGroupUserFactory(group_user__group=self.group_user_creator_one,
                                                   work_group=work_group_one)

        # Irrelevant work group user, for testing purpose
        WorkGroupUserFactory(group_user__group=self.group_user_creator_one, work_group=work_group_two)

        response = generate_request(api=WorkGroupUserListAPI,
                                    user=self.group_user_creator_one.user,
                                    url_params=dict(work_group_id=work_group_one.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['group_user']['user']['id'],
                         work_group_user_one.group_user.user.id)
        self.assertEqual(response.data['results'][1]['group_user']['user']['id'],
                         work_group_user_two.group_user.user.id)

    def test_work_group_user_join_request_list(self):
        work_group_one = WorkGroupFactory(group=self.group_user_creator_one)
        work_group_two = WorkGroupFactory(group=self.group_user_creator_one)
        work_group_user_one = WorkGroupUserFactory(group_user__group=self.group_user_creator_one,
                                                   work_group=work_group_one)
        WorkGroupUserFactory(group_user__group=self.group_user_creator_one, work_group=work_group_one)

        # Join Request
        join_request = WorkGroupJoinRequestFactory(group_user__group=self.group_user_creator_one,
                                                   work_group=work_group_one)

        # Irrelevant work group user, for testing purpose
        WorkGroupUserFactory(group_user__group=self.group_user_creator_one, work_group=work_group_two)
        WorkGroupJoinRequestFactory(group_user__group=self.group_user_creator_one, work_group=work_group_two)

        response = generate_request(api=WorkGroupUserJoinRequestListAPI,
                                    user=work_group_user_one.user,
                                    url_params=dict(work_group_id=work_group_one.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['group_user']['user']['id'],
                         join_request.group_user.user.id)

    def test_work_group_create(self):
        data = dict(name="test_work_group", direct_join=True)

        response = generate_request(api=WorkGroupCreateAPI,
                                    data=data,
                                    url_params=dict(group_id=self.group_user_creator_one.group.id),
                                    user=self.group_user_creator_one.user)

        work_group = WorkGroup.objects.get(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(work_group.name, data['name'])
        self.assertEqual(work_group.group, self.group_user_creator_one.group)
        self.assertEqual(work_group.direct_join, data['direct_join'])

    def test_work_group_update(self):
        work_group = WorkGroupFactory(user=self.group_user_creator_one.user, name="test_old", direct_join=False)
        data = dict(name="test_updated", direct_join=True)

        response = generate_request(api=WorkGroupUpdateAPI,
                                    data=data,
                                    url_params=dict(work_group_id=work_group.id),
                                    user=self.group_user_creator_one.user)

        work_group.refresh_from_db()
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertEqual(work_group.name, data['name'])
        self.assertEqual(work_group.direct_join, data['direct_join'])

    def test_work_group_delete(self):
        work_group = WorkGroupFactory(user=self.group_user_creator_one.user, name="test_old", direct_join=False)

        response = generate_request(api=WorkGroupDeleteAPI,
                                    url_params=dict(work_group_id=work_group.id),
                                    user=self.group_user_creator_one.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(WorkGroup.objects.filter(id=work_group.id).exists())

    # Work Group User Test
    def test_work_group_user_join(self):
        work_group = WorkGroupFactory(user=self.group_user_creator_one.user, direct_join=False)

        response = generate_request(api=WorkGroupUserJoinAPI,
                                    url_params=dict(work_group_id=work_group.id),
                                    user=self.group_user_creator_one.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(WorkGroupUser.objects.filter(id=work_group.id).exists())

    def test_work_group_user_leave(self):
        work_group_user = WorkGroupUserFactory(group_user=self.group_user_creator_one)

        response = generate_request(api=WorkGroupUserLeaveAPI,
                                    url_params=dict(work_group_id=work_group_user.work_group.id),
                                    user=self.group_user_creator_one.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(WorkGroupUser.objects.filter(id=work_group_user.work_group.id).exists())

    def test_work_group_user_invite(self):
        group_user = GroupUserFactory(group=self.group_user_creator_one.group)
        work_group = WorkGroupFactory(user=self.group_user_creator_one.user, direct_join=False)

        response = generate_request(api=WorkGroupUserAddAPI,
                                    url_params=dict(work_group_id=work_group.id),
                                    data=dict(target_user_id=group_user.id, is_moderator=False),
                                    user=self.group_user_creator_one.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(WorkGroupUser.objects.filter(group_user=group_user, work_group=work_group).exists())
        self.assertTrue(WorkGroupUserJoinRequest.objects.filter(group_user=group_user, work_group=work_group).exists())

        # Accept invite
        response = generate_request(api=WorkGroupUserJoinAPI,
                                    url_params=dict(work_group_id=work_group.id),
                                    user=group_user.user)

        response.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(WorkGroupUser.objects.filter(group_user=group_user, work_group=work_group).exists())
        self.assertFalse(WorkGroupUserJoinRequest.objects.filter(group_user=group_user, work_group=work_group).exists())

    def test_work_group_user_direct_join(self):
        group_user = GroupUserFactory(group=self.group_user_creator_one.group)
        work_group = WorkGroupFactory(user=self.group_user_creator_one.user, direct_join=True)

        response = generate_request(api=WorkGroupUserAddAPI,
                                    url_params=dict(work_group_id=work_group.id),
                                    data=dict(target_user_id=group_user.id, is_moderator=False),
                                    user=self.group_user_creator_one.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(WorkGroupUser.objects.filter(group_user=group_user, work_group=work_group).exists())
