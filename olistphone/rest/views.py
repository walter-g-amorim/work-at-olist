from django.contrib.auth.models import User, Group
from rest.models import CallRecord
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest.serializers import CallRecordSerializer
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import rest.services as services
from json import dumps, loads


class CallRecordView(APIView):
    renderer_classes = (JSONRenderer, )
   
    def get(self, request, format='json'):
        print(request.data)
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
        # Find calls that ended in the reference period as in spec
        monthly_records_by_end = CallRecord.objects.filter(
            record_type='E',
            timestamp__gte=last_reference_start,
            timestamp__lte=last_reference_end
        )
        # Get the call ids of the filtered records
        call_ids = []
        for record in monthly_records_by_end:
            call_ids.append(record.call_id)
        # Get the whole collection of records to be billed
        billed_records = CallRecord.objects.filter(call_id__in=call_ids)
        bills = services.calculate_bills(billed_records)
        return Response(bills)
