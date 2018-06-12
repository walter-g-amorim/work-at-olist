from itertools import groupby
from dateutil.relativedelta import relativedelta
from math import floor
from rest.models import PhoneBill, CallTariff
from django.utils import dateparse, timezone
from datetime import datetime
from decimal import *
getcontext().prec = 2


# Gets the call records and transforms them into bills.
def calculate_bills(records):
    calls = groupby(records, lambda call: call.call_id)
    bills = []
    for _, call_records in calls:
        start = ""
        end = ""
        destination = ""
        for call_record in call_records:
            if call_record.type == "S":
                start = call_record.timestamp
                destination = call_record.destination
            else:
                end = call_record.timestamp
        try:
            bill = PhoneBill.objects.get(
                destination=destination,
                start_timestamp=start
            )
        except PhoneBill.DoesNotExist:
            try:
                tariff = CallTariff.objects.filter(
                    valid_after__lte=start
                ).order_by('-valid_after')[0]
            except IndexError:
                tariff = CallTariff(
                    valid_after=timezone.now().replace(year=1900),
                    base_tariff=Decimal('0.36'),
                    minute_charge=Decimal('0.09'),
                    discount_charge=Decimal('0.00')
                )
                tariff.save()
            charge = calculate_pricing(start, end, tariff)
            duration = calculate_time_delta(start, end)
            bill = PhoneBill(
                destination=destination,
                start_timestamp=start,
                call_duration=duration.total_seconds(),
                charge=charge
            )
            bill.save()
        bills.append(bill)
    return bills


def calculate_basic_tariff(start, end, call_tariff):
    delta = end - start
    call_minutes = floor(delta.seconds/60)
    tariff = call_minutes * call_tariff.minute_charge
    return tariff


def calculate_discount_tariff(start, end, call_tariff):
    delta = end - start
    call_minutes = floor(delta.seconds/60)
    tariff = call_minutes * call_tariff.discount_charge
    return tariff


def calculate_period(timestamp):
    if (timestamp.hour >= 6) and (timestamp.hour < 22):
        is_discount_period = False
        to_break = (
            timestamp.replace(hour=22, minute=0, second=0)
            - timestamp
        )
    elif timestamp.hour < 6:
        is_discount_period = True
        to_break = (
            timestamp.replace(hour=6, minute=0, second=0)
            - timestamp
        )
    elif timestamp.hour >= 22:
        is_discount_period = True
        next_day = timestamp + relativedelta(days=1)
        to_break = (
            next_day.replace(hour=6, minute=0, second=0)
            - timestamp
        )
    return is_discount_period, to_break


def calculate_time_delta(start, end):
    return end - start


def delta_hours(delta):
    return floor(delta.seconds/3600)


def calculate_pricing(start, end, call_tariff):
    tariff = 0
    delta = calculate_time_delta(start, end)
    current = start
    while delta_hours(delta) >= 0:
        is_discount_period, to_break = calculate_period(current)
        if delta > to_break:
            if is_discount_period:
                tariff += calculate_discount_tariff(
                    current,
                    (current+to_break),
                    call_tariff
                )
            else:
                tariff += calculate_basic_tariff(
                    current,
                    (current+to_break),
                    call_tariff
                )
            delta -= to_break
            current += to_break
        else:
            if is_discount_period:
                tariff += calculate_discount_tariff(current, end, call_tariff)
            else:
                tariff += calculate_basic_tariff(current, end, call_tariff)
            break
    tariff += call_tariff.base_tariff
    return tariff


def get_last_month():
    reference_start = timezone.now().replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )+relativedelta(months=-1)
    reference_end = timezone.now().replace(
        day=1,
        hour=23,
        minute=59,
        second=59,
        microsecond=0
    )+relativedelta(days=-1)
    return reference_start, reference_end


def parse_month_year(date_string):
    date = dateparse.parse_date(date_string)
    if date is not None:
        return get_monthly_period(date)
    date = dateparse.parse_datetime(date_string)
    if date is not None:
        return get_monthly_period(date)
    return parse_obscure_formats(date_string)


def parse_obscure_formats(date_string):
    # Try to parse dates in which only the month is passed
    # This assumes that the year is the current one
    try:
        # Try the number format first...
        date = datetime.strptime(date_string, "%m")
        date = date.replace(year=timezone.now().year)
        return get_monthly_period(date)
    except ValueError:
        date = None
    try:
        # ... then the shorthand letter format
        date = datetime.strptime(date_string, "%b")
        date = date.replace(year=timezone.now().year)
        return get_monthly_period(date)
    except ValueError:
        date = None
    # Try to parse dates in the "06-1994" format
    try:
        date = datetime.strptime(date_string, "%m-%Y")
        return get_monthly_period(date)
    except ValueError:
        date = None
    # Try to parse dates in the "Jun-1994" format
    try:
        date = datetime.strptime(date_string, "%b-%Y")
        return get_monthly_period(date)
    except ValueError:
        date = None
    # Try to parse dates in the "1994-Jun" format
    try:
        date = datetime.strptime(date_string, "%Y-%b")
        return get_monthly_period(date)
    except ValueError:
        date = None
    # Try to parse dates in the "Jun1994" format
    try:
        date = datetime.strptime(date_string, "%b%Y")
        return get_monthly_period(date)
    except ValueError:
        date = None
    # Couldn't parse the string
    if date is None:
        raise ValueError


def get_monthly_period(date):
    reference_start = date.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )
    reference_end = date.replace(
        day=1,
        hour=23,
        minute=59,
        second=59,
        microsecond=0
    )+relativedelta(months=1, days=-1)
    return reference_start, reference_end
