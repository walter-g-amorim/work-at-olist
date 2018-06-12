from itertools import groupby
from dateutil.relativedelta import relativedelta
from math import floor
from rest.models import PhoneBill, CallTariff
from django.utils import dateparse, timezone
from datetime import datetime
from decimal import *
getcontext().prec = 2

# Main service functionalities to be called by the views

def calculate_bills(records):
    '''
    Gets the call records and transforms them into bills.
    This returns a list of PhoneBill objects.
    '''
    # Group our records by call_id. This makes it so the start and end
    # records are joined inside one key
    calls = groupby(records, lambda call: call.call_id)
    bills = []
    # Iterating over the grouped call records
    for _, call_records in calls:
        # Initialize variables to avoid scope conflicts
        start = ""
        end = ""
        destination = ""
        # Since the records are grouped by call_id, we have both the
        # start and end records inside the set
        # We check the type and extract the necessary data from each
        # of them
        for call_record in call_records:
            if call_record.type == "S":
                start = call_record.timestamp
                destination = call_record.destination
            else:
                end = call_record.timestamp
        # If that record already exists, get it from the database
        # This is cacheable, and it might be a good idea to do so
        try:
            bill = PhoneBill.objects.get(
                destination=destination,
                start_timestamp=start
            )
        # If it doesn't, it needs to be calculated and created
        except PhoneBill.DoesNotExist:
            # Get the latest tariffs for that time period
            try:
                tariff = CallTariff.objects.filter(
                    valid_after__lte=start
                ).order_by('-valid_after')[0]
            # If for some reason they aren't there, initialize the
            # database with a tariff set (in this case, the one in
            # the spec)
            except IndexError:
                tariff = CallTariff(
                    valid_after=timezone.now().replace(year=1900),
                    base_tariff=Decimal('0.36'),
                    minute_charge=Decimal('0.09'),
                    discount_charge=Decimal('0.00')
                )
                tariff.save()
            # Calculate the charge for this particular call
            charge = calculate_pricing(start, end, tariff)
            # Calculate the duration of this call
            duration = calculate_time_delta(start, end)
            # Create the PhoneBill object
            bill = PhoneBill(
                destination=destination,
                start_timestamp=start,
                call_duration=duration.total_seconds(),
                charge=charge
            )
            bill.save()
        # Add the bill to the list
        bills.append(bill)
    return bills

# Functions to calculate the pricing of a given call
# They are separated in case of a pricing calculation change,
# e.g. making the discount tariff a percentage of the full tariff

def calculate_basic_tariff(start, end, call_tariff):
    '''
    Function to calculate the usual tariff between two time periods
    '''
    # Get the time delta between the start and end of the call
    delta = end - start
    # We only count full minutes
    call_minutes = floor(delta.seconds/60)
    tariff = call_minutes * call_tariff.minute_charge
    return tariff


def calculate_discount_tariff(start, end, call_tariff):
    '''
    Function to calculate a discounted tariff between two time periods
    '''
    # Get the time delta between the start and end of the call
    delta = end - start
    # We only count full minutes
    call_minutes = floor(delta.seconds/60)
    tariff = call_minutes * call_tariff.discount_charge
    return tariff

# Functions to calculate the whole bill of a record

def calculate_pricing(start, end, call_tariff):
    '''
    This function calculates the full price of a given call from
    timestamp start to timestamp end, given a set of call tariffs
    '''
    # Safety measure for scope problems
    tariff = 0
    # Get the measurement of time between the timestamps
    delta = calculate_time_delta(start, end)
    current = start
    # While we still have time to process...
    while delta_hours(delta) >= 0:
        # Get if we are inside the discount period and how much time
        # is left until the next period change
        is_discount_period, to_break = calculate_period(current)
        # If the next break period comes before the call ends...
        if delta > to_break:
            # ...check if it's the discount period and add the tariff
            # from the current time until the period flip
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
            # Take off the time we just processed from the delta
            delta -= to_break
            # and add the time passed to our 'current' timestamp
            current += to_break
        # If we don't cross any periods until the call ends, then it's
        # easy happy dreamland
        else:
            # Check if we're in a discount period and add the tariff
            if is_discount_period:
                tariff += calculate_discount_tariff(current, end, call_tariff)
            else:
                tariff += calculate_basic_tariff(current, end, call_tariff)
            # If we did not cross a billing period then we're done by here
            break
    # Add up the base tariff to the minute charges
    tariff += call_tariff.base_tariff
    return tariff

# Helper functions

def calculate_period(timestamp):
    '''
    Calculates the rates and time until the next change in tariff rate
    from a given timestamp
    '''
    # If the time period is between the two discount periods
    if (timestamp.hour >= 6) and (timestamp.hour < 22):
        # No discount for you :(
        is_discount_period = False
        # The next discount period starts at 22:00:00
        # so we calculate the delta between the timestamp and that
        # start timestamp
        to_break = (
            timestamp.replace(hour=22, minute=0, second=0)
            - timestamp
        )
    # If the time period is inside one of the discount periods
    elif timestamp.hour < 6:
        # We get the discount!
        is_discount_period = True
        # The normal period starts at 06:00:00
        # so we calculate the delta between the timestamp and that
        # start timestamp
        to_break = (
            timestamp.replace(hour=6, minute=0, second=0)
            - timestamp
        )
    elif timestamp.hour >= 22:
        # We also get the discount!
        is_discount_period = True
        # There is a day flip until the next normal period, so we
        # need to add a day to the current date...
        next_day = timestamp + relativedelta(days=1)
        # and then get the delta to the next 06:00:00 timestamp
        to_break = (
            next_day.replace(hour=6, minute=0, second=0)
            - timestamp
        )
    return is_discount_period, to_break


def calculate_time_delta(start, end):
    '''
    Helper function that calculates a time delta between two time
    periods. Not strictly necessary, just for added readability
    '''
    return end - start


def delta_hours(delta):
    '''
    Helper function that calulates a given time delta in hours.
    Also not strictly necessary, but helps understanding
    '''
    return floor(delta.seconds/3600)


def get_last_month():
    '''
    Gets the time period referring the last month
    '''
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

def get_monthly_period(date):
    '''
    Gets the period referring to a month in which a date is contained
    '''
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


def parse_month_year(date_string):
    '''
    Usual datetime parsing routine. Tries parsing date and datetime,
    then moves on to the weirder formats.
    '''
    date = dateparse.parse_date(date_string)
    if date is not None:
        return get_monthly_period(date)
    date = dateparse.parse_datetime(date_string)
    if date is not None:
        return get_monthly_period(date)
    return parse_obscure_formats(date_string)


def parse_obscure_formats(date_string):
    '''
    This function tries to parse the more unusual date formats,
    like just the month, or string-based month representations
    '''
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
