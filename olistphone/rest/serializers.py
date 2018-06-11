from rest.models import CallRecord, PhoneBill, CallTariff
from rest_framework import serializers
from collections import OrderedDict
from rest_framework.fields import SkipField


# Class responsible for serializing CallRecord objects
class CallRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallRecord
        fields = (
            'id',
            'type',
            'timestamp',
            'call_id',
            'source',
            'destination'
        )

    # We want to omit NULL/None fields from the representation,
    # so we need to override the Serializer methods.
    # This is pretty close to the actual implementation
    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = [field for field in self.fields.values()
                  if not field.write_only]

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            if attribute is not None:
                representation = field.to_representation(attribute)
                # This is the main change
                if representation is None:
                    # Do not serialize empty objects
                    continue
                if isinstance(representation, list) and not representation:
                    # Do not serialize empty lists
                    continue
                ret[field.field_name] = representation

        return ret

class PhoneBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneBill
        fields = (
            'destination',
            'start_timestamp',
            'call_duration',
            'charge'
        )

class CallTariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallTariff
        fields = (
            'base_tariff',
            'minute_charge',
            'discount_charge',
            'valid_after'
        )
