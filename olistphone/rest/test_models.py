from django.test import TestCase
from rest.models import CallRecord
from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError


def create_record(
        type=None,
        timestamp=None,
        call_id=None,
        source=None,
        destination=None):
    return CallRecord.objects.create(
        type=type,
        timestamp=timestamp,
        call_id=call_id,
        source=source,
        destination=destination
    )


# Create your tests here.
class CallRecordTests(TestCase):

    def test_create_new_record(self):
        time = timezone.now()
        record = create_record(
            type='S',
            timestamp=time,
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        self.assertIsNotNone(record)
        self.assertIsInstance(record, CallRecord)
        self.assertEquals(record.type, 'S')
        self.assertEquals(record.timestamp, time)
        self.assertEquals(record.call_id, 40)
        self.assertEquals(record.source, '2199999999')
        self.assertEquals(record.destination, '41000000000')

    def test_required_fields_are_required(self):
        self.assertRaises(IntegrityError, create_record)

    def test_phone_number_format_more_digits(self):
        record = create_record(
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='2199999999',
            destination='410000000000'
        )
        self.assertRaises(
            ValidationError,
            record.clean_fields
        )

    def test_phone_number_format_less_digits(self):
        record = create_record(
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='219999999',
            destination='41000000000'
        )
        self.assertRaises(
            ValidationError,
            record.clean_fields
        )

    def test_phone_number_format_invalid_characters(self):
        record = create_record(
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='219999999a',
            destination='e10000000000'
        )
        self.assertRaises(
            ValidationError,
            record.clean_fields
        )

    def test_end_record_must_have_no_numbers(self):
        record = create_record(
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        good_record = create_record(
            type='E',
            timestamp=timezone.now(),
            call_id=40,
        )
        self.assertIsNotNone(good_record)
        self.assertIsInstance(good_record, CallRecord)
        record = create_record(
            type='S',
            timestamp=timezone.now(),
            call_id=41,
            source='2199999999',
            destination='41000000000'
        )
        bad_record = create_record(
            type='E',
            timestamp=timezone.now(),
            call_id=41,
            source='2199999999',
            destination='41000000000'
        )
        self.assertRaises(ValidationError, bad_record.clean)

    def test_record_uniqueness(self):
        record1 = create_record(
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        self.assertIsNotNone(record1)
        self.assertIsInstance(record1, CallRecord)
        record2 = create_record(
            type='E',
            timestamp=timezone.now(),
            call_id=40,
        )
        self.assertIsNotNone(record2)
        self.assertIsInstance(record2, CallRecord)
        self.assertRaises(
            IntegrityError,
            create_record,
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='2112349999',
            destination='41111000000'
        )
