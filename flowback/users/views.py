import string
import random
import datetime

from random import randint
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import decorators, viewsets, status, serializers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.paginator import Paginator
from django.db.models import Count, Value as V
from django.db.models.functions import Concat

from flowback.response import Created, BadRequest
from flowback.response import Ok
from flowback.response_handler import success_response, failed_response
from flowback.users.models import Group, GroupMembers, OnboardUser, GroupDocs, GroupRequest, FriendChatMessage, \
    GroupChatMessage
from flowback.users.models import User, PasswordReset
from flowback.users.models import Country, State, City
from flowback.users.models import Friends
from flowback.polls.models import Poll
from flowback.users.selectors import group_members_get
from flowback.users.serializer import UserGroupCreateSerializer, MyGroupSerializer, AddParticipantSerializer, \
    OnboardUserFirstSerializer, OnboardUserSecondSerializer, GroupParticipantSerializer, CreateGroupRequestSerializer, \
    UpdateGroupRequestSerializer, GetChatMessagesSerializer, GetAllGroupRoomsSerializer, GetGroupChatMessagesSerializer
from flowback.users.serializer import UserSerializer, SimpleUserSerializer, UserRegistrationSerializer, \
    GroupDetailsSerializer, CreateGroupDocSerializer, GroupDocsListSerializer, GetGroupJoinRequestListSerializer, \
    SearchGroupSerializer, GetAllCountrySerializer, GetAllStatesByCountries, GetAllCityByStateSerializer, \
    ResetPasswordSerializer, ResetPasswordVerifySerializer
from flowback.users.serializer import CreateFriendRequestSerializer, GetAllFriendRequestSerializer, \
    GetAllFriendsRoomSerializer
from flowback.polls.serializer import SearchPollSerializer
from flowback.users.services import group_member_update, group_user_permitted, mail_all_group_members, leave_group
from settings.base import EMAIL_HOST_USER, DEBUG, NOREG


class UserViewSet(viewsets.ViewSet):
    """
    this class is use for sign up the user by multiple step
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @decorators.action(detail=False, methods=['post'], url_path="sign_up_first")
    def sign_up_first(self, request, *args, **kwargs):
        data = request.data
        # serializer for sign up user for first step
        serializer = OnboardUserFirstSerializer(data=data)

        if NOREG:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if serializer.is_valid(raise_exception=False):
            verification_code = randint(100000, 999999)
            user_onboard = OnboardUser.objects.filter(email=serializer.validated_data.get('email')).first()
            if user_onboard:
                if not user_onboard.is_verified:
                    user_onboard.screen_name = serializer.validated_data.get('screen_name')
                    user_onboard.verification_code = verification_code
                    user_onboard.save()
                    # send email with verification code
                    send_mail('Flowback Verification Code', 'Please Enter This Code: %s' % (verification_code),
                              EMAIL_HOST_USER,
                              [str(serializer.data.get('email'))])
                    if DEBUG:
                        print(verification_code)
                    result = success_response(data=None, message="")
                    return Created(result)
                else:
                    result = failed_response(data="Already verified with this email", message="")
                    return BadRequest(result)
            else:
                # sign up user for first step
                OnboardUser.objects.create(email=serializer.validated_data.get('email'),
                                           screen_name=serializer.validated_data.get('screen_name'),
                                           verification_code=verification_code)
                send_mail('Flowback Verification Code', 'Please Enter This Code: %s' % (verification_code),
                          EMAIL_HOST_USER,
                          [str(serializer.data.get('email'))])
                if DEBUG:
                    print(verification_code)
                result = success_response(data=None, message="")
                return Created(result)

        else:
            result = failed_response(data=serializer.errors, message="")
            return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path="reset-password-one")
    def reset_password_one(self, request):
        data = request.data
        serializer = ResetPasswordSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = get_object_or_404(User, **serializer.data)
        code = random.randint(100000, 999999)
        PasswordReset.objects.create(user=user, verification_code=code)
        send_mail('Flowback Reset Password', 'Please Enter This Code: %s' % (code),
                  EMAIL_HOST_USER,
                  [str(serializer.data.get('email'))])
        print(code)

        return Response(status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['post'], url_path="reset-password-two")
    def reset_password_two(self, request):
        data = request.data
        serializer = ResetPasswordVerifySerializer(data=data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        code = serializer.validated_data.get('verification_code')
        password = serializer.validated_data.get('password')
        verification = get_object_or_404(PasswordReset, user__email=email, verification_code=code)

        verification.user.set_password(password)
        verification.user.save()
        return Response(status=status.HTTP_200_OK)

    @decorators.action(detail=False, methods=['post'], url_path="sign_up_two")
    def sign_up_two(self, request, *args, **kwargs):
        data = request.data
        # serializer for final step for sign up the user
        serializer = OnboardUserSecondSerializer(data=data)

        if NOREG:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if serializer.is_valid(raise_exception=False):
            user_onboard = OnboardUser.objects.filter(email=serializer.validated_data.get('email')).first()
            if user_onboard:
                if not user_onboard.is_verified:
                    # if verification code is right then sign up the user
                    if serializer.validated_data.get('verification_code') == user_onboard.verification_code:
                        user_onboard.is_verified = True
                        user_onboard.save()
                        result = success_response(data=None, message="")
                        return Created(result)
                    else:
                        result = failed_response(data="Invalid verification code", message="")
                        return BadRequest(result)
                else:
                    result = failed_response(data="Already verified with this email", message="")
                    return BadRequest(result)
            else:
                result = failed_response(data="No user found with this email", message="")
                return BadRequest(result)

        else:
            result = failed_response(data=serializer.errors, message="")
            return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path="sign_up_three")
    def sign_up_three(self, request, *args, **kwargs):

        if NOREG:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data
        user_onboard = OnboardUser.objects.filter(email=data.get('email')).first()
        if user_onboard:
            if user_onboard.is_verified:
                serializer = UserRegistrationSerializer(data=data)
                if serializer.is_valid(raise_exception=False):
                    user = serializer.save()
                    user.first_name = user_onboard.screen_name
                    user.save()
                    result = success_response(data=None, message="")
                    return Created(result)
                else:
                    result = failed_response(data=serializer.errors, message="")
                    return BadRequest(result)
            else:
                result = failed_response(data='First verify your email', message="")
                return BadRequest(result)
        else:
            result = failed_response(data='Email Not Exist', message="")
            return BadRequest(result)


class CurrentUserViewSet(viewsets.GenericViewSet):
    """
    this class is use for get user profile details
    """
    serializer_class = SimpleUserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.queryset.get(id=self.request.user.id)

    def get_object_by_id(self, user_id):
        return self.queryset.get(id=user_id)

    def list(self, request):
        serializer = self.get_serializer(self.get_object())
        data = serializer.data
        result = success_response(data=data, message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path="profile")
    def profile(self, request):
        # get user object and update the profile details
        instance = self.get_object()
        instance.first_name = request.data.get('first_name', instance.first_name)
        instance.last_name = request.data.get('last_name', instance.last_name)
        instance.bio = request.data.get('bio', instance.bio)
        instance.image = request.data.get('image', instance.image)
        instance.cover_image = request.data.get('cover_image', instance.cover_image)
        # instance.phone_number = request.data.get('phone_number', instance.phone_number)
        instance.website = request.data.get('website', instance.website)
        instance.country = request.data.get('country', instance.country)
        instance.city = request.data.get('city', instance.city)
        instance.save()
        serializer = self.get_serializer(instance)
        data = serializer.data
        result = success_response(data=data, message="")
        return Created(result)

    @decorators.action(detail=False, methods=['get'], url_path='get_public_key')
    def get_public_key_api(self, request):
        class OutputSerializer(serializers.Serializer):
            address = serializers.CharField(allow_null=True, allow_blank=True)
            public_key = serializers.CharField(allow_null=True, allow_blank=True)

        user = request.user
        return Response(data=OutputSerializer(user).data)

    @decorators.action(detail=False, methods=['post'], url_path='update_public_key')
    def update_public_key_api(self, request):
        class InputSerializer(serializers.Serializer):
            address = serializers.CharField(allow_null=True, allow_blank=True)
            public_key = serializers.CharField(allow_null=True, default=None)

        user = request.user
        serializer = InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.public_key = serializer.validated_data.get('public_key')
        user.address = serializer.validated_data.get('address')
        user.save()
        return Response(status=status.HTTP_200_OK)

    @decorators.action(detail=False, methods=['post'], url_path='get-my-data')
    def get_logged_in_user(self, request):
        # get details of logged in user
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        result = success_response(data=data, message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path='get-other-user')
    def get_other_user(self, request):
        try:
            data = self.request.data
            # get user details by user id
            instance = self.get_object_by_id(user_id=data.get('id'))
            serializer = self.get_serializer(instance, context={'request': self.request})
            data = serializer.data
            result = success_response(data=data, message="")
            return Ok(result)
        except Exception as e:
            result = failed_response(data={}, message=str(e))
            return BadRequest(result)


class UserLogin(ObtainAuthToken):
    """
    Generate user's authentication token.
    Token authentication is done using this header: "Authorization: Token TOKEN_HERE"
    """

    def post(self, request, *args, **kwargs):
        # serializer for token auth
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})

        if serializer.is_valid(raise_exception=False):
            user = serializer.validated_data['user']
            # create or get token for user
            token, created = Token.objects.get_or_create(user=user)
            user_serializer = SimpleUserSerializer(user)
            # return the created token in response with required user details
            result = success_response(data={'token': token.key, 'user': user_serializer.data}, message="")
            return Ok(result)
        else:
            result = failed_response(data=serializer.errors, message="")
            return BadRequest(result)


class UserLogout(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # simply delete the token to force a login
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class UserGroupViewSet(viewsets.ViewSet):
    """
    This class is used for create, update or delete all the things related to group
    """
    serializer_class = UserGroupCreateSerializer
    permission_classes = [IsAuthenticated]

    @decorators.action(detail=False, methods=['post'], url_path="create_group")
    def create_group(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=False):
            # create or get the group
            group, created = Group.objects.get_or_create(created_by=request.user,
                                                         updated_by=request.user,
                                                         title=serializer.validated_data.get('title'),
                                                         description=serializer.validated_data.get('description'),
                                                         public=serializer.validated_data.get('public'),
                                                         members_request=serializer.validated_data.get(
                                                             'members_request'),
                                                         poll_approval=serializer.validated_data.get('poll_approval'),
                                                         country=serializer.validated_data.get('country'),
                                                         city=serializer.validated_data.get('city'),
                                                         )
            group.owners.add(request.user)
            if serializer.validated_data.get('image'):
                group.image = serializer.validated_data.get('image')
            if serializer.validated_data.get('cover_image'):
                group.cover_image = serializer.validated_data.get('cover_image')
            if data.get('tags'):
                tags = data.get('tags').split(' ')
                # add all #hashtag in group
                for tag in tags:
                    group.tag.add(tag)
            group.save()
            group_member_update(target=user.id, group=group.id, allow_vote=True)

            # create room name for group chat
            letters = string.ascii_letters
            random_string = "".join(random.choice(letters) for i in range(5))

            room_name = "{}_{}".format(group.id, random_string)
            group.room_name = room_name
            group.save()

            result = success_response(data=None, message="")
            return Created(result)

        else:
            result = failed_response(data=serializer.errors, message="")
            return BadRequest(result)

    # @decorators.action(detail=False, methods=['post'], url_path="direct_join_to_group")
    # def direct_join_to_group(self, request, *args, **kwargs):
    #     user = request.user
    #     data = request.data
    #     group = Group.objects.filter(id=data.get('group_id')).first()
    #     if group:
    #         if group.members_request == 'direct_join':
    #             group.members.add(user)
    #             group.save()
    #             result = success_response(data={}, message="")
    #             return Ok(result)
    #         result = failed_response(data={}, message="Don't have permission to direct join the group.")
    #         return BadRequest(result)
    #     result = failed_response(data={}, message="Group is does not exist.")
    #     return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path="update_group_member_type")
    def update_group_member_type(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        # get group object by group id
        group = Group.objects.filter(id=data.get('group_id')).first()
        if group:
            # check the user role
            if user in group.owners.all() or user in group.admins.all():
                user_id = data.get('user_id')
                old_user_type = data.get('old_user_type')
                new_user_type = data.get('new_user_type')
                participant = User.objects.filter(id=user_id).first()
                if participant:
                    # based on old user type update the new role and remove old role
                    if old_user_type == "Admin":
                        if new_user_type == 'Moderator':
                            group.admins.remove(participant)
                            group.moderators.add(participant)
                        elif new_user_type == 'Member':
                            group.admins.remove(participant)
                            group.members.add(participant)
                        elif new_user_type == 'Delegator':
                            group.admins.remove(participant)
                            group.delegators.add(participant)
                    elif old_user_type == "Moderator":
                        if new_user_type == 'Admin':
                            group.moderators.remove(participant)
                            group.admins.add(participant)
                        elif new_user_type == 'Member':
                            group.moderators.remove(participant)
                            group.members.add(participant)
                        elif new_user_type == 'Delegator':
                            group.moderators.remove(participant)
                            group.delegators.add(participant)
                    elif old_user_type == "Member":
                        if new_user_type == 'Admin':
                            group.members.remove(participant)
                            group.admins.add(participant)
                        elif new_user_type == 'Moderator':
                            group.members.remove(participant)
                            group.moderators.add(participant)
                        elif new_user_type == 'Delegator':
                            group.members.remove(participant)
                            group.delegators.add(participant)
                    elif old_user_type == "Delegator":
                        if new_user_type == 'Admin':
                            group.delegators.remove(participant)
                            group.admins.add(participant)
                        elif new_user_type == 'Moderator':
                            group.delegators.remove(participant)
                            group.moderators.add(participant)
                        elif new_user_type == 'Member':
                            group.delegators.remove(participant)
                            group.members.add(participant)
                    group.modified_by = request.user
                    group.save()
                result = success_response(data={}, message="")
                return Ok(result)
            result = failed_response(data={}, message="Owner or Admin only can edit the user designation.")
            return BadRequest(result)
        result = failed_response(data={}, message="Group is not exist.")
        return BadRequest(result)

    @decorators.action(detail=True, methods=['post', 'update'], url_path="mail_all_group_members")
    def mail_all_group_members_api(self, request, pk):
        class InputSerializer(serializers.Serializer):
            subject = serializers.CharField()
            message = serializers.CharField()

        user = request.user
        data = request.data

        serializer = InputSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        mail_all_group_members(user=user.id, group=pk, **serializer.validated_data)

        return Response(status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=['post', 'update'], url_path="group_member_update")
    def group_member_update_api(self, request, pk):
        class InputSerializer(serializers.Serializer):
            target = serializers.IntegerField()
            allow_vote = serializers.BooleanField()

        user = request.user
        data = request.data

        serializer = InputSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        group_member_update(user=user.id, group=pk, **serializer.validated_data)
        return Response()

    @decorators.action(detail=True, methods=['get'], url_path="group_members_get")
    def group_members_get_api(self, request, pk):
        class OutputSerializer(serializers.ModelSerializer):
            class Meta:
                model = GroupMembers
                fields = (
                    'user',
                    'allow_vote'
                )

        group_user_permitted(user=request.user.id, group=pk, permission='member')
        group_members = group_members_get(group=pk)
        serializer = OutputSerializer(group_members, many=True)

        return Response(data=serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="my_groups")
    def my_groups(self, request, *args, **kwargs):
        user = request.user
        # get all the group of logged in user
        groups = Group.objects.filter(Q(owners__in=[user]) | Q(admins__in=[user]) | Q(moderators__in=[user]) |
                                      Q(members__in=[user]) | Q(delegators__in=[user]))
        serializer = MyGroupSerializer(groups, many=True, context={"request": self.request})
        data = serializer.data
        result = success_response(data=data, message="")
        return Ok(result)

    # @decorators.action(detail=False, methods=['post'], url_path="add_participant")
    # def add_participant(self, request, *args, **kwargs):
    #     data = request.data
    #     user = request.user
    #     serializer = AddParticipantSerializer(data=data)
    #     if serializer.is_valid(raise_exception=False):
    #         group = Group.objects.filter(id=data.get('id'), created_by=user).first()
    #         if group:
    #             participant = User.objects.filter(email=data.get('email')).first()
    #             if participant:
    #                 user_type = data.get("user_type")
    #                 if user_type == "owner":
    #                     group.owners.add(participant)
    #                     group.moderators.remove(participant)
    #                     group.members.remove(participant)
    #                 elif user_type == "moderator":
    #                     group.moderators.add(participant)
    #                     group.owners.remove(participant)
    #                     group.members.remove(participant)
    #                 elif user_type == "member":
    #                     group.members.add(participant)
    #                     group.moderators.remove(participant)
    #                     group.owners.remove(participant)
    #         result = success_response(data=None, message="")
    #         return Created(result)
    #
    #     else:
    #         result = failed_response(data=serializer.errors, message="")
    #         return BadRequest(result)

    # @decorators.action(detail=False, methods=['post'], url_path="remove_participant")
    # def remove_participant(self, request, *args, **kwargs):
    #     data = request.data
    #     user = request.user
    #     group = Group.objects.filter(id=data.get('id'), created_by=user).first()
    #     if group:
    #         participant = User.objects.filter(email=data.get('email')).first()
    #         if participant:
    #             group.owners.remove(participant)
    #             group.moderators.remove(participant)
    #             group.members.remove(participant)
    #     result = success_response(data=None, message="")
    #     return Created(result)

    @decorators.action(detail=False, methods=['post'], url_path="update_group")
    def update_group(self, request, *args, **kwargs):
        data = request.data
        # get group object by group id
        group = Group.objects.filter(created_by=request.user, id=data.get('id')).first()
        if group:
            # update all the details of group
            group.title = data.get('title', group.title)

            group.description = data.get('description', group.description)

            image = data.get('image', '')
            cover = data.get('cover_image', '')
            image = image if image != '' else group.image
            cover = cover if cover != '' else group.cover_image

            group.cover_image = cover
            group.image = image
            if data.get('public'):
                if data.get('public') == 'true':
                    group.public = True
                else:
                    group.public = False
            group.members_request = data.get('members_request', group.members_request)
            group.poll_approval = data.get('poll_approval', group.poll_approval)
            group.country = data.get('country', group.country)
            group.city = data.get('city', group.city)

            # remove all the #hashtag nad add new updated #hashtag
            if data.get('tags'):
                group.tag.clear()
                tags = data.get('tags').split(' ')
                for tag in tags:
                    group.tag.add(tag)
            group.updated_by = request.user
            group.save()
        serializer = self.serializer_class(group)
        result = success_response(data=serializer.data, message="")
        return Created(result)

    @decorators.action(detail=False, methods=['post'], url_path='group_participants')
    def group_participants(self, request, *args, **kwargs):
        data = request.data
        # get group object by group id
        group = Group.objects.filter(id=data.get('id')).first()
        if group:
            # serializer for get group participant details
            serializer = GroupParticipantSerializer(group, context={'request': self.request})
            data = dict()
            [i.update({"user_type": 'Owner'}) for i in serializer.data['owners']]
            [i.update({"user_type": 'Admin'}) for i in serializer.data['admins']]
            [i.update({"user_type": 'Moderator'}) for i in serializer.data['moderators']]
            [i.update({"user_type": 'Member'}) for i in serializer.data['members']]
            [i.update({"user_type": 'Delegator'}) for i in serializer.data['delegators']]

            # return all participants and count of it in reponse
            data['participant'] = serializer.data['owners'] + serializer.data['admins'] + serializer.data[
                'moderators'] + \
                                  serializer.data['members'] + serializer.data['delegators']
            data['total_participant'] = len(data['participant'])

            result = success_response(data=data, message="")
            return Ok(result)
        result = success_response(data=[], message="Group does not exist.")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path='all_group')
    def all_groups(self, request, *args, **kwargs):
        data = request.data
        # get all active groups
        groups = Group.objects.filter(active=True)

        # get sort by fields and filtered by fields
        sort_by = data.get('sort_by', 'new')
        filter_my_groups = data.get('filter_my_groups', False)
        filter_country = data.get('filter_country', False)
        filter_city = data.get('filter_city', False)
        filter_date_created = data.get('filter_date_created', False)
        # filter the group by needed filter passed in request
        if filter_my_groups:
            groups = groups.filter(created_by=request.user)
        if filter_country:
            groups = groups.filter(country=filter_country)
        if filter_city:
            groups = groups.filter(city=filter_city)
        if filter_date_created:
            month, year = filter_date_created.split(' ')
            groups = groups.filter(created_at__month=int(month), created_at__year=int(year))

        # sort the group by needed sort field passed in request
        if sort_by == 'new':
            groups = groups.order_by('-created_at')
        elif sort_by == 'popular':
            groups = groups.annotate(total_mmbs=Count('owners') + Count('moderators') + Count('delegators') +
                                                Count('members')).order_by('-total_mmbs')
        elif sort_by == 'rising':
            groups = groups  # TODO: need to discuss

        page_number = data.get('page', 1)  # page number
        page_size = data.get('page_size', 10)  # size of result per page
        paginator = Paginator(groups, page_size)

        response = dict()
        response['count'] = paginator.count
        response['total_page'] = len(paginator.page_range)
        response['next'] = paginator.page(page_number).has_next()
        response['previous'] = paginator.page(page_number).has_previous()

        # serializer for get group details page by page
        serializer = MyGroupSerializer(paginator.page(page_number), many=True, context={"request": self.request})
        response['data'] = serializer.data
        result = success_response(data=response, message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path='get_group_details')
    def get_group_details(self, request, *args, **kwargs):
        data = request.data
        # get group object by group id
        group = Group.objects.filter(id=data.get('id')).first()
        if group:
            # serializer for get particular group details
            serializer = GroupDetailsSerializer(group, context={'request': self.request})
            result = success_response(data=serializer.data, message="")
            return Ok(result)
        result = success_response(data=[], message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path='join_group')
    def join_group(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        as_delegator = data.get('as_delegator', False)
        # get group object by group id
        group = Group.objects.filter(id=data.get('group')).first()
        if group:
            if not data.get('key') and group.blockchain:
                return ValidationError('Group requires key to join')

            # check the join type of group
            if not group.members_request == 'direct_join':
                # sent request to owner and admin to join the group
                data['participant'] = data['created_by'] = data['modified_by'] = user.id
                serializer = CreateGroupRequestSerializer(data=data)
                if serializer.is_valid(raise_exception=False):
                    serializer.save()
                    group_member_update(target=user.id, group=group.id,
                                        key=data.get('key'))
                    result = success_response(data=None, message="")
                    return Created(result)
                result = failed_response(data=serializer.errors, message="")
                return BadRequest(result)
            else:
                # direct join the group
                if as_delegator:
                    group.delegators.add(user)
                else:
                    group.members.add(user)
                group.save()
                group_member_update(target=user.id, group=group.id,
                                    key=data.get('key'))
                result = success_response(data={}, message="")
                return Ok(result)
        result = failed_response(data={}, message="Group does not exist.")
        return BadRequest(result)

    @decorators.action(detail=True, methods=['post'], url_path='leave_group')
    def leave_group_api(self, request, pk):
        user = request.user
        leave_group(target=user.id, group=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(detail=True, methods=['post'], url_path='kick_group_user')
    def kick_group_user_api(self, request, pk):
        class InputSerializer(serializers.Serializer):
            target = serializers.IntegerField()

        user = request.user
        serializer = InputSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        leave_group(user=user.id, group=pk, **serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(detail=False, methods=['post'], url_path='get_group_join_requests')
    def get_group_join_requests(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        # get group object by group id
        group = Group.objects.filter(id=data.get('group')).first()
        if group:
            # check the user permission in group for get all group join requests
            if user in group.owners.all() or user in group.admins.all():
                # get all group requests with status `requested`
                group_requests = GroupRequest.objects.filter(group=group, status='requested').order_by('-created_at')
                serializer = GetGroupJoinRequestListSerializer(group_requests, many=True,
                                                               context={'request': self.request})
                # return all requests details and count of request in response
                response_data = dict()
                response_data['requests'] = serializer.data
                response_data['total_requests'] = len(serializer.data)
                result = success_response(data=response_data, message="")
                return Ok(result)
            result = failed_response(data={}, message="Owner and Admin only can get the join group requests.")
            return BadRequest(result)
        result = failed_response(data={}, message="Group does not exist.")
        return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path='get_all_groups_join_requests')
    def get_all_groups_join_requests(self, request, *args, **kwargs):
        user = request.user
        # get all groups of logged in user
        groups = Group.objects.filter(Q(created_by=user) | Q(owners__in=[user]) | Q(admins__in=[user]) |
                                      Q(moderators__in=[user]))
        # get all join request of above groups
        group_requests = GroupRequest.objects.filter(group__in=groups, status='requested')
        serializer = GetGroupJoinRequestListSerializer(group_requests, many=True, context={'request': self.request})
        result = success_response(data=serializer.data, message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['put'], url_path='accept_reject_group_request')
    def accept_reject_group_request(self, request, *args, **kwargs):
        data = request.data
        data['modified_by'] = request.user.id
        # get join group request by group id and user id
        request_obj = GroupRequest.objects.filter(group=data.get('group'), participant=data.get('participant')).first()
        if request_obj:
            # serializer for accept or reject the group join request
            serializer = UpdateGroupRequestSerializer(request_obj, data=data, partial=True,
                                                      context={'request': self.request})
            if serializer.is_valid(raise_exception=False):
                status = serializer.validated_data.get('status')
                # if accept the request then add that user in requested group
                if status == 'accepted':
                    group = Group.objects.filter(id=serializer.validated_data.get('group').id).first()
                    group.members.add(serializer.validated_data.get('participant'))
                    group.save()
                    serializer.save()
                # if reject the request then delete that request
                elif status == 'rejected':
                    request_obj.delete()
                result = success_response(data=None, message="")
                return Ok(result)
            result = failed_response(data=serializer.errors, message="")
            return BadRequest(result)
        result = failed_response(data=None, message="Request does not exist.")
        return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path='add_group_doc')
    def add_group_doc(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        # get group object by group id
        group = Group.objects.get(id=data.get('group'))
        # check the role of user in group
        if group_user_permitted(user=user.id, group=group.id, permission='member'):
            serializer = CreateGroupDocSerializer(data=data)
            if serializer.is_valid():
                # create or get the doc object for add that doc in group
                grp_doc, created = GroupDocs.objects.get_or_create(group=group, doc=data.get('doc'),
                                                                   doc_name=data.get('doc_name'), created_by=user)
                grp_doc.save()
                result = success_response(data=serializer.data, message="")
                return Created(result)
            result = failed_response(data=serializer.errors, message="")
            return BadRequest(result)
        result = failed_response(data={}, message="Owner or Admin only Add the documents.")
        return BadRequest(result)

    @decorators.action(detail=False, methods=['delete'], url_path='delete_group_doc')
    def delete_group_doc(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        # get group object by group id
        group = Group.objects.get(id=request.query_params['group'])
        # check the role of user in group
        if user in group.owners.all() or user in group.admins.all():
            # get doc object filter by group id and doc id
            grp_doc = GroupDocs.objects.filter(group=request.query_params['group'],
                                               id=request.query_params['doc']).first()
            if grp_doc:
                # if object is found then delete that object
                grp_doc.delete()
                result = success_response(data={}, message="")
                return Ok(result)
            result = failed_response(data={}, message="Document is not exist.")
            return BadRequest(result)
        result = failed_response(data={}, message="Owner or Admin only remove the documents.")
        return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path='get_all_group_docs')
    def get_all_group_docs(self, request, *args, **kwargs):
        data = request.data
        # get all group doc objects by group id
        grp_docs = GroupDocs.objects.filter(group=data.get('group'))
        serializer = GroupDocsListSerializer(grp_docs, many=True, context={'request': self.request})
        result = success_response(data=serializer.data, message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path='get_search_result')
    def get_search_result(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        response = dict()
        search_by = data.get('search_by')
        search_value = data.get('search_value', None)
        first_page = data.get('first_page')
        last_created_at = data.get('last_created_at', None)

        # when select `people` on search tab
        if search_by == 'people':
            if search_value:
                if first_page:
                    # get all user objects as per serach query passed in search box
                    users = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name')). \
                        filter(full_name__icontains=search_value).order_by('-created_at')
                    last_created_at = users.first().created_at if users else None
                    response['last_created_at'] = last_created_at
                else:
                    users = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name')). \
                        filter(full_name__icontains=search_value).filter(created_at__lte=last_created_at).order_by(
                        '-created_at') if last_created_at else []
                message = "Get all users list successfully with search value."
            else:
                if first_page:
                    users = User.objects.all().order_by('-created_at')
                    last_created_at = users.first().created_at if users else None
                    response['last_created_at'] = last_created_at
                else:
                    users = User.objects.filter(created_at__lte=last_created_at).order_by(
                        '-created_at') if last_created_at else []
                message = "Get all users list successfully."
            page_number = data.get('page', 1)  # page number
            page_size = data.get('page_size', 10)  # size of result per page
            paginator = Paginator(users, page_size)

            response['count'] = paginator.count
            response['total_page'] = len(paginator.page_range)
            response['next'] = paginator.page(page_number).has_next()
            response['previous'] = paginator.page(page_number).has_previous()

            # serializer for get basic details of user page by page
            serializer = SimpleUserSerializer(paginator.page(page_number), many=True, context={"request": self.request})

            response['data'] = serializer.data
            result = success_response(data=response, message=message)
            return Ok(result)

        # when select `group` on search tab
        elif search_by == 'group':
            if search_value:
                if first_page:
                    # get all groups objects as per search query passed in search box
                    groups = Group.objects.filter(title__icontains=search_value).annotate(
                        total_mmbs=Count('owners') + Count('moderators') + Count('members')).order_by('-total_mmbs')
                    last_created_at = groups.first().created_at if groups else None
                    response['last_created_at'] = last_created_at
                else:
                    groups = Group.objects.filter(title__icontains=search_value).filter(created_at__lte=last_created_at) \
                        .annotate(total_mmbs=Count('owners') + Count('moderators') + Count('members')) \
                        .order_by('-total_mmbs') if last_created_at else []
                message = "Get all groups list successfully with search value."
            else:
                if first_page:
                    groups = Group.objects.annotate(total_mmbs=Count('owners') + Count('moderators') + Count('members')) \
                        .order_by('-total_mmbs')
                    last_created_at = groups.first().created_at if groups else None
                    response['last_created_at'] = last_created_at
                else:
                    groups = Group.objects.filter(created_at__lte=last_created_at) \
                        .annotate(total_mmbs=Count('owners') + Count('moderators') + Count('members')) \
                        .order_by('-total_mmbs') if last_created_at else []
                message = "Get all groups list successfully."

            page_number = data.get('page', 1)  # page number
            page_size = data.get('page_size', 10)  # size of result per page
            paginator = Paginator(groups, page_size)

            response['count'] = paginator.count
            response['total_page'] = len(paginator.page_range)
            response['next'] = paginator.page(page_number).has_next()
            response['previous'] = paginator.page(page_number).has_previous()

            # serializer for get basic details of group page by page for search query
            serializer = SearchGroupSerializer(paginator.page(page_number), many=True,
                                               context={"request": self.request})

            response['data'] = serializer.data
            result = success_response(data=response, message=message)
            return Ok(result)

        # when select `polls` on search tab
        elif search_by == 'polls':
            if search_value:
                if first_page:
                    # get all public group poll or participated group polls
                    polls = Poll.objects.filter(
                        Q(group__public=True) | Q(Q(group__owners__in=[user]) | Q(group__admins__in=[user])
                                                  | Q(group__moderators__in=[user]) | Q(group__members__in=[user]) |
                                                  Q(group__delegators__in=[user]), group__public=False)).distinct()
                    # filter polls by search query passed in search box
                    polls = polls.filter(title__icontains=search_value).order_by('-created_at')
                    last_created_at = polls.first().created_at if polls else None
                    response['last_created_at'] = last_created_at
                else:
                    # get all public group poll or participated group polls
                    polls = Poll.objects.filter(
                        Q(group__public=True) | Q(Q(group__owners__in=[user]) | Q(group__admins__in=[user])
                                                  | Q(group__moderators__in=[user]) | Q(group__members__in=[user]) |
                                                  Q(group__delegators__in=[user]), group__public=False)
                    ).distinct().filter(created_at__lte=last_created_at) if last_created_at else []
                    # filter polls by search query passed in search box
                    polls = polls.filter(title__icontains=search_value).order_by(
                        '-created_at') if last_created_at else []
                message = "Get all poll list successfully with search value."
            else:
                if first_page:
                    polls = Poll.objects.filter(
                        Q(group__public=True) | Q(Q(group__owners__in=[user]) | Q(group__admins__in=[user])
                                                  | Q(group__moderators__in=[user]) | Q(group__members__in=[user]) |
                                                  Q(group__delegators__in=[user]), group__public=False)
                    ).distinct().order_by('-created_at')
                    last_created_at = polls.first().created_at if polls else None
                    response['last_created_at'] = last_created_at
                else:
                    polls = Poll.objects.filter(
                        Q(group__public=True) | Q(Q(group__owners__in=[user]) | Q(group__admins__in=[user])
                                                  | Q(group__moderators__in=[user]) | Q(group__members__in=[user]) |
                                                  Q(group__delegators__in=[user]), group__public=False)
                    ).distinct().filter(
                        created_at__lte=last_created_at).order_by('-created_at') if last_created_at else []
                message = "Get all poll list successfully."

            page_number = data.get('page', 1)  # page number
            page_size = data.get('page_size', 10)  # size of result page by page
            paginator = Paginator(polls, page_size)

            response['count'] = paginator.count
            response['total_page'] = len(paginator.page_range)
            response['next'] = paginator.page(page_number).has_next()
            response['previous'] = paginator.page(page_number).has_previous()

            # serializer for get basic details of poll for search result
            serializer = SearchPollSerializer(paginator.page(page_number), many=True)
            response['data'] = serializer.data
            result = success_response(data=response, message=message)
            return Ok(result)

        else:
            result = failed_response(data=None, message="Please pass valid search_by parameter.")
            return BadRequest(result)


class UserGroupChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @decorators.action(detail=False, methods=['post'], url_path="get_group_rooms")
    def get_group_rooms(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        # group_rooms = Group.objects.filter()
        # to be continue...
        return Ok(data)


class LocationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @decorators.action(detail=False, methods=['post'], url_path="get_all_countries")
    def get_all_countries(self, request, *args, **kwargs):
        # get all countries
        all_countries = Country.objects.all()
        serializer = GetAllCountrySerializer(all_countries, many=True)
        result = success_response(data=serializer.data, message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path="get_all_state_by_country")
    def get_all_state_by_country(self, request, *args, **kwargs):
        data = request.data
        country = data.get('country')
        # get all state by country id
        if country:
            states = State.objects.filter(country=country)
            serializer = GetAllStatesByCountries(states, many=True)
            result = success_response(data=serializer.data, message="")
            return Ok(result)
        result = failed_response(data={}, message="Please pass country parameter.")
        return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path="get_all_city_by_state")
    def get_all_city_by_state(self, request, *args, **kwargs):
        data = request.data
        state = data.get('state')
        # get all city by state id
        if state:
            cities = City.objects.filter(state=state)
            serializer = GetAllCityByStateSerializer(cities, many=True)
            result = success_response(data=serializer.data, message="")
            return Ok(result)
        result = failed_response(data={}, message="Please pass state parameter.")
        return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path="get_all_cities_by_country")
    def get_all_cities_by_country(self, request, *args, **kwargs):
        data = request.data
        country_id = data.get('country')
        if country_id:
            # get country by country id
            country = Country.objects.filter(id=country_id).first()
            if country:
                # get state by country id and city by state id
                states = State.objects.filter(country=country)
                cities = City.objects.filter(state__in=states)
                serializer = GetAllCityByStateSerializer(cities, many=True)
                result = success_response(data=serializer.data, message="")
                return Ok(result)
            result = failed_response(data={}, message="Country does not exist.")
            return BadRequest(result)
        result = failed_response(data={}, message="Please pass country parameter.")
        return BadRequest(result)


class FriendsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @decorators.action(detail=False, methods=['get'], url_path="get_all_friends_rooms")
    def get_all_friends_rooms(self, request, *args, **kwargs):
        user = request.user
        # get all friend's room for chat connection
        friends = Friends.objects.filter(Q(request_accept=True), Q(user_1=user) | Q(user_2=user))
        serializer = GetAllFriendsRoomSerializer(friends, many=True, context={'request': request})
        result = success_response(data=serializer.data, message="Get all friend's rooms successfully.")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path="send_friend_request")
    def send_friend_request(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        # serializer for create object of friend request
        serializer = CreateFriendRequestSerializer(data=data)
        if serializer.is_valid():
            friend = Friends.objects.filter(user_1=user, user_2=data.get('user_2')) or Friends.objects.filter \
                (user_2=user, user_1=data.get('user_2'))
            # if request is not sent yet then create the friend request
            if not friend:
                user_obj = User.objects.filter(id=data.get('user_2')).first()
                if user_obj:
                    friend = Friends.objects.create(user_1=user, user_2=user_obj)
                    friend.save()

                    result = success_response(data=None, message="Request sent successfully.")
                    return Ok(result)
                else:
                    result = failed_response(data=None, message="User does not exist.")
                    return BadRequest(result)
            else:
                result = failed_response(data=None, message="Request is already sent by you or your friend.")
                return BadRequest(result)
        else:
            result = failed_response(data=serializer.errors, message="")
            return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path="get_all_friend_request")
    def get_all_friend_request(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        response = dict()
        first_page = data.get('first_page')
        last_request_sent_at = data.get('last_request_sent_at', None)
        if first_page:
            # get all friend request of logged in user
            friends_requests = Friends.objects.filter(user_2=user, request_accept=False).order_by('-request_sent_at')
            last_sent_at = friends_requests.first().request_sent_at if friends_requests else None
            response['last_request_sent_at'] = last_sent_at
        else:
            # get all friend request of logged in user
            friends_requests = Friends.objects.filter(user_2=user, request_accept=False). \
                filter(request_sent_at__lte=last_request_sent_at).order_by(
                '-request_sent_at') if last_request_sent_at else []

        page_number = data.get('page', 1)  # page number
        page_size = data.get('page_size', 10)  # size of result page by page
        paginator = Paginator(friends_requests, page_size)

        response['count'] = paginator.count
        response['total_page'] = len(paginator.page_range)
        response['next'] = paginator.page(page_number).has_next()
        response['previous'] = paginator.page(page_number).has_previous()

        serializer = GetAllFriendRequestSerializer(paginator.page(page_number), many=True)
        response['data'] = serializer.data
        result = success_response(data=response, message="")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path="accept_reject_friend_request")
    def accept_reject_friend_request(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        # get friend request object by friend id and user id
        friend_request = Friends.objects.filter(user_1=data.get('friend_id'), user_2=user, request_accept=False).first()
        if friend_request:
            accept_or_reject = data.get('accept_or_reject')
            if accept_or_reject == 'accept':
                # after accept the request, create room for chat
                friend_request.request_accept = True
                friend_request.request_accepted_at = datetime.datetime.now()

                letters = string.ascii_letters
                random_string = "".join(random.choice(letters) for i in range(5))

                room_name = "{}_{}".format(friend_request.id, random_string)
                friend_request.room_name = room_name
                friend_request.save()

                result = success_response(data=None, message="Request accepted successfully.")
                return Ok(result)
            elif accept_or_reject == 'reject':
                # if reject the request then delete that friend request
                friend_request.delete()
                result = success_response(data=None, message="Request rejected successfully.")
                return Ok(result)
            else:
                result = failed_response(data=None, message="Please enter valid value of 'accept_or_reject' parameter.")
                return BadRequest(result)
        else:
            result = failed_response(data=None, message="Friend request is not available.")
            return BadRequest(result)

    @decorators.action(detail=False, methods=['post'], url_path="get_chat_messages")
    def get_chat_messages(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        response = dict()
        first_page = data.get('first_page')
        last_message_id = data.get('last_message_id', None)
        if not last_message_id:
            # get all chat message with friend filtered by friend id
            messages = FriendChatMessage.objects.filter(Q(sender=user, receiver=data.get('friend_id')) |
                                                        Q(sender=data.get('friend_id'), receiver=user)).order_by(
                '-created_at')
            # response['last_message_id'] = messages.first().id if messages else None
        else:
            # get all chat message with friend filtered by friend id
            messages = FriendChatMessage.objects.filter(Q(id__lt=last_message_id),
                                                        Q(sender=user, receiver=data.get('friend_id')) |
                                                        Q(sender=data.get('friend_id'), receiver=user)).order_by(
                '-created_at') if last_message_id else []

        page_number = data.get('page', 1)  # page number
        page_size = data.get('page_size', 25)  # size of result page by page
        paginator = Paginator(messages, page_size)

        response['count'] = paginator.count
        response['total_page'] = len(paginator.page_range)
        response['next'] = paginator.page(page_number).has_next()
        response['previous'] = paginator.page(page_number).has_previous()

        serializer = GetChatMessagesSerializer(paginator.page(page_number), many=True, context={'request': self.request,
                                                                                                'friend_id': data.get(
                                                                                                    'friend_id')})
        # return all chat messages with friend and count of unread message
        response['data'] = dict()
        response['data']['message'] = serializer.data[::-1]
        unread_messages = FriendChatMessage.objects.filter(sender=data.get('friend_id'), receiver=user, seen=False)
        unread_messages = len(unread_messages)
        response['data']['unread_messages'] = unread_messages

        result = success_response(data=response, message="Get chat message successfully.")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path="seen_messages")
    def seen_messages(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        friend_user_id = data.get('friend_user_id')
        # get all unseen chat message with friend filtered by friend id
        unseen_messages = FriendChatMessage.objects.filter(sender=friend_user_id, receiver=user, seen=False)
        # seen all chat message
        unseen_messages.update(seen=True, seen_at=datetime.datetime.now())
        result = success_response(data={}, message="All message seen successfully.")
        return Ok(result)


class GroupChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @decorators.action(detail=False, methods=['get'], url_path="get_all_group_rooms")
    def get_all_group_rooms(self, request, *args, **kwargs):
        user = request.user
        groups = Group.objects.filter(Q(created_by=user) | Q(owners__in=[user]) | Q(admins__in=[user]) |
                                      Q(moderators__in=[user]) | Q(delegators__in=[user]))
        serializer = GetAllGroupRoomsSerializer(groups, many=True, context={'request': request})
        result = success_response(data=serializer.data, message="Get all group's rooms successfully.")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path="get_chat_messages")
    def get_chat_messages(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        response = dict()
        last_message_id = data.get('last_message_id', None)
        group = data.get('group_id')
        if not last_message_id:
            messages = GroupChatMessage.objects.filter(group=group).order_by('-created_at')
        else:
            messages = GroupChatMessage.objects.filter(id__lt=last_message_id, group=group).order_by(
                '-created_at') if last_message_id else []

        page_number = data.get('page', 1)
        page_size = data.get('page_size', 25)
        paginator = Paginator(messages, page_size)

        response['count'] = paginator.count
        response['total_page'] = len(paginator.page_range)
        response['next'] = paginator.page(page_number).has_next()
        response['previous'] = paginator.page(page_number).has_previous()

        serializer = GetGroupChatMessagesSerializer(paginator.page(page_number), many=True,
                                                    context={'request': self.request})
        response['data'] = dict()
        response['data']['message'] = serializer.data[::-1]
        unread_messages = GroupChatMessage.objects.filter(group=group).exclude(seen_by__in=[user])
        unread_messages = len(unread_messages)
        response['data']['unread_messages'] = unread_messages

        result = success_response(data=response, message="Get group chat message successfully.")
        return Ok(result)

    @decorators.action(detail=False, methods=['post'], url_path="seen_messages")
    def seen_messages(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        group = data.get('group')
        unseen_messages = GroupChatMessage.objects.filter(group=group).exclude(seen_by__in=[user])
        for message in unseen_messages:
            if user not in message.seen_by.all():
                message.seen_by.add(user)
                message.save()
        # unseen_messages.update(seen=True, seen_at=datetime.datetime.now())
        result = success_response(data={}, message="All message seen successfully.")
        return Ok(result)

# from django.shortcuts import render
#
# def index(request):
#     return render(request, 'chat_template/index.html')
#
# def room(request, room_name):
#     return render(request, 'chat_template/room.html', {
#         'room_name': room_name
#     })
