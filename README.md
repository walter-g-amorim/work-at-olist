# Olistphone, a Work at Olist application
Olistphone is a Call Detail Record (CDR) management RESTful web application
that handles Call Record creation and billing.

## How to install
For installing and using Olistphone, it's required you install [Python 3.6](https://www.python.org).
Usage of a `virtualenv` is heavily recommended.

1. Clone this repository through `git clone https://github.com/walter-g-amorim/work-at-olist.git`
or downloading it through github. 
2. Navigate to the project's directory and run `pip install -r requirements.txt` to install
all the required libraries.
3. That's it! The SQLite database used is already present in the directory. If you want to
reset the database, you can remove the `db.sqlite3` file from the `olistphone` directory
and run the migration command.

## How to run and functionalities
There is a `makefile` bundled with this project to facilitate execution.

*Running the Server: `make run`
*Run Unit Tests: `make test`
*Run Migrations (if you deleted the database): `make migrate`
*Open Django Shell: `make shell`

Additionally, there is a dump of the populated database in the `db_dump.json`.

## API Reference
###`/record/`
Route for sending call record data.
*Methods allowed: `POST`
*Usage: `POST /record/` with a `Content-Type: application/json` header.
*JSON format:
```
{
  "type": "S" for start call records or "E" for end call records,
  "timestamp": ISO-8601 formatted datetime timestamp representing the record timestamp,
  "call_id": A positive integer call-id to be paired for each "S" and "E" pair,
  "source": Required for type "S", disallowed for "E". A 10 to 11 digit string representing the source phone number,
  "destination": Required for type "S", disallowed for "E". A 10 to 11 digit string representing the destination phone number
}
```
*Returns: Code `201 Created` with no body if successful.
###`/billing/`
Route for retrieving phone bill data.
*Methods allowed: `GET`
*Usage: `GET /billing/[subscriber_number]/` to get data referring to the last closed period or `GET /billing/[subscriber_number]/[month-year]/` for a specific period.
*Returns: Code `200 OK` with body containing a JSON string.
*JSON format:
```
{
  "subscriber": A 10 to 11 digit string. The requested subscriber's phone number,
  "reference_period": The reference period requested. If not in the request, this is the last month before the current one,
  "billed_calls": A list of phone bills referring to the requested period
}
```
## Model Reference
### Call Record
Model referring to a call record, to be received through the `/record/` route.
*JSON format:
```
{
  "type": "S" for start call records or "E" for end call records,
  "timestamp": A ISO-8601 formatted datetime timestamp representing the record timestamp,
  "call_id": A positive integer call-id to be paired for each "S" and "E" pair,
  "source": Required for type "S", disallowed for "E". A 10 to 11 digit string representing the source phone number,
  "destination": Required for type "S", disallowed for "E". A 10 to 11 digit string representing the destination phone number
}
```
### Phone Bill
The model contained in the "billed_calls" attribute of the `/billing/` route response.
*JSON format:
```
{
  "destination": A 10 to 11 digit string representing the destination phone number,
  "start_timestamp": ISO-8601 formatted datetime timestamp representing the start of the call's timestamp,
  "call_duration": A positive integer representing the call duration in seconds,
  "charge": A string (Decimal) field representing the tariff to be paid by this call
}
```

### Call Tariff
Internal-use model that defines the call tariffs to be used in the Phone Bill calculations.
*Model format:
```
base_tariff: A DecimalField representing the base tariff for any call,
minute_charge: A DecimalField representing the usual charge per minute,
discount_charge: A DecimalField representing the discounted charge in the discount per
```
