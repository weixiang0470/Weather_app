from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
import requests
import os
import sqlite3

# WeatherAPI 的 API 金鑰 (請替換為你的 API 金鑰)
API_KEY = os.getenv("API_KEY")

class WeatherApp(App):
    def build(self):
        # 主佈局
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 輸入框
        self.location_input = TextInput(hint_text='Enter location (ex: Taipei, London, etc)', multiline=False, size_hint=(1, 0.1))
        layout.add_widget(self.location_input)

        # 查詢按鈕
        search_button = Button(text='Search weather', size_hint=(1, 0.1))
        search_button.bind(on_press=self.fetch_weather)
        layout.add_widget(search_button)

        # 天氣圖標
        self.weather_icon = AsyncImage(size_hint=(1, 0.3))
        layout.add_widget(self.weather_icon)

        # history_button = Button(text='History', size_hint=(1,0.1))
        # layout.add_widget(history_button)

        # 當前天氣結果
        self.current_weather_label = Label(text='', size_hint=(1, 0.3))
        layout.add_widget(self.current_weather_label)

        # 預報結果
        self.forecast_label = Label(text='', size_hint=(1, 0.3))
        layout.add_widget(self.forecast_label)

        return layout

    def fetch_weather(self, instance):
        # 取得使用者輸入的地點
        location = self.location_input.text.strip()
        if not location:
            self.result_label.text = "Please enter valid location!"
            return

        # 呼叫 WeatherAPI
        #url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={location}"
        url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=5"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # 解析天氣資料
                location_name = data['location']['name']
                temp_celsius = data['current']['temp_c']
                weather_desc = data['current']['condition']['text']
                icon_url = f"http:{data['current']['condition']['icon']}"

                # 更新當前天氣顯示
                self.weather_icon.source = icon_url
                self.current_weather_label.text = (f"Location: {location_name}\n"
                                                   f"Temperature: {temp_celsius:.1f}°C\n"
                                                   f"Weather: {weather_desc}")
                
                # 預報天氣資料
                forecast_data = data['forecast']['forecastday']
                forecast_text = "5-day forecast:\n"
                for day in forecast_data:
                    date = day['date']
                    max_temp = day['day']['maxtemp_c']
                    min_temp = day['day']['mintemp_c']
                    condition = day['day']['condition']['text']
                    forecast_text += (f"{date}: {condition}, "
                                      f"{min_temp:.1f}°C - {max_temp:.1f}°C\n")

                # 更新預報顯示
                self.forecast_label.text = forecast_text

            else:
                self.current_weather_label.text = "Weather information not found, please check the location is valid!"
                self.weather_icon.source = ""
                self.forecast_label.text = ""
        except Exception as e:
            self.current_weather_label.text = f"Error occur: {e}"
            self.weather_icon.source = ""
            self.forecast_label.text = ""

# 啟動應用程式
if __name__ == '__main__':
    WeatherApp().run()
