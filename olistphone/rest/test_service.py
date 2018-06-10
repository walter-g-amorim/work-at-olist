from django.test import TestCase
from rest.models import CallRecord
import rest.services as services
from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from olistphone.settings import CONFIG

class CallRecordServiceTests(TestCase):

    def test_calculate_basic_tariff(self):
        time_start = timezone.now().replace(second=0)
        time_end = time_start + relativedelta(seconds=137)
        tariff = (
            CONFIG.get("BASE_TARIFF")
            + services.calculate_basic_tariff(time_start, time_end)
        )
        expected = (
            CONFIG.get("BASE_TARIFF")
            + (2 * CONFIG.get("MINUTE_CHARGE"))
        )
        self.assertAlmostEqual(tariff, expected)

    def test_calculate_discount_tariff(self):
        time_start = timezone.now().replace(second=0)
        time_end = time_start + relativedelta(seconds=137)
        tariff = (
            CONFIG.get("BASE_TARIFF")
            + services.calculate_discount_tariff(time_start, time_end)
        )
        expected = (
            CONFIG.get("BASE_TARIFF")
            + (2 * CONFIG.get("DISCOUNT_CHARGE"))
        )
        self.assertAlmostEqual(tariff, expected)

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
            CONFIG.get("BASE_TARIFF")
            + (3 * CONFIG.get("MINUTE_CHARGE"))
        )
        tariff = services.calculate_pricing(time_start, time_end)
        self.assertAlmostEqual(tariff, expected)

    def test_calculate_pricing_discount_period(self):
        time_start = timezone.now().replace(hour=5, minute=0, second=0)
        time_end = time_start + relativedelta(minutes=1, seconds=14)
        expected = (
            CONFIG.get("BASE_TARIFF")
            + (1 * CONFIG.get("DISCOUNT_CHARGE"))
        )
        tariff = services.calculate_pricing(time_start, time_end)
        self.assertAlmostEqual(tariff, expected)

    def test_calculate_pricing_multiple_periods(self):
        time_start = timezone.now().replace(hour=21, minute=0, second=0)
        time_end = time_start + relativedelta(hours=9, minutes=10)
        expected = (
            CONFIG.get("BASE_TARIFF")
            + (7 * 60 * CONFIG.get("DISCOUNT_CHARGE"))
            + (70 * CONFIG.get("MINUTE_CHARGE"))
        )
        tariff = services.calculate_pricing(time_start, time_end)
        self.assertAlmostEqual(tariff, expected)
