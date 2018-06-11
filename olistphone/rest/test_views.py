from django.test import TestCase, Client
import rest.views as views

class CallRecordViewTests(TestCase):

    def test_not_allowed_method(self):
        response = self.client.get(
            '/records/',
            follow=True)
        self.assertEqual(response.status_code, 405)
        response = self.client.put(
            '/records/',
            content_type='application/json',
            follow=True)
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(
            '/records/',
            content_type='application/json',
            follow=True)
        self.assertEqual(response.status_code, 405)

    def test_unsupported_media_type(self):
        response = self.client.post(
            '/records/',
            follow=True)
        self.assertEqual(response.status_code, 415)
        response = self.client.post(
            '/records/',
            content_type='text/html',
            follow=True)
        self.assertEqual(response.status_code, 415)
        response = self.client.post(
            '/records/',
            content_type='image/png',
            follow=True)
        self.assertEqual(response.status_code, 415)
        response = self.client.post(
            '/records/',
            content_type='application/xml',
            follow=True)
        self.assertEqual(response.status_code, 415)

    def test_send_invalid_data(self):
        invalid_data = '{"asdf": "abc"}'
        response = self.client.post(
            '/records/',
            content_type='application/json',
            data=invalid_data,
            follow=True)
        self.assertEqual(response.status_code, 400)
        invalid_data = '{"type":"F", timestamp:"2017-12-12T15:07:13Z",' \
            + ' "call_id": 11101}'
        response = self.client.post(
            '/records/',
            content_type='application/json',
            data=invalid_data,
            follow=True)
        self.assertEqual(response.status_code, 400)

    def test_send_end_record_with_numbers(self):
        invalid_data = '{"type":"E", timestamp:"2017-12-12T15:07:13Z",' \
            + ' "call_id"=10110, "source": "2199999999",' \
            + '" destination": "41000000000"}'
        response = self.client.post(
            '/records/',
            content_type='application/json',
            data=invalid_data,
            follow=True)
        self.assertEqual(response.status_code, 400)

    def test_send_valid_data(self):
        valid_data = '{"type":"S", "timestamp":"2017-12-12T15:10:13Z",' \
            + ' "call_id": 9990, "source": "2199999999",' \
            + ' "destination": "41000000000"}'
        response = self.client.post(
            '/records/',
            content_type='application/json',
            data=valid_data,
            follow=True)
        self.assertEqual(response.status_code, 201)
        valid_data = '{"type":"E", "timestamp":"2017-12-12T15:13:13Z",' \
            + ' "call_id": 9990}'
        response = self.client.post(
            '/records/',
            content_type='application/json',
            data=valid_data,
            follow=True)
        self.assertEqual(response.status_code, 201)

class MonthlyBillingViewTests(TestCase):

    def test_not_allowed_method(self):
        response = self.client.post(
            '/billing/21998833445/',
            content_type='application/json',
            follow=True
        )
        self.assertEqual(response.status_code, 405)
        response = self.client.put(
            '/billing/21998833445/',
            content_type='application/json',
            follow=True
        )
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(
            '/billing/21998833445/',
            content_type='application/json',
            follow=True
        )
        self.assertEqual(response.status_code, 405)

    def test_invalid_phone(self):
        response = self.client.get(
            '/billing/1234/',
            follow=True
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            '/billing/219999999999/',
            follow=True
        )
        self.assertEqual(response.status_code, 400)

    def test_request_with_no_period(self):
        response = self.client.get(
            '/billing/21998833445/',
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_request_with_unparseable_period(self):
        response = self.client.get(
            '/billing/21998833445/abc2017/',
            follow=True
        )
        self.assertEqual(response.status_code, 400)

    def test_request_with_period_parsing(self):
        response = self.client.get(
            '/billing/21998833445/mar-2018',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
