from itertools import groupby
from dateutil.relativedelta import relativedelta
from math import floor
from rest.models import PhoneBill, CallTariff
import json
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
            tariff = CallTariff.objects.filter(
                valid_after__lte=start
            ).order_by('-valid_after')[0]
            charge = calculate_pricing(start, end, tariff)
            duration = calculate_time_delta(start, end)
            bill = PhoneBill(
                destination=destination,
                start_timestamp=start,
                call_duration=duration.seconds,
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
