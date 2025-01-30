import requests
import os

# Get api key from .env
API_KEY = os.getenv("API_KEY")

# Get current weather information and forecast informatioin
def fetch_forecast_weather(location,start=1,end=14,c=None):
        # 呼叫 WeatherAPI
        url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=14"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Get weather information
                location_name = data['location']['name']
                temp_celsius = data['current']['temp_c']
                weather_desc = data['current']['condition']['text']
                icon_url = f"http:{data['current']['condition']['icon']}"

                icon = icon_url
                current_weather = ( f"- {location_name} | {weather_desc} | {temp_celsius:.1f}°C -\n")
                
                # forecast information
                forecast_data = data['forecast']['forecastday']
                if c==None:forecast_text = current_weather+"13-day forecast:\n"
                else:forecast_text=current_weather
                cnt = 0
                for day in forecast_data:
                    cnt+=1
                    if cnt<=start:continue
                    date = day['date']
                    max_temp = day['day']['maxtemp_c']
                    min_temp = day['day']['mintemp_c']
                    condition = day['day']['condition']['text']
                    forecast_text += (f"{date}: {condition}, {min_temp:.1f}°C - {max_temp:.1f}°C\n")
                    if cnt>=end:break

                forecast_weather = forecast_text

                return icon,current_weather,forecast_weather

            else:
                current_weather = "Weather information not found, please check the location is valid!"
                icon = ""
                forecast_weather = ""

                return icon,current_weather,forecast_weather
        except Exception as e:
            current_weather = f"Error occur: {e}"
            icon = ""
            forecast_weather = ""

            return icon,current_weather,forecast_weather
        

# Get weather information using future api
def fetch_future_weather(location,start_date):
     
    url = f"http://api.weatherapi.com/v1/future.json?key={API_KEY}&q={location}&dt={start_date}"
     
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            future_data = data['forecast']['forecastday'][0]
            date = future_data["date"]
            # print(f'{date=}')
            max_temp = future_data['day']['maxtemp_c']
            # print(f'{max_temp=}')
            min_temp = future_data["day"]["mintemp_c"]
            condition = future_data['day']['condition']['text']
            # print(f'{condition=}')
            future_weather = (f"{date}: {condition}, {min_temp:.1f}°C - {max_temp:.1f}°C\n")
            return future_weather
        else:
            future_weather = "Weather information not found, please check the location or date is valid!"
            return future_weather
    except Exception as e:
        future_weather = f"Error occur: {e}"
        return future_weather