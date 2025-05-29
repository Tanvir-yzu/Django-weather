import json
from unittest.mock import patch, Mock
import requests.exceptions
from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings

# Ensure RAPIDAPI_KEY is available for tests, either by overriding or ensuring it's in test settings.
# If weather_website.settings.RAPIDAPI_KEY is reliably available in the test environment,
# this override_settings might not be strictly necessary for RAPIDAPI_KEY itself,
# but it's good practice if settings could be different.
@override_settings(RAPIDAPI_KEY='test_api_key_123')
class GetWeatherViewTests(TestCase):

    def setUp(self):
        self.url = reverse('get_weather')
        self.valid_location = 'testcity'
        self.mock_weather_data = {
            "location": {"city": "Test City", "country": "Testland"},
            "current_observation": {
                "condition": {"temperature": 25, "text": "Sunny"},
                "atmosphere": {"humidity": 60},
                "wind": {"speed": 10, "direction": "N"}
            },
            "forecasts": [
                {"day": "Today", "high": 28, "low": 20, "text": "Sunny"},
                {"day": "Tomorrow", "high": 27, "low": 19, "text": "Partly Cloudy"}
            ]
        }

    @patch('weather.views.requests.get')
    def test_successful_weather_data_retrieval(self, mock_requests_get):
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_weather_data
        mock_requests_get.return_value = mock_response

        response = self.client.post(self.url, {'location': self.valid_location})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
        self.assertEqual(response.context['weather_data'], self.mock_weather_data)
        self.assertIsNone(response.context['error_message'])
        mock_requests_get.assert_called_once()

    @patch('weather.views.requests.get')
    def test_api_connection_error(self, mock_requests_get):
        mock_requests_get.side_effect = requests.exceptions.RequestException

        response = self.client.post(self.url, {'location': self.valid_location})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
        self.assertIsNone(response.context['weather_data'])
        self.assertEqual(response.context['error_message'], "Could not connect to the weather service.")
        mock_requests_get.assert_called_once()

    @patch('weather.views.requests.get')
    def test_api_non_200_status_code(self, mock_requests_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests_get.return_value = mock_response

        response = self.client.post(self.url, {'location': self.valid_location})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
        self.assertIsNone(response.context['weather_data'])
        self.assertEqual(response.context['error_message'], "Weather service returned an error: 500")
        mock_requests_get.assert_called_once()

    @patch('weather.views.requests.get')
    def test_api_invalid_json_response(self, mock_requests_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Error", "doc", 0)
        mock_requests_get.return_value = mock_response

        response = self.client.post(self.url, {'location': self.valid_location})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
        self.assertIsNone(response.context['weather_data'])
        self.assertEqual(response.context['error_message'], "Invalid response from the weather service.")
        mock_requests_get.assert_called_once()

    @patch('weather.views.requests.get')
    def test_invalid_location_empty(self, mock_requests_get):
        response = self.client.post(self.url, {'location': ''})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
        self.assertIsNone(response.context['weather_data'])
        self.assertEqual(response.context['error_message'], "Location cannot be empty.")
        mock_requests_get.assert_not_called()

    @patch('weather.views.requests.get')
    def test_invalid_location_too_long(self, mock_requests_get):
        long_location = 'a' * 101
        response = self.client.post(self.url, {'location': long_location})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
        self.assertIsNone(response.context['weather_data'])
        self.assertEqual(response.context['error_message'], "Location is too long.")
        mock_requests_get.assert_not_called()

    # Test for default GET request (e.g., initial page load)
    @patch('weather.views.requests.get')
    def test_get_request_default_location(self, mock_requests_get):
        # Configure mock response for the default location 'jessore'
        mock_response = Mock()
        mock_response.status_code = 200
        # Create a distinct mock data for default location to ensure it's being used
        default_mock_data = self.mock_weather_data.copy()
        default_mock_data["location"]["city"] = "Jessore" # Default city
        mock_response.json.return_value = default_mock_data
        mock_requests_get.return_value = mock_response

        response = self.client.get(self.url) # GET request

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/weather.html')
        self.assertEqual(response.context['weather_data'], default_mock_data)
        self.assertEqual(response.context['location'], 'jessore') # Default location
        self.assertIsNone(response.context['error_message'])
        # Check that requests.get was called with 'jessore'
        mock_requests_get.assert_called_once()
        args, kwargs = mock_requests_get.call_args
        self.assertIn('params', kwargs)
        self.assertEqual(kwargs['params']['location'], 'jessore')

    # Test that RAPIDAPI_KEY from settings is used
    @patch('weather.views.requests.get')
    def test_uses_api_key_from_settings(self, mock_requests_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_weather_data
        mock_requests_get.return_value = mock_response

        # This test will run with RAPIDAPI_KEY = 'test_api_key_123' due to class-level override_settings
        self.client.post(self.url, {'location': self.valid_location})
        
        mock_requests_get.assert_called_once()
        args, kwargs = mock_requests_get.call_args
        self.assertIn('headers', kwargs)
        self.assertEqual(kwargs['headers']['x-rapidapi-key'], 'test_api_key_123')

        # Now test with a different key to be absolutely sure override_settings works per-method too
        # and that the view picks up the change.
        mock_requests_get.reset_mock()
        with override_settings(RAPIDAPI_KEY='another_test_key_456'):
            self.client.post(self.url, {'location': self.valid_location})
            mock_requests_get.assert_called_once()
            args, kwargs = mock_requests_get.call_args
            self.assertIn('headers', kwargs)
            self.assertEqual(kwargs['headers']['x-rapidapi-key'], 'another_test_key_456')

# It's good practice to also test that if RAPIDAPI_KEY is not set,
# the view would ideally not error out immediately but perhaps have a default behavior or specific error.
# However, Django's settings access (settings.RAPIDAPI_KEY) would raise an AttributeError
# if the key is not defined at all, which would lead to an unhandled server error (500)
# unless the view itself has a try-except around settings access.
# The current view implementation does not have such a try-except for settings access.
# So, a test for a missing RAPIDAPI_KEY would expect a server error if settings are truly empty.
# For this set of tests, we assume RAPIDAPI_KEY will always be defined in settings as per instructions.

# To run these tests:
# python manage.py test weather.tests.GetWeatherViewTests

# If you want to test a specific method:
# python manage.py test weather.tests.GetWeatherViewTests.test_successful_weather_data_retrieval
