from rest_framework import serializers
from flowback.users.models import User, Group, OnboardUser, GroupRequest, GroupDocs, Country, State, City, Friends, \
    FriendChatMessage, GroupChatMessage, GroupMembers


# from rest_framework_simplejwt.serializers import TokenObtainSerializer
# from rest_framework_simplejwt.tokens import RefreshToken
#
#
# class TokenObtainPairSerializer(TokenObtainSerializer):
#     @classmethod
#     def get_token(cls, user):
#         return RefreshToken.for_user(user)
#
#     def validate(self, attrs):
#         data = super().validate(attrs)
#
#         refresh = self.get_token(self.user)
#
#         data['refresh'] = str(refresh)
#         data['access'] = str(refresh.access_token)
#         user = {"email": self.user.email, "first_name": self.user.first_name, "last_nme": self.user.last_name}
#         data['user'] = user
#         result = {"success": True, "messages": "user logged in successfully", "data": data}
#         return result


class UserRegistrationSerializer(serializers.ModelSerializer):
    accepted_terms_condition = serializers.BooleanField()

    class Meta:
        model = User
        fields = ('email', 'password', 'accepted_terms_condition')

    def validate_accepted_terms_use(self, value):
        if value:
            return True
        raise serializers.ValidationError('accepted_terms_use is not True')

    def validate_accepted_terms_condition(self, value):
        if value:
            return True
        raise serializers.ValidationError('accepted_terms_condition is not True')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.username = validated_data.get('email')
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.IntegerField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')


class SimpleUserSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    friendship_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'bio', 'image', 'cover_image', 'phone_number', 'country',
                  'city', 'website', 'friendship_status')

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_city(self, obj):
        if obj.city and obj.city != 'undefined':
            city = City.objects.filter(id=obj.city).first()
            if city:
                serializer = GetCityDetailsSerializer(city)
                return serializer.data
        return {}

    def get_country(self, obj):
        if obj.country and obj.country != 'undefined':
            country = Country.objects.filter(id=obj.country).first()
            if country:
                serializer = GetCountryDetailsSerializer(country)
                return serializer.data
        return {}

    def get_friendship_status(self, obj):
        user = self.get_user()
        if user is None or user.is_anonymous:
            return 'not friend'
        if Friends.objects.filter(user_1=user, user_2=obj.id, request_accept=True) or Friends.objects.filter \
                    (user_2=user, user_1=obj.id, request_accept=True):
            return "friend"
        elif Friends.objects.filter(user_1=user, user_2=obj.id, request_accept=False):
            return 'requested'
        elif Friends.objects.filter(user_2=user, user_1=obj.id, request_accept=False):
            return 'respond'
        else:
            return 'not friend'


class PollCommentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'image')


class GroupRequestParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'image')


class UserGroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('title', 'description', 'image', 'cover_image', 'public', 'members_request', 'poll_approval',
                  'country', 'city')


class SearchGroupSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'title', 'image', 'cover_image', 'created_at', 'user_type')

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_user_type(self, obj):
        user = self.get_user()
        if user in obj.owners.all():
            return "Owner"
        elif user in obj.admins.all():
            return "Admin"
        elif user in obj.moderators.all():
            return "Moderator"
        elif user in obj.members.all():
            return "Member"
        elif user in obj.delegators.all():
            return "Delegator"
        else:
            return ''


class MyGroupSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    total_members = serializers.SerializerMethodField()
    group_join_status = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
        'id', 'created_by', 'title', 'description', 'blockchain', 'image', 'cover_image', 'tags', 'country', 'city',
        'public', 'members_request', 'poll_approval', 'active', 'deleted', 'total_members',
        'group_join_status', 'user_type', 'room_name', 'created_at')

    def get_city(self, obj):
        if obj.city and obj.city != 'undefined':
            city = City.objects.filter(id=obj.city).first()
            if city:
                serializer = GetCityDetailsSerializer(city)
                return serializer.data
        return {}

    def get_country(self, obj):
        if obj.country and obj.country != 'undefined':
            country = Country.objects.filter(id=obj.country).first()
            if country:
                serializer = GetCountryDetailsSerializer(country)
                return serializer.data
        return {}

    def get_tags(self, obj):
        return obj.tag.names()

    def get_total_members(self, obj):
        return len(obj.owners.all()) + len(obj.admins.all()) + len(obj.moderators.all()) + \
               len(obj.delegators.all()) + len(obj.members.all())

    def get_group_join_status(self, obj):
        request = self.context.get("request")
        if GroupRequest.objects.filter(group=obj.id, participant=request.user, status='requested').first():
            return 'Requested'
        elif GroupRequest.objects.filter(group=obj.id, participant=request.user, status='accepted').first():
            return 'Accepted'
        elif GroupRequest.objects.filter(group=obj.id, participant=request.user, status='rejected').first():
            return 'Rejected'
        else:
            return 'Not requested'

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_user_type(self, obj):
        user = self.get_user()
        if user in obj.owners.all():
            return "Owner"
        elif user in obj.admins.all():
            return "Admin"
        elif user in obj.moderators.all():
            return "Moderator"
        elif user in obj.members.all():
            return "Member"
        elif user in obj.delegators.all():
            return "Delegator"
        else:
            return ''


class GroupParticipantSerializer(serializers.ModelSerializer):
    owners = SimpleUserSerializer(read_only=True, many=True)
    admins = SimpleUserSerializer(read_only=True, many=True)
    moderators = SimpleUserSerializer(read_only=True, many=True)
    members = SimpleUserSerializer(read_only=True, many=True)
    delegators = SimpleUserSerializer(read_only=True, many=True)

    class Meta:
        model = Group
        fields = ('id', 'owners', 'admins', 'moderators', 'members', 'delegators')


class GroupDetailsSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    total_members = serializers.SerializerMethodField()
    group_join_status = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    created_by = SimpleUserSerializer()

    class Meta:
        model = Group
        fields = (
        'id', 'created_by', 'title', 'description', 'blockchain',
        'image', 'cover_image', 'user_type', 'tags', 'country', 'city',
        'public', 'members_request', 'poll_approval', 'active', 'deleted', 'total_members', 'room_name',
        'group_join_status')

    def get_city(self, obj):
        if obj.city and obj.city != 'undefined':
            city = City.objects.filter(id=obj.city).first()
            if city:
                serializer = GetCityDetailsSerializer(city)
                return serializer.data
        return {}

    def get_country(self, obj):
        if obj.country and obj.country != 'undefined':
            country = Country.objects.filter(id=obj.country).first()
            if country:
                serializer = GetCountryDetailsSerializer(country)
                return serializer.data
        return {}

    def get_tags(self, obj):
        return obj.tag.names()

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_user_type(self, obj):
        user = self.get_user()
        if user in obj.owners.all():
            return "Owner"
        elif user in obj.admins.all():
            return "Admin"
        elif user in obj.moderators.all():
            return "Moderator"
        elif user in obj.members.all():
            return "Member"
        elif user in obj.delegators.all():
            return "Delegator"
        else:
            return ""

    def get_group_join_status(self, obj):
        request = self.context.get("request")
        if GroupRequest.objects.filter(group=obj.id, participant=request.user, status='requested').first():
            return 'Requested'
        elif GroupRequest.objects.filter(group=obj.id, participant=request.user, status='accepted').first():
            return 'Accepted'
        elif GroupRequest.objects.filter(group=obj.id, participant=request.user, status='rejected').first():
            return 'Rejected'
        else:
            return 'Not requested'

    def get_total_members(self, obj):
        return len(obj.owners.all()) + len(obj.admins.all()) + len(obj.moderators.all()) + len(obj.members.all()) + \
               len(obj.delegators.all())


class AddParticipantSerializer(serializers.Serializer):
    user_type = serializers.CharField(required=True)
    id = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=True)


class CreateGroupRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRequest
        fields = ('group', 'participant', 'status', 'created_by', 'modified_by')


class UpdateGroupRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupRequest
        fields = ('group', 'participant', 'status', 'modified_by')


class GetGroupJoinRequestListSerializer(serializers.ModelSerializer):
    participant = GroupRequestParticipantSerializer(read_only=True)

    class Meta:
        model = GroupRequest
        fields = ('group', 'participant', 'status', 'created_at', 'modified_at')


class CreateGroupDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDocs
        fields = ('id', 'group', 'doc', 'doc_name')


class GroupDocsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDocs
        fields = ('id', 'group', 'doc', 'doc_name', 'created_by', 'created_at')


class OnboardUserFirstSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    screen_name = serializers.CharField(required=True)


class OnboardUserSecondSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    verification_code = serializers.IntegerField(required=True)


class GetAllCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class GetAllStatesByCountries(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'


class GetAllCityByStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'
        depth = 2


class GetCityDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ('id', 'city_name')


class GetCountryDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'country_name')


class CreateFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = ('user_2',)


class GetAllFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = ('user_1', 'room_name', 'request_sent_at')
        depth = 1


class GetAllFriendsRoomSerializer(serializers.ModelSerializer):
    friend_details = serializers.SerializerMethodField()

    class Meta:
        model = Friends
        fields = ('id', 'room_name', 'friend_details')

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_friend_details(self, obj):
        user = self.get_user()
        print("obj.user_1", obj.user_2)
        if obj.user_1 == user:
            friend = obj.user_2
        elif obj.user_2 == user:
            friend = obj.user_1
        else:
            return None

        return {'id': friend.id, 'full_name': "{} {}".format(friend.first_name, friend.last_name),
                'image': friend.image.url if friend.image else ''}


class GetChatMessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendChatMessage
        fields = ('id', 'sender', 'receiver', 'message', 'message_type', 'seen', 'seen_at', 'created_at')
        depth = 1


class GetGroupChatMessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupChatMessage
        fields = ('id', 'sender', 'message', 'message_type', 'created_at')
        depth = 1


class GetAllGroupRoomsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'title', 'room_name', 'image')
