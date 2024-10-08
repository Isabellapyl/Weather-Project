import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import openmeteo_requests
import requests_cache
from retry_requests import retry

#my API key
api_key = 'f17d0ee637c6ba466d1e9442d3722279'

#Get the users location based on their IP address
def get_geolocation():
    try:
        #using "requests" use the api
        response = requests.get('http://ip-api.com/json')
        #Convert the response to json so both humans and the computer can easily understand
        data = response.json()
        #check if the api worked
        if data['status'] == 'success':
            #if it worked, it will retreieve the latitude, longitude, and the city of the IP address
            return data['lat'], data['lon'], data['city']
    #if the geolocation can not be retrieved no information will be collected.
    except:
        print(f"Error finding location")
        return None, None, None
#define the function. It needs the api ke and city to work.
def get_current_weather(api_key, city):
    #URL to the api. Uses the f sting to put the api key and city to personalize the link to each user
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    #code accesses the internet
    response = requests.get(url)
    #check if the status code is 200, this means it is sucessful
    if response.status_code == 200:
        #Convert the response to json so both humans and the computer can easily understand
        data = response.json()
        #get the current temp
        temp = data['main']['temp']
        #gets the weather description
        description = data['weather'][0]['description']
        # Return temperature and description
        return temp, description
        print(f"Error getting current weather data")
    # Return "None" values if the request was not successful
    return None, None

#Define the function to get the weather lased on latitude and longitude
def get_predicted_weather(api_key, lat, lon):
    #url to the api. Uses the f sting to put the api key and city to personalize the link to each user
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    #send the request to weather api
    response = requests.get(url)
   #check if the request worked (it will  be 200)
    if response.status_code == 200:
        #convert it to json which bot comouters and humans can understand simply
        data = response.json()
        # Return the temperature for the first 5 forecast entries
        return [entry['main']['temp'] for entry in data['list'][:5]]
    # Return a default list of temperatures if the request was not successful
    return [14, 15, 13, 12, 11]

#get the latitude, longitude, and city using the geolocation function
lat, lon, city = get_geolocation()
#make sure city works
if city:
    # Create a cached session to store API responses forever
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    # Set up a retry mechanism for failed requests
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    # Initializes the OpenMeteo client with the retry session
    openmeteo = openmeteo_requests.Client(session=retry_session)
    # Create a dictionary to store historical temperatures for 5 days
    historical_temps = {f"Day {i + 1}": [] for i in range(5)}
    # Get the current year
    current_year = datetime.now().year
    # Loop through the past 50 years
    for year in range(current_year - 50, current_year):
        # Loop for the next 5 days
        for i in range(5):
            # Calculate the date for each day
            date = datetime(year, 10, 2) + timedelta(days=i)
            # Format the date as a string
            start_date = date.strftime('%Y-%m-%d')
            # Create the parameters for the weather API request
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": start_date,
                "hourly": "temperature_2m"
            }
            # Send request to the weather archive API
            responses = openmeteo.weather_api("https://archive-api.open-meteo.com/v1/archive", params=params)
            # Take the first response (0)
            response = responses[0]
            # Retrieve hourly data from the response
            hourly = response.Hourly()
            #get hourly temp
            hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
            #find the days maximum temp
            max_temp = hourly_temperature_2m.max() if len(hourly_temperature_2m) > 0 else None
            #find the max temp of the corresonding day in history
            historical_temps[f"Day {i + 1}"].append(max_temp)

    # Initializes a list to store average temperatures for each day
    averages_list = []
    for key, temps in historical_temps.items():
        # Filter out None values
        valid_temps = [temp for temp in temps if temp is not None]
        #calculate average temp
        avg_temp = sum(valid_temps) / len(valid_temps) if valid_temps else None
        #add the averages to the list
        averages_list.append(avg_temp)

    # Get the current temperature and weather description
    current_temp, current_desc = get_current_weather(api_key, city)
    # Gets the predicted temperatures for the next 5 days
    predicted_temps = get_predicted_weather(api_key, lat, lon)

    # Prints the current temperature and weather description
    print(f'Current Temperature: {current_temp}°C, {current_desc}')
    # Create a dictionary to match weather descriptions to their emojis
    weather_icons = {
        'clear sky': "☀️",
        'few clouds': "⛅",
        'scattered clouds': "☁️   ☀️  ☁️",
        'broken clouds': "☁️ ☁️ ☀️ ☁️ ☁️",
        'overcast clouds': "☁️ ☁️ ☁️ ☁️ ☁️\n☁️ ☁️ ☁️ ☁️ ☁️",
        'light rain': "☁️🌧️\n   💧",
        'moderate rain': "☁️🌧️🌧️\n  💧💧💧",
        'heavy intensity rain': "☁️🌧️🌧️🌧️\n 💧💧💧💧💧",
        'freezing rain': "☁️🌧️❄️\n  💧❄️💧",
        'light intensity shower rain': "☁️🌧️\n   💧",
        'shower rain': "☁️🌧️🌧️\n///////",
        'heavy intensity shower rain': "☁️🌧️🌧️🌧️\n///////",
        'ragged shower rain': "☁️🌧️🌧️\n//////",
        'light intensity drizzle': "☁️🌦️\n  💧",
        'drizzle': "☁️🌦️\n 💧💧💧",
        'heavy intensity drizzle': "☁️🌦️🌦️\n💧💧💧💧💧",
        'light intensity drizzle rain': "☁️🌦️\n 💧",
        'drizzle rain': "☁️🌦️🌦️\n 💧💧",
        'heavy intensity drizzle rain': "☁️🌦️🌦️🌦️\n💧💧💧",
        'shower rain and drizzle': "☁️🌧️🌦️\n💧💧💧",
        'heavy shower rain and drizzle': "☁️🌧️🌧️🌦️\n💧💧💧💧",
        'shower drizzle': "☁️🌦️\n 💧💧",
        'thunderstorm with light rain': "☁️🌩️🌧️\n  💧💧",
        'thunderstorm with rain': "☁️🌩️🌧️🌧️",
        'thunderstorm with heavy rain': "☁️🌩️🌩️🌧️\n  💧💧💧",
        'light thunderstorm': "☁️🌩️",
        'thunderstorm': "☁️🌩️🌩️",
        'heavy thunderstorm': "☁️🌩️🌩️🌩️\n ⚡⚡⚡⚡",
        'ragged thunderstorm': "☁️🌩️🌩️🌩️",
        'thunderstorm with light drizzle': "☁️🌩️🌦️\n 💧",
        'thunderstorm with drizzle': "☁️🌩️🌦️🌦️\n 💧💧",
        'thunderstorm with heavy drizzle': "☁️🌩️🌦️🌦️🌦️\n💧💧💧",
        'light snow': "☁️🌨️\n ❄️❄️",
        'snow': "☁️🌨️🌨️\n❄️❄️❄️",
        'heavy snow': "☁️🌨️🌨️🌨️\n❄️❄️❄️❄️❄️",
        'sleet': "☁️🌨️🌧️\n ❄️💧❄️",
        'light shower sleet': "☁️🌨️\n ❄️",
        'shower sleet': "☁️🌨️🌧️\n ❄️💧",
        'light rain and snow': "☁️🌨️🌧️\n ❄️💧❄️",
        'rain and snow': "☁️🌨️🌧️🌧️\n❄️💧💧",
        'light shower snow': "☁️🌨️\n ❄️",
        'shower snow': "☁️🌨️🌨️\n ❄️❄️",
        'heavy shower snow': "☁️🌨️🌨️🌨️\n❄️❄️❄️",
        'mist': "🌫️🌫️🌫️",
        'smoke': "💨💨💨",
        'haze': "🌫️🌫️🌫️",
        'sand/ dust whirls': "💨🌪️💨",
        'fog': "🌁🌁🌁",
        'sand': "🌪️🌪️🌪️",
        'dust': "💨💨💨",
        'volcanic ash': "🌋🌫️🌫️",
        'squalls': "🌬️🌬️🌬️",
        'tornado': "🌪️🌪️🌪️"
    }

    # Use the dictionary to print the corresponding icon
    print(weather_icons.get(current_desc, "Unknown weather condition"))

    #convert the average temps to floats
    historical_temps_full = [float(num) for num in averages_list]
    #find the index for the current say in a 20 - day cycle
    current_day_index = datetime.now().day % 20
    historical_temps = historical_temps_full[current_day_index:current_day_index + 5] #sorts the list to get the historical temp for the next 5 days
    #label the days
    days = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5']

    #set up the plot
    plt.figure(figsize=(9, 5))
    # Plot the predicted temperatures
    plt.plot(days, predicted_temps, marker='o', linestyle='-', label='Predicted')
    # Plot the historical temperatures
    plt.plot(days, historical_temps_full, marker='x', linestyle='--', label='Historical')
    #set the title (size, font ect.)
    plt.title(f'Weather in {city}: Predicted vs Historical', fontdict={'fontsize': 15, 'fontname': 'Comic Sans MS', 'fontweight': 'bold'})
    #set the x axis label  (size, font ect.)
    plt.xlabel('Days', fontdict={'fontsize': 12, 'fontname': 'Comic Sans MS', 'fontweight': 'bold'})
    #set the y axis label  (size, font ect.)
    plt.ylabel('Temperature (°C)', fontdict={'fontsize': 12, 'fontname': 'Comic Sans MS', 'fontweight': 'bold'})
    #makr the legend
    plt.legend()
    plt.show()
#if something fails, print the error
else:
    print("Error: Cant retrieve the weather data for your location.")
