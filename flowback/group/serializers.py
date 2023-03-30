from rest_framework import serializers

from flowback.group.models import Group, GroupUser
from flowback.user.serializers import BasicUserSerializer

class BasicGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'image', 'cover_image', 'hide_poll_users')


class GroupUserSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer()

    delegate = serializers.BooleanField()
    permission_id = serializers.IntegerField(allow_null=True)
    permission_name = serializers.CharField(source='permission.role_name', default='Member')

    class Meta:
        model = GroupUser
        fields = ('id',
                  'user',
                  'delegate',
                  'is_admin',
                  'permission_name',
                  'permission_id',
                  'permission_name')
