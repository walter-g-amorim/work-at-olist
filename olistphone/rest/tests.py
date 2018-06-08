from django.test import TestCase
from rest.models import CallRecord
from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError


# Create your tests here.
class CallRecordTests(TestCase):

    def create_record(
            self,
            record_type=None,
            record_timestamp=None,
            call_id=None,
            source_number=None,
            destination_number=None
    ):
        return CallRecord.objects.create(
            record_type=record_type,
            record_timestamp=record_timestamp,
            call_id=call_id,
            source_number=source_number,
            destination_number=destination_number
        )

    def test_create_new_record(self):
        record = self.create_record(
            record_type='S',
            record_timestamp=timezone.now(),
            call_id=40,
            source_number="2199999999",
            destination_number="41000000000"
        )
        self.assertIsNotNone(record)
        self.assertIsInstance(record, CallRecord)

    def test_required_fields_are_required(self):
        self.assertRaises(IntegrityError, self.create_record)

    def test_phone_number_format_more_digits(self):
        record = self.create_record(
            record_type='S',
            record_timestamp=timezone.now(),
            call_id=40,
            source_number="2199999999",
            destination_number="410000000000"
        )
        self.assertRaises(
            ValidationError,
            record.full_clean
        )

    def test_phone_number_format_less_digits(self):
        record = self.create_record(
            record_type='S',
            record_timestamp=timezone.now(),
            call_id=40,
            source_number="219999999",
            destination_number="41000000000"
        )
        self.assertRaises(
            ValidationError,
            record.full_clean
        )

    def test_phone_number_format_invalid_characters(self):
        record = self.create_record(
            record_type='S',
            record_timestamp=timezone.now(),
            call_id=40,
            source_number="219999999a",
            destination_number="e10000000000"
        )
        self.assertRaises(
            ValidationError,
            record.full_clean
        )
