from django.contrib.auth.models import User, Group
from rest.models import CallRecord, RECORD_TYPES
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

# Class responsible for serializing CallRecord objects
class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallRecord

        fields = (
            'id',
            'record_type',
            'timestamp',
            'call_id',
            'source',
            'destination'
        )