from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

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

# We need this class for the 'source' and 'destination' fields,
# since they are null for End records, but have a unique_together
# restriction on both of them
class NullableCharField(models.CharField):
    def clean(self, value):
        value = super(NullCharField, self).clean(value)
        if value in forms.fields.EMPTY_VALUES:
            return None
        return value

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
    call_id = models.PositiveIntegerField()

    # Since call_id is not unique, but a unique-pair, we need to define
    # a combination of fields for uniqueness
    class Meta:
        # This makes it so we can have one Start record
        # and one End record with the same call_id, but never more than
        # one of each, and also impossibilitates simultaneous calls.
        unique_together = (
            ('type', 'call_id'),
            ('source', 'timestamp'),
            ('destination', 'timestamp')
        )

    # Source (caller) phone number.
    # Uses phone_validator_regex for validation
    source = NullableCharField(
        validators=[phone_validator_regex],
        max_length=11,
        blank=True,
        null=True
    )
    # Destination (called) phone number.
    # Uses phone_validator_regex for validation
    destination = NullableCharField(
        validators=[phone_validator_regex],
        max_length=11,
        blank=True,
        null=True
    )

    # Additional validation for the record model
    # If we are creating a End Call Record, it should not have any
    # phone numbers stored.
    def clean(self):
        if ((self.source or self.destination is not None) and
                self.type == 'E'):
            raise ValidationError('End records must not have numbers.')
    
    # We override the models.Model.save() method to ensure
    # we don't create a record where the source and destination
    # numbers are the same
    def save(self, *args, **kwargs):
        if self.source == self.destination:
            raise ValidationError(
                'Cannot create a call where source is the same as destination.'
            )
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
    call_duration = models.PositiveIntegerField()

    # The full value charge of the phone call.
    # Using DecimalFields to avoid float precision loss.
    charge = models.DecimalField(decimal_places=2, max_digits=15)


# CallTariff represents the tariffs referring to a call in a certain
# period of time
class CallTariff(models.Model):

    # Base flat charge for all calls
    base_tariff = models.DecimalField(decimal_places=2, max_digits=15)

    # Tariff added per full minute in the normal time period
    minute_charge = models.DecimalField(decimal_places=2, max_digits=15)

    # Tariff added per full minute in the discounted time period
    discount_charge = models.DecimalField(decimal_places=2, max_digits=15)

    # This tariff applies to everything after this date and before
    # the next tariff's valid_after field
    valid_after = models.DateField()
