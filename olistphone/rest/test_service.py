from django.test import TestCase
import rest.services as services
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from rest.models import CallTariff, PhoneBill
from rest.test_models import create_record
from decimal import *
getcontext().prec = 2


class CallRecordServiceTests(TestCase):

    def setUp(self):
        self.call_tariff = CallTariff.objects.create(
            base_tariff=Decimal(0.36),
            minute_charge=Decimal(0.09),
            discount_charge=Decimal(0),
            valid_after=timezone.now().replace(
                day=27,
                month=6,
                year=1994
            )
        )
        self.records = []
        self.bills = []
        time_start = timezone.now().replace(
            hour=10,
            minute=0,
            second=0
        )
        time_end = time_start + relativedelta(seconds=137)
        record = create_record(
            type='S',
            timestamp=time_start,
            call_id=40,
            source='2199999999',
            destination='41000000000'
        )
        self.records.append(record)
        bill = PhoneBill(
            destination=record.destination,
            start_timestamp=time_start,
            call_duration=(time_end-time_start).seconds,
            charge=(
                self.call_tariff.base_tariff
                + (2*self.call_tariff.minute_charge)
            )
        )
        bill.save()
        self.bills.append(bill)
        self.records.append(record)
        record = create_record(
            type='E',
            timestamp=time_end,
            call_id=40
        )
        time_start = timezone.now().replace(
            hour=12,
            minute=30,
            second=0
        )
        self.records.append(record)
        time_end = time_start + relativedelta(seconds=151)
        record = create_record(
            type='S',
            timestamp=time_start,
            call_id=41,
            source='2199999999',
            destination='41000000000'
        )
        bill = PhoneBill(
            destination=record.destination,
            start_timestamp=time_start,
            call_duration=(time_end-time_start).seconds,
            charge=(
                self.call_tariff.base_tariff
                + (2*self.call_tariff.minute_charge)
            )
        )
        bill.save()
        self.bills.append(bill)
        self.records.append(record)
        record = create_record(
            type='E',
            timestamp=time_end,
            call_id=41
        )
        self.records.append(record)
        time_start = timezone.now().replace(
            hour=23,
            minute=10,
            second=0
        )
        time_end = time_start + relativedelta(seconds=130)
        record = create_record(
            type='S',
            timestamp=time_start,
            call_id=42,
            source='2199999999',
            destination='41000000000'
        )
        bill = PhoneBill(
            destination=record.destination,
            start_timestamp=time_start,
            call_duration=(time_end-time_start).seconds,
            charge=(
                self.call_tariff.base_tariff
                + (2*self.call_tariff.discount_charge)
            )
        )
        bill.save()
        self.bills.append(bill)
        self.records.append(record)
        record = create_record(
            type='E',
            timestamp=time_end,
            call_id=42
        )
        self.records.append(record)

    def test_calculate_basic_tariff(self):
        time_start = timezone.now().replace(second=0)
        time_end = time_start + relativedelta(seconds=137)
        tariff = (
            self.call_tariff.base_tariff
            + services.calculate_basic_tariff(
                time_start,
                time_end,
                self.call_tariff
            )
        )
        expected = (
            self.call_tariff.base_tariff
            + (2 * self.call_tariff.minute_charge)
        )
        self.assertEqual(tariff, expected)

    def test_calculate_discount_tariff(self):
        time_start = timezone.now().replace(second=0)
        time_end = time_start + relativedelta(seconds=137)
        tariff = (
            self.call_tariff.base_tariff
            + services.calculate_discount_tariff(
                time_start,
                time_end,
                self.call_tariff
            )
        )
        expected = (
            self.call_tariff.base_tariff
            + (2 * self.call_tariff.discount_charge)
        )
        self.assertEqual(tariff, expected)

    def test_calculate_time_delta(self):
        time_start = timezone.now()
        time_delta = services.calculate_time_delta(time_start, time_start)
        self.assertEqual(0, time_delta.seconds)
        time_end = time_start + relativedelta(seconds=137)
        time_delta = services.calculate_time_delta(time_start, time_end)
        self.assertEqual(137, time_delta.seconds)
        time_end = time_start + relativedelta(hours=1)
        time_delta = services.calculate_time_delta(time_start, time_end)
        self.assertEqual(3600, time_delta.seconds)

    def test_calculate_period_normal_tariff(self):
        time = timezone.now().replace(hour=12, minute=36, second=42)
        expected_is_discount_period = False
        expected_to_break = timedelta(
            hours=9,
            minutes=23,
            seconds=18
        )
        is_discount_period, to_break = services.calculate_period(time)
        self.assertEqual(expected_is_discount_period, is_discount_period)
        self.assertEqual(expected_to_break, to_break)

    def test_calculate_period_discount_tariff(self):
        time = timezone.now().replace(hour=2, minute=11, second=50)
        expected_is_discount_period = True
        expected_to_break = timedelta(
            hours=3,
            minutes=48,
            seconds=10
        )
        is_discount_period, to_break = services.calculate_period(time)
        self.assertEqual(expected_is_discount_period, is_discount_period)
        self.assertEqual(expected_to_break, to_break)
        time = time.replace(hour=5, minute=59, second=59)
        expected_is_discount_period = True
        expected_to_break = timedelta(seconds=1)
        is_discount_period, to_break = services.calculate_period(time)
        self.assertEqual(expected_is_discount_period, is_discount_period)
        self.assertEqual(expected_to_break, to_break)

    def test_calculate_period_discount_until_next_day(self):
        time = timezone.now().replace(hour=23, minute=30, second=0)
        expected_is_discount_period = True
        expected_to_break = timedelta(
            hours=6,
            minutes=30,
        )
        is_discount_period, to_break = services.calculate_period(time)
        self.assertEqual(expected_is_discount_period, is_discount_period)
        self.assertEqual(expected_to_break, to_break)

    def test_calculate_pricing_normal_period(self):
        time_start = timezone.now().replace(hour=12, minute=0, second=0)
        time_end = time_start + relativedelta(minutes=3, seconds=43)
        expected = (
            self.call_tariff.base_tariff
            + (3 * self.call_tariff.minute_charge)
        )
        tariff = services.calculate_pricing(
            time_start,
            time_end,
            self.call_tariff
        )
        self.assertEqual(tariff, expected)

    def test_calculate_pricing_discount_period(self):
        time_start = timezone.now().replace(hour=5, minute=0, second=0)
        time_end = time_start + relativedelta(minutes=1, seconds=14)
        expected = (
            self.call_tariff.base_tariff
            + (1 * self.call_tariff.discount_charge)
        )
        tariff = services.calculate_pricing(
            time_start,
            time_end,
            self.call_tariff
        )
        self.assertEqual(tariff, expected)

    def test_calculate_pricing_multiple_periods(self):
        time_start = timezone.now().replace(hour=21, minute=0, second=0)
        time_end = time_start + relativedelta(hours=9, minutes=10)
        expected = (
            self.call_tariff.base_tariff
            + (7 * 60 * self.call_tariff.discount_charge)
            + (70 * self.call_tariff.minute_charge)
        )
        tariff = services.calculate_pricing(
            time_start,
            time_end,
            self.call_tariff
        )
        self.assertEqual(tariff, expected)

    def test_calculate_bills(self):
        expected = self.bills
        actual = services.calculate_bills(self.records)
        self.assertEqual(actual, expected)