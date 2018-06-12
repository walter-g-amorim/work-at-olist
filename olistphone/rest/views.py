from rest.models import CallRecord
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
import rest.services as services
from rest.serializers import CallRecordSerializer, PhoneBillSerializer
import re


class CallRecordView(APIView):
    renderer_classes = (JSONRenderer, )
    parser_classes = (JSONParser, )

    def post(self, request):
        if request.data:
            serializer = CallRecordSerializer(data=request.data)
            is_valid = serializer.is_valid()
            if not is_valid:
                return Response(serializer.errors, status=400)
            try:
                serializer.save()
            except ValidationError as err:
                return Response(data=err, status=400)
            return Response(status=201)
        return Response(status=400)


class MonthlyBillingView(APIView):
    renderer_classes = (JSONRenderer, )
    parser_classes = (JSONParser, )

    def get(self, request, phone_number, year_month=None, format='json'):
        # First, we need to validate if the phone number received
        # is valid
        is_valid_phone = re.compile(r'^\d{10,11}$').match(phone_number)
        # If it isn't, return a 'BAD REQUEST' response
        if not is_valid_phone:
            return Response(status=400)
        # With only the number as a parameter, we take the whole
        # last month as the reference period
        if not year_month:
            (last_reference_start,
             last_reference_end) = services.get_last_month()
        # If a year and month are supplied, we need to parse
        # that date into something filterable
        else:
            try:
                (last_reference_start,
                 last_reference_end) = services.parse_month_year(
                     year_month
                     )
            except ValueError:
                return Response(status=400)
        # Find calls that ended in the reference period
        # The spec says that inclusion or exclusion in a monthly period
        # is through the call end timestamp, so we filter accordingly
        monthly_records_by_end = CallRecord.objects.filter(
            type='E',
            timestamp__gte=last_reference_start,
            timestamp__lte=last_reference_end
        )
        # Next we need to find out what of these calls are made by
        # the number we want to search for so we filter out
        # for the calls that are made by the source...
        calls_by_this_source = CallRecord.objects.filter(
            source=phone_number,
            call_id__in=[
                call.call_id for call in monthly_records_by_end
            ]
        )
        # ...and then filter again for the call end records, since
        # they do not contain a "source" number
        calls_by_this_source = (
            calls_by_this_source
            | monthly_records_by_end.filter(
                type='E',
                call_id__in=[
                    call.call_id for call in calls_by_this_source
                ]
            )
        )
        calls_by_this_source = calls_by_this_source.order_by('call_id')
        bills = services.calculate_bills(calls_by_this_source)
        reference_period = "{}/{}".format(
            last_reference_start.month,
            last_reference_start.year
        )
        serializer = PhoneBillSerializer(data=bills, many=True)
        serializer.is_valid()
        return_data = {
            "subscriber": phone_number,
            "reference_period": reference_period,
            "billed_calls": serializer.data
        }
        return Response(return_data)
