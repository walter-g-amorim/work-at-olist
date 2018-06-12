from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from decimal import *
getcontext().prec = 2

# Enumeration makes further modifications, if necessary, easier
RECORD_TYPES = (
    ('S', 'Start'),
    ('E', 'End'),
)

# Here we define what a valid phone number is,
# following the repository's guidelines
# Phone numbers have to be all digits (0-9)
# Their length has to be between 10 (2 area digits + 8 phone digits)
# and 11 (2 area digits + 9 phone digits)
phone_validator_regex = RegexValidator(
    regex=r'^\d{10,11}$',
    code="invalid_phone_number",
    message='Phone numbers must be all digits,'
    + ' with 2 area code digits and 8 or 9 phone number digits.'
)


# CallRecord models the start and end of a phone call
class CallRecord(models.Model):
    # Call records can be either Start or End records
    # Type of the record model.
    type = models.CharField(
        max_length=1,
        choices=RECORD_TYPES
    )

    # Timestamp of the event
    timestamp = models.DateTimeField()

    # Unique-pair call ID.
    # MinValueValidator is included due to SQLite not verifying
    # for negative numbers even with PositiveIntegerField
    call_id = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )

    # Since call_id is not unique, but a unique-pair, we need to define
    # a combination of fields for uniqueness
    class Meta:
        # This makes it so we can have one Start record
        # and one End record with the same call_id, but never more than
        # one of each.
        # Additionally, we can prevent repeated records by checking
        # the call_id and timestamp
        unique_together = (
            ('type', 'call_id'),
            ('call_id', 'timestamp')
        )

    # Source (caller) phone number.
    # Uses phone_validator_regex for validation
    source = models.CharField(
        validators=[phone_validator_regex],
        max_length=11,
        null=True
    )
    # Destination (called) phone number.
    # Uses phone_validator_regex for validation
    destination = models.CharField(
        validators=[phone_validator_regex],
        max_length=11,
        null=True
    )

    # Additional validation for the record model
    # If we are creating a End Call Record, it should not have any
    # phone numbers stored.
    def validate_end_record_with_numbers(self):
        '''
        Validates end call records have no source or destination numbers
        in its structure
        '''
        if ((self.source or self.destination is not None) and
                self.type == 'E'):
            raise ValidationError('End records must not have numbers.')

    def validate_source_and_destination(self):
        '''
        Validates that call records cannot have the same source and
        destination, or one of these fields and not the other
        '''
        if self.source is not None:
            if self.destination is None:
                raise ValidationError(
                    'Cannot create a call with source and no destination'
                )
            if self.source == self.destination:
                raise ValidationError(
                    'Cannot create a call where source is the same as'
                    + ' the destination.'
                )
        elif self.destination is not None:
            if self.source is None:
                raise ValidationError(
                    'Cannot create a call with destination and no source'
                )

    def validate_source_and_timestamp(self):
        '''
        Validates the uniqueness between a call's source and timestamp
        i.e. a person cannot call two people at once
        '''
        if self.source is not None:
            conflict = CallRecord.objects.filter(
                source=self.source,
                timestamp=self.timestamp
            )
            if self.id is not None:
                conflict = conflict.exclude(pk=self.id)
            if conflict.exists():
                raise ValidationError(
                    'Cannot create a call when there is already a record for'
                    + ' this source and timestamp'
                )

    def validate_destination_and_timestamp(self):
        '''
        Validates the uniqueness between a call's destination and
        timestamp, i.e. a person cannot receive two calls at once
        '''
        if self.destination is not None:
            conflict = CallRecord.objects.filter(
                destination=self.destination,
                timestamp=self.timestamp
            )
            if self.id is not None:
                conflict = conflict.exclude(pk=self.id)
            if conflict.exists():
                raise ValidationError(
                    'Cannot create a call when there is already a record for'
                    + ' this destination and timestamp'
                )

    
    def validate_call_id(self):
        '''
        Validates the existence of a start call record if there is an
        attempt to insert an end call record with a given call_id
        '''
        if self.type == 'E':
            start = CallRecord.objects.filter(
                type='S',
                call_id=self.call_id
            )
            if not start.exists():
                raise ValidationError(
                    'Cannot create an end call report with no previous'
                    + ' start call report (no start report with this call ID)'
                )

    def validate_overlap(self):
        '''
        Validates that calls cannot start before another call has ended
        and if there's an attempt to add a start call record, that it
        cannot exist if there's an end call record in a timestamp
        after its own
        '''
        if self.type == 'S':
            started_calls = CallRecord.objects.filter(
                source=self.source,
                type='S',
                timestamp__lte=self.timestamp
            )
            ended_calls = CallRecord.objects.filter(
                call_id__in=[call.call_id for call in started_calls],
                type='E',
            )
            conflict = ended_calls.filter(
                timestamp__gte=self.timestamp
            )
            if conflict.exists():
                raise ValidationError(
                    'Cannot create a start call report when there is an'
                    + ' end call report with a later timestamp for the'
                    + ' same source'
                )
            unended_calls = started_calls.exclude(
                call_id__in=[call.call_id for call in ended_calls]
            )
            if unended_calls.exists():
                raise ValidationError(
                    'Cannot create a start call report when there is an'
                    + ' unfinished call report for the same source'
                    + ' (Unpaired call_id)'
                )

    def validate_end_call_timestamp(self):
        '''
        Validates that an end call record cannot have a timestamp
        before its own start call record pair
        '''
        if self.type == 'E':
            started_call = CallRecord.objects.get(
                call_id=self.call_id,
                type='S'
            )
            if self.timestamp <= started_call.timestamp:
                raise ValidationError(
                    'The end call record timestamp cannot be a period in'
                    + ' time which comes before the start call period'
                )

    def validate_numbers(self):
        '''
        If it's a start call record, check for the correctness of its
        phone number fields
        '''
        if self.type == 'S':
            self.clean_fields()

    def validate_save(self):
        '''
        Runs the validation routines
        '''
        self.validate_numbers()
        self.validate_end_record_with_numbers()
        self.validate_source_and_destination()
        self.validate_source_and_timestamp()
        self.validate_destination_and_timestamp()
        self.validate_call_id()
        self.validate_end_call_timestamp()
        self.validate_overlap()

    # We override the models.Model.save() method to ensure
    # we don't create a record in which there are invalid or
    # inconsistent fields, using the custom validation methods
    def save(self, *args, **kwargs):
        self.validate_save()
        super(CallRecord, self).save(*args, **kwargs)


# PhoneBill represents a single billing of a pair of call records
class PhoneBill(models.Model):
    # The destination number of the call. Follows the same validation
    # as the CallRecord phone numbers.
    destination = models.CharField(
        validators=[phone_validator_regex],
        max_length=11
    )

    # The starting timestamp of the call.
    start_timestamp = models.DateTimeField()

    # The duration of the call in seconds.
    # MinValueValidator is included due to SQLite not verifying
    # for negative numbers even with PositiveIntegerField
    call_duration = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )

    # The full value charge of the phone call.
    # Using DecimalFields to avoid float precision loss.
    charge = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # We override the models.Model.save() method to ensure
    # we don't create a record in which there are invalid or
    # inconsistent fields
    def save(self, *args, **kwargs):
        self.clean_fields()
        super(PhoneBill, self).save(*args, **kwargs)


# CallTariff represents the tariffs referring to a call in a certain
# period of time
class CallTariff(models.Model):

    # Base flat charge for all calls
    base_tariff = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Tariff added per full minute in the normal time period
    minute_charge = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Tariff added per full minute in the discounted time period
    discount_charge = models.DecimalField(
        decimal_places=2,
        max_digits=15,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # This tariff applies to everything after this date and before
    # the next tariff's valid_after field
    valid_after = models.DateField()

    def validate_discount(self):
        '''
        Validates that a discount tariff can't be greater than the
        usual tariff (makes sense, right?)
        '''
        if self.discount_charge > self.minute_charge:
            raise ValidationError(
                'Cannot create a tariff where the discount charge is greater'
                + ' than the minute charge'
            )

    # We override the models.Model.save() method to ensure
    # we don't create a record in which there are invalid or
    # inconsistent fields
    def save(self, *args, **kwargs):
        self.clean_fields()
        self.validate_discount()
        super(CallTariff, self).save(*args, **kwargs)
