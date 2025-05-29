import requests
import json
from django.shortcuts import render
from django.conf import settings

def get_weather(request):
    location = request.POST.get('location') if request.method == 'POST' else 'jessore'
    weather_data = None
    error_message = None

    # Input validation for location
    if not location:
        error_message = "Location cannot be empty."
    elif len(location) > 100:
        error_message = "Location is too long."

    # If there's no error message from input validation, proceed with API call
    if not error_message:
        url = "https://yahoo-weather5.p.rapidapi.com/weather"
        querystring = {"location": location, "format": "json", "u": "c"}
        headers = {
            "x-rapidapi-key": settings.RAPIDAPI_KEY,
            "x-rapidapi-host": "yahoo-weather5.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code == 200:
                try:
                    weather_data = response.json()
                except json.JSONDecodeError:
                    error_message = "Invalid response from the weather service."
            else:
                error_message = f"Weather service returned an error: {response.status_code}"

        except requests.exceptions.RequestException:
            error_message = "Could not connect to the weather service."
            # Optionally, log the specific exception e if needed for debugging
            # import sys
            # print(f"RequestException: {sys.exc_info()[0]}")

    return render(request, 'weather/weather.html', {
        'weather_data': weather_data,
        'location': location,
        'error_message': error_message
    })
