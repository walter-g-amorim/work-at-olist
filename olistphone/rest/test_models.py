from django.test import TestCase
from rest.models import CallRecord, PhoneBill, CallTariff
from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from decimal import *
getcontext().prec = 2


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


def create_bill(
        destination=None,
        start_timestamp=None,
        call_duration=None,
        charge=None):
    return PhoneBill.objects.create(
        destination=destination,
        start_timestamp=start_timestamp,
        call_duration=call_duration,
        charge=charge
    )


def create_tariff(
        valid_after=None,
        base_tariff=None,
        minute_charge=None,
        discount_charge=None):
    return CallTariff.objects.create(
        valid_after=valid_after,
        base_tariff=base_tariff,
        minute_charge=minute_charge,
        discount_charge=discount_charge
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
        self.assertEqual(record.type, 'S')
        self.assertEqual(record.timestamp, time)
        self.assertEqual(record.call_id, 40)
        self.assertEqual(record.source, '2199999999')
        self.assertEqual(record.destination, '41000000000')

    def test_required_fields_are_required(self):
        self.assertRaises(IntegrityError, create_record)

    def test_call_id_cannot_be_negative(self):
        self.assertRaises(
            ValidationError,
            create_record,
            type='S',
            timestamp=timezone.now(),
            call_id=-40,
            source='2199999999',
            destination='41000000000'
        )

    def test_phone_number_format_more_digits(self):
        self.assertRaises(
            ValidationError,
            create_record,
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='2199999999',
            destination='410000000000'
        )

    def test_phone_number_format_less_digits(self):
        self.assertRaises(
            ValidationError,
            create_record,
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='2199999999',
            destination='4112345'
        )

    def test_phone_number_format_invalid_characters(self):
        self.assertRaises(
            ValidationError,
            create_record,
            type='S',
            timestamp=timezone.now(),
            call_id=40,
            source='219999999o',
            destination='410000000ae'
        )

    def test_end_record_must_have_no_numbers(self):
        time = timezone.now()
        create_record(
            type='S',
            timestamp=time,
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        good_record = create_record(
            type='E',
            timestamp=time+relativedelta(minutes=2),
            call_id=40,
        )
        self.assertIsNotNone(good_record)
        self.assertIsInstance(good_record, CallRecord)
        create_record(
            type='S',
            timestamp=time+relativedelta(minutes=3),
            call_id=41,
            source='2199999999',
            destination='41000000000'
        )
        self.assertRaises(
            ValidationError,
            create_record,
            type='E',
            timestamp=time+relativedelta(minutes=5),
            call_id=41,
            source='2199999999',
            destination='41000000000'
        )

    def test_start_record_must_have_both_numbers(self):
        self.assertRaises(
            ValidationError,
            create_record,
            type='S',
            timestamp=timezone.now(),
            call_id=41,
            source='2199999999'
        )
        self.assertRaises(
            ValidationError,
            create_record,
            type='S',
            timestamp=timezone.now()+relativedelta(minutes=5),
            call_id=41,
            destination='41000000000'
        )

    def test_record_cannot_overlap(self):
        time = timezone.now().replace(
            year=1994,
            month=6,
            day=27,
            hour=12,
            minute=0,
            second=0
        )
        create_record(
            type='S',
            timestamp=time,
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        create_record(
            type='E',
            timestamp=time+relativedelta(minutes=2),
            call_id=40,
        )
        self.assertRaises(
            ValidationError,
            create_record,
            type='S',
            timestamp=time+relativedelta(minutes=1),
            call_id=41,
            source='2199999999',
            destination='41000000000'
        )

    def test_call_cannot_end_before_start(self):
        time = timezone.now().replace(
            year=1994,
            month=6,
            day=27,
            hour=12,
            minute=0,
            second=0
        )
        create_record(
            type='S',
            timestamp=time,
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        self.assertRaises(
            ValidationError,
            create_record,
            type='E',
            timestamp=time+relativedelta(minutes=-1),
            call_id=40
        )

    def test_record_uniqueness(self):
        time = timezone.now()
        record1 = create_record(
            type='S',
            timestamp=time,
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        self.assertIsNotNone(record1)
        self.assertIsInstance(record1, CallRecord)
        record2 = create_record(
            type='E',
            timestamp=time+relativedelta(minutes=2),
            call_id=40,
        )
        self.assertIsNotNone(record2)
        self.assertIsInstance(record2, CallRecord)
        self.assertRaises(
            IntegrityError,
            create_record,
            type='S',
            timestamp=time+relativedelta(minutes=4),
            call_id=40,
            source='2112349999',
            destination='41111000000'
        )


class PhoneBillTest(TestCase):

    def test_create_new_bill(self):
        time = timezone.now()
        delta = timedelta(seconds=10)
        bill = create_bill(
            start_timestamp=time,
            call_duration=delta.total_seconds(),
            destination='41000000000',
            charge=Decimal('0.36')
        )
        self.assertIsNotNone(bill)
        self.assertIsInstance(bill, PhoneBill)
        self.assertEqual(bill.start_timestamp, time)
        self.assertEqual(bill.call_duration, delta.total_seconds())
        self.assertEqual(bill.destination, '41000000000')

    def test_required_fields_are_required(self):
        self.assertRaises(ValidationError, create_bill)

    def test_phone_number_format_more_digits(self):
        time = timezone.now()
        delta = timedelta(seconds=10)
        self.assertRaises(
            ValidationError,
            create_bill,
            start_timestamp=time,
            call_duration=delta.total_seconds(),
            destination='410000000001',
            charge=Decimal('0.36')
        )

    def test_phone_number_format_less_digits(self):
        time = timezone.now()
        delta = timedelta(seconds=10)
        self.assertRaises(
            ValidationError,
            create_bill,
            start_timestamp=time,
            call_duration=delta.total_seconds(),
            destination='4112345',
            charge=Decimal('0.36')
        )

    def test_phone_number_format_invalid_characters(self):
        time = timezone.now()
        delta = timedelta(seconds=10)
        self.assertRaises(
            ValidationError,
            create_bill,
            start_timestamp=time,
            call_duration=delta.total_seconds(),
            destination='410000000ae',
            charge=Decimal('0.36')
        )

    def test_duration_cannot_be_negative(self):
        time = timezone.now()
        delta = timedelta(seconds=10)
        self.assertRaises(
            ValidationError,
            create_bill,
            start_timestamp=time,
            call_duration=-delta.total_seconds(),
            destination='41000000000',
            charge=Decimal('0.36')
        )

    def test_charge_cannot_be_negative(self):
        time = timezone.now()
        delta = timedelta(seconds=10)
        self.assertRaises(
            ValidationError,
            create_bill,
            start_timestamp=time,
            call_duration=delta.total_seconds(),
            destination='41000000000',
            charge=Decimal('-0.36')
        )


class CallTariffTests(TestCase):

    def test_create_new_tariff(self):
        valid_after = timezone.now()
        tariff = create_tariff(
            base_tariff=Decimal('0.36'),
            minute_charge=Decimal('0.09'),
            discount_charge=Decimal('0.00'),
            valid_after=valid_after
        )
        self.assertIsNotNone(tariff)
        self.assertIsInstance(tariff, CallTariff)
        self.assertEqual(tariff.valid_after, valid_after.date())
        self.assertEqual(tariff.base_tariff, Decimal('0.36'))
        self.assertEqual(tariff.minute_charge, Decimal('0.09'))
        self.assertEqual(tariff.discount_charge, Decimal('0.00'))

    def test_required_fields_are_required(self):
        self.assertRaises(ValidationError, create_tariff)

    def test_base_tariff_cannot_be_negative(self):
        self.assertRaises(
            ValidationError,
            create_tariff,
            base_tariff=Decimal('-0.36'),
            minute_charge=Decimal('0.09'),
            discount_charge=Decimal('0.00'),
            valid_after=timezone.now()
        )

    def test_minute_charge_cannot_be_negative(self):
        self.assertRaises(
            ValidationError,
            create_tariff,
            base_tariff=Decimal('0.36'),
            minute_charge=Decimal('-0.09'),
            discount_charge=Decimal('0.00'),
            valid_after=timezone.now()
        )

    def test_discount_charge_cannot_be_negative(self):
        self.assertRaises(
            ValidationError,
            create_tariff,
            base_tariff=Decimal('0.36'),
            minute_charge=Decimal('0.09'),
            discount_charge=Decimal('-0.01'),
            valid_after=timezone.now()
        )

    def test_discount_cannot_be_greater_than_minute_charge(self):
        self.assertRaises(
            ValidationError,
            create_tariff,
            base_tariff=Decimal('0.36'),
            minute_charge=Decimal('0.09'),
            discount_charge=Decimal('0.11'),
            valid_after=timezone.now()
        )
