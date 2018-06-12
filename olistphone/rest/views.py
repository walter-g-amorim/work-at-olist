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
        '''
        Method to receive a CallRecord creation request, in JSON format
        '''
        # If we don't have an empty POST...
        if request.data:
            # Try to process and validate the request data
            serializer = CallRecordSerializer(data=request.data)
            # We don't pass the raise exception parameter in case
            # we want to do additional processing before returning
            # a 400 BAD REQUEST response
            is_valid = serializer.is_valid()
            if not is_valid:
                # Return a 400 BAD REQUEST :(
                return Response(serializer.errors, status=400)
            # If it is valid, try saving it since we have methods
            # inside the model for additional validation
            try:
                serializer.save()
            # If it fails model-side validation, we return a 400 BAD
            # REQUEST as well
            except ValidationError as err:
                return Response(data=err, status=400)
            # If all is done correctly, return a 201 CREATED
            return Response(status=201)
        # ...if it's empty, just return a 400 BAD REQUEST
        return Response(status=400)


class MonthlyBillingView(APIView):
    renderer_classes = (JSONRenderer, )
    parser_classes = (JSONParser, )

    def get(self, request, phone_number, year_month=None):
        '''
        This method receives a phone number and optionally a year-month
        period to calculate a bill posting from. If the year_month
        parameter is not passed, it assumes the last month as the
        reference period.
        '''
        # First, we need to validate if the phone number received
        # is valid
        is_valid_phone = re.compile(r'^\d{10,11}$').match(phone_number)
        # If it isn't, return a 400 BAD REQUEST response
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
        # We then order the queryset by call_id to group the calls
        # with the same id together. This is necessary for the groupby
        # call in the service.calculate_bills method
        calls_by_this_source = calls_by_this_source.order_by('call_id')
        bills = services.calculate_bills(calls_by_this_source)
        reference_period = "{}/{}".format(
            last_reference_start.month,
            last_reference_start.year
        )
        # Create a serializer to create the response data
        serializer = PhoneBillSerializer(data=bills, many=True)
        # Double-check for validity
        serializer.is_valid()
        # Create the response dict with the subscriber and reference
        # period fields
        return_data = {
            "subscriber": phone_number,
            "reference_period": reference_period,
            "billed_calls": serializer.data
        }
        # Return a 200 OK response with the requested data
        return Response(return_data)
