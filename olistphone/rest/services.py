from rest.models import CallRecord
from itertools import groupby
from dateutil.relativedelta import relativedelta
from math import floor
from olistphone.settings import CONFIG

def calculate_bills(records):
    calls = groupby(records, lambda call: call.call_id)
    bills = []
    for _, call_records in calls:
        start = ""
        end = ""
        destination = ""
        for call_record in call_records:
            if call_record.record_type == "S":
                start = call_record.timestamp
                destination = call_record.destination
            else:
                end = call_record.timestamp
        price = calculate_pricing(start, end)
        duration = calculate_time_delta(start, end)
        bills.append(
            {
                "destination": destination,
                "call start timestamp": start,
                "call duration": duration,
                "total price": price
            }
        )
    return bills

def calculate_basic_tariff(start, end):
    delta = end - start
    call_minutes = floor(delta.seconds/60)
    tariff = call_minutes * CONFIG.get("MINUTE_CHARGE")
    return tariff

def calculate_discount_tariff(start, end):
    delta = end - start
    call_minutes = floor(delta.seconds/60)
    tariff = call_minutes * CONFIG.get("DISCOUNT_CHARGE")
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

def calculate_pricing(start,end):
    tariff = 0
    delta = calculate_time_delta(start, end)
    current = start
    while delta_hours(delta) >= 0:
        is_discount_period, to_break = calculate_period(current)
        if delta > to_break:
            if is_discount_period:
                tariff += (
                    calculate_discount_tariff(
                        current,
                        (current+to_break)
                    )
                )
            else:
                tariff += (
                    calculate_basic_tariff(
                        current,
                        (current+to_break)
                    )
                )
            delta -= to_break
            current += to_break
        else:
            tariff += (
                calculate_discount_tariff(current, end) if is_discount_period
                else calculate_basic_tariff(current, end)
            )
            break
    tariff += CONFIG.get("BASE_TARIFF")
    return tariff
