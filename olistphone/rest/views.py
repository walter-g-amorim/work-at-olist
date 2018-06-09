from django.contrib.auth.models import User, Group
from rest.models import CallRecord
from rest_framework import viewsets
from rest.serializers import (
    UserSerializer, GroupSerializer,CallRecordSerializer
)
from django.utils import timezone
from dateutil.relativedelta import relativedelta

# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class CallRecordViewSet(viewsets.ModelViewSet):
    # We have to indicate which Serializer will be responsible for
    # this class
    serializer_class = CallRecordSerializer
    
    # With no parameters, we take the whole last month as the reference
    # period
    last_reference_start = timezone.now().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )+relativedelta(months=-1)
    last_reference_end = timezone.now().replace(
        day=1,
        hour=23,
        minute=59,
        second=59,
        microsecond=0
    )+relativedelta(days=-1)
    queryset = CallRecord.objects.filter(
        timestamp__gte=last_reference_start,
        timestamp__lte=last_reference_end,
    )

