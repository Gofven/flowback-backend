import json

from rest_framework import status
from rest_framework.test import APITransactionTestCase, APIRequestFactory, force_authenticate

from flowback.chat.models import MessageChannel, MessageChannelParticipant
from flowback.chat.tests.factories import MessageChannelFactory
from flowback.comment.tests.factories import CommentFactory
from flowback.common.tests import generate_request
from flowback.group.tests.factories import GroupThreadFactory, GroupUserFactory
from flowback.poll.tests.factories import PollFactory
from flowback.user.models import User, UserChatInvite
from flowback.user.services import user_create, user_create_verify
from flowback.user.tests.factories import UserFactory
from flowback.user.views.home import UserHomeFeedAPI
from flowback.user.views.user import UserDeleteAPI, UserGetChatChannelAPI, UserUpdateApi, UserChatInviteAPI


class UserTest(APITransactionTestCase):
    def setUp(self):
        (self.user_one,
         self.user_two,
         self.user_three) = (UserFactory() for x in range(3))

    def test_user_delete(self):
        user = self.user_one

        factory = APIRequestFactory()
        view = UserDeleteAPI.as_view()
        request = factory.post('')
        force_authenticate(request, user=user)
        view(request)

        user.refresh_from_db()
        self.assertTrue(user.username.startswith('deleted_user'))
        self.assertTrue(user.email.startswith('deleted_user'))

        self.assertTrue(not all([user.is_active,
                                 user.email_notifications,
                                 user.profile_image,
                                 user.banner_image,
                                 user.bio,
                                 user.website,
                                 user.kanban,
                                 user.schedule]))

    def test_user_create(self):
        code = user_create(username="test_user", email="test@example.com")
        user = user_create_verify(verification_code=code, password="password123")

        self.assertTrue(User.objects.filter(id=user.id).exists())

    def test_user_update(self):
        user = UserFactory()
        generate_request(UserUpdateApi,
                         data={"contact_phone": "+46701234567"},
                         user=user)

        self.assertEqual(User.objects.get(id=user.id).contact_phone, "+46701234567")

    def test_user_home_feed(self):
        group_user, group_user_three = GroupUserFactory.create_batch(size=2, group__public=False)
        group_user_two = GroupUserFactory(group__public=True)

        GroupThreadFactory.create_batch(size=2)
        PollFactory.create_batch(size=5, created_by=group_user)

        PollFactory.create_batch(size=5, created_by=group_user_two)
        GroupThreadFactory.create_batch(size=5, created_by=group_user_two)

        polls = PollFactory.create_batch(size=5, created_by=group_user_three)
        poll_with_comments = polls[0] # Testing total comments aggregate
        CommentFactory.create_batch(size=5,
                                    author=group_user_three.user,
                                    comment_section=poll_with_comments.comment_section)

        GroupThreadFactory.create_batch(size=5, created_by=group_user_three)

        response = generate_request(api=UserHomeFeedAPI, user=group_user.user)

        # Check if order_by is for created_at, in descending order
        for x in range(1, response.data['count']):
            self.assertTrue(response.data['results'][x]['created_at'] < response.data['results'][x - 1]['created_at'])

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['count'], 17)

        # Test total_comments
        # response = generate_request(api=UserHomeFeedAPI,
        #                             user=group_user_three.user,
        #                             data=dict(related_model="poll", id=poll_with_comments.id))
        #
        # self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # self.assertEqual(response.data['count'], 1)
        # self.assertEqual(response.data['results'][0]['total_comments'], 5)

    def test_user_get_chat_channel(self):
        participants = UserFactory.create_batch(25)

        response = generate_request(api=UserGetChatChannelAPI,
                                    data=dict(target_user_ids=[u.id for u in participants]),
                                    user=self.user_one)

        # Run second time to make sure we get the same channel_id
        response_two = generate_request(api=UserGetChatChannelAPI,
                                        data=dict(target_user_ids=[u.id for u in participants]),
                                        user=self.user_one)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response_two.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(response.data['id'], response_two.data['id'])
        self.assertTrue(MessageChannel.objects.filter(id=response.data['id']).exists())

        # Count all participants + the user itself
        self.assertEqual(MessageChannelParticipant.objects.filter(channel_id=response.data['id']).count(), 26)

    def test_user_get_chat_channel_invite(self):
        participants = UserFactory.create_batch(25, direct_message=False)

        response = generate_request(api=UserGetChatChannelAPI,
                                    data=dict(target_user_ids=[u.id for u in participants]),
                                    user=self.user_one)

        channel_id = response.data['id']
        self.assertEqual(UserChatInvite.objects.all().count(), 25)
        self.assertEqual(MessageChannelParticipant.objects.filter(channel_id=channel_id, active=True).count(),
                         1)

        for i, user in enumerate(participants):
            response = generate_request(api=UserChatInviteAPI,
                                        data=dict(invite_id=UserChatInvite.objects.get(user=user).id,
                                                  accept=True if i <= 9 else False),
                                        user=user)

            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(MessageChannelParticipant.objects.filter(channel_id=channel_id, active=True).count(), 11)
        self.assertEqual(UserChatInvite.objects.filter(rejected=True).count(), 15)

        response = generate_request(api=UserGetChatChannelAPI,
                                    data=dict(target_user_ids=[u.id for u in participants]),
                                    user=self.user_one)

        self.assertEqual(response.data['id'], channel_id, "Channel ID should not have changed")

        self.assertEqual(UserChatInvite.objects.all().count(), 25)
        self.assertEqual(UserChatInvite.objects.filter(rejected=True).count(), 0)
