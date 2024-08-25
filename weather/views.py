import requests
from django.shortcuts import render

def get_weather(request):
    if request.method == 'POST':
        location = request.POST.get('location')
    else:
        location = 'jessore'  # default location

    url = "https://yahoo-weather5.p.rapidapi.com/weather"
    querystring = {"location": location, "format": "json", "u": "c"}

    headers = {
        "x-rapidapi-key": "e1326a9c62msh4c90aa7db28b09fp13482cjsnbaa9986d5d44",
        "x-rapidapi-host": "yahoo-weather5.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    weather_data = response.json()

    return render(request, 'weather/weather.html', {'weather_data': weather_data, 'location': location})
