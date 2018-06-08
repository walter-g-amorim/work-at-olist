from django.db import models
from django.core.validators import RegexValidator


# CallRecord models the start and end of a phone call
class CallRecord(models.Model):
    # Call records can be either Start or End records
    # Enumeration makes further modifications, if necessary, easier
    RECORD_TYPES = (
        ('S', 'Start'),
        ('E', 'End'),
    )
    # Type of the record model
    record_type = models.CharField(
        max_length=1,
        choices=RECORD_TYPES
    )

    # Timestamp of the event
    record_timestamp = models.DateTimeField()

    # Unique-pair call ID.
    call_id = models.CharField(max_length=255)

    # Since call_id is not unique, but a unique-pair, we need to define
    # a combination of fields for uniqueness
    class Meta:
        # This makes it so we can have one Start record
        # and one End record with the same call_id, but never more than
        # one of each
        unique_together = ['record_type', 'call_id']

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
    # Source (caller) phone number.
    # Uses phone_validator_regex for validation
    source_number = models.CharField(
        validators=[phone_validator_regex],
        max_length=11,
        blank=True
    )
    # Destination (called) phone number.
    # Uses phone_validator_regex for validation
    destination_number = models.CharField(
        validators=[phone_validator_regex],
        max_length=11,
        blank=True
    )
