import kivy
import re
import sqlite3
import requests
import pyjokes
import schedule
import threading
import json
import time
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from datetime import datetime,timedelta
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.clock import Clock

import currentcity
import Chi2Eng as CE
import Weather

kivy.require('2.1.0')
# Initial database
def init_db():
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location TEXT,
            records TEXT
        )
    """)
    conn.commit()
    conn.close()

# Get current city
def city():
    city = currentcity.get_city()
    print(f'{city=}')
    return city

## Scrollable label building
Builder.load_string('''
<ScrollableLabel>:
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
''')

class ScrollableLabel(ScrollView):
    text = StringProperty('')

# Weather screen
class WeatherScreen(Screen):
    def __init__(self, **kwargs):
        super(WeatherScreen, self).__init__(**kwargs)

        # Input layout
        input_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)

        # Input text
        self.location_input = TextInput(hint_text='Enter city (ex: Taipei, London)', multiline=False, size_hint=(1, 0.1))
        self.start_date_input = TextInput(hint_text='Start data (YYYY-MM-DD, ex:2025-01-20)', multiline=False, size_hint=(1, 0.1))
        self.end_date_input = TextInput(hint_text='End date (YYYY-MM-DD, ex:2025-01-25)', multiline=False, size_hint=(1, 0.1))
        self.id_input = TextInput(hint_text='Enter record ID (For update or delete)', multiline=False, size_hint=(1, 0.1))
        #TextInput(hint_text='Enter how many days', multiline=False, size_hint=(1, 0.1), input_filter="int")
        input_layout.add_widget(self.location_input)
        input_layout.add_widget(self.start_date_input)
        input_layout.add_widget(self.end_date_input)
        input_layout.add_widget(self.id_input)

        # Button layout
        button_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Search button
        search_button = Button(text='Search', size_hint=(1, 0.1))
        search_button.bind(on_press=self.search_weather)
        button_layout.add_widget(search_button)

        # Read database button
        read_button = Button(text='History', size_hint=(1, 0.1))
        read_button.bind(on_press=self.read_records)
        button_layout.add_widget(read_button)

        # Update button
        update_button = Button(text='Update (ID)', size_hint=(1, 0.1))
        update_button.bind(on_press=self.update_record)
        button_layout.add_widget(update_button)

        # Delete button
        delete_button = Button(text='Delete (ID)', size_hint=(1, 0.1))
        delete_button.bind(on_press=self.delete_record)
        button_layout.add_widget(delete_button)

        # Input text and button layout
        input_both_layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        input_both_layout.add_widget(input_layout)
        input_both_layout.add_widget(button_layout)

        # Output layout
        output_layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)
        self.current_waether_output = Label(text='Current Weather:', size_hint=(1, 0.5),pos_hint={'center_x': 0.5, 'center_y': 0.5})
        # Weather icon
        self.weather_icon = AsyncImage(size_hint=(1, 0.1),pos_hint={'center_x': 0.5, 'center_y': 0.5},allow_stretch= True)

        # Current weather information layout
        output_layout_left2 = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.forecast_waether_output = ScrollableLabel(text='Forecast Weather:', size_hint=(1, 0.5))
        output_layout_left2.add_widget(self.weather_icon)
        output_layout_left2.add_widget(self.forecast_waether_output)

        # Search area output scrollable label
        self.search_waether_output = ScrollableLabel(text='Search Weather:', size_hint=(1, 1))

        # Output history file button
        output_file_b = Button(text='Output history')
        output_file_b.bind(on_press=self.output_file)

        # About button
        about_us_b = Button(text="About")
        about_us_b.bind(on_press = self.about_us)

        # Output area layout
        output_layout.add_widget(output_layout_left2)
        output_layout.add_widget(self.search_waether_output)
        output_layout.add_widget(output_file_b)
        output_layout.add_widget(about_us_b)

        # Weather Screen layout
        main_layout = BoxLayout(orientation='vertical', spacing=10)
        main_layout.add_widget(input_both_layout)
        main_layout.add_widget(output_layout)
        self.add_widget(main_layout)
        self.show_current()
        self.update_joke()
        # Set refresh joke every 30 seconds
        schedule.every(0.5).minutes.do(self.schedule_joke_update)
        # schedule in background
        threading.Thread(target=self.run_schedule, daemon=True).start()

    # Check date range is valid and the date range is in which condition
    def validate_date_range(self, start, end,today):
        try:
            r = end-start
            if(r.days>=0): 
                if (start - today).days <=14 and (end-today).days <=14:
                    return r.days + 1,0
                elif (start - today).days <=14 and (end-today).days > 14:
                    return r.days + 1,1
                else:
                    return r.days + 1,2
            else: return r.days>=0,None
        except ValueError:
            return False

    # def fetch_forecast_weather(self, location, start_date=None, end_date=None,range=None,url=None):
        # url_forecast = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days={range}"
        # url_future = f"http://api.weatherapi.com/v1/future.json?key={API_KEY}&q={location}&dt={start_date}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # 解析天氣資料
                # location_name = data['location']['name']
                # temp_celsius = data['current']['temp_c']
                # weather_desc = data['current']['condition']['text']
                # icon_url = f"http:{data['current']['condition']['icon']}"
                #forecast = data['forecast']['forecastday']
                forecast_data = data['forecast']['forecastday']
                forecast_text = ""
                for day in forecast_data:
                    date = day['date']
                    max_temp = day['day']['maxtemp_c']
                    min_temp = day['day']['mintemp_c']
                    condition = day['day']['condition']['text']
                    forecast_text += (f"{date}: {condition}, "
                                      f"{min_temp:.1f}°C - {max_temp:.1f}°C\n")
                return forecast_text
            else:
                return None
        except Exception:
            return None

    # Search weather information
    def search_weather(self,instance):
        location = self.location_input.text.strip()
        start_date = self.start_date_input.text.strip()
        end_date = self.end_date_input.text.strip()
        try:
            today_date = datetime.today().strftime('%Y-%m-%d')
            today = datetime.strptime(today_date, "%Y-%m-%d")
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            r,c =self.validate_date_range(start, end,today)

            if not r:
                self.search_waether_output.text = "Date range invalid! Please enter correct date."
                return
            print(f'{r=}')
            if r==-1:
                self.search_waether_output.text = "Start date should between 14 days and 300 days from today"
                return
            if r > 7:
                self.search_waether_output.text = "Please don't over 10 days"
                return
            future_weather=(f"{location}\n")
            if c ==0 or c==1:
                icon,current_weather,forecast = Weather.fetch_forecast_weather(location,c=1)
                t = re.split(r'\n',forecast)
                cnt=0
                for l in t:
                    cnt+=1
                    if cnt<=(start-today).days or cnt>14 or cnt>(end-today).days+1:continue
                    future_weather+=l+"\n"
                if c==1:
                    new_starttime = today + timedelta(days=14)
                    for i in range((end-new_starttime).days+1):
                        day = new_starttime + timedelta(days=i)
                        forecast = Weather.fetch_future_weather(location,day)
                        future_weather+=forecast

            elif c==2:
                for i in range(r):
                    day = start + timedelta(days=i)
                    forecast = Weather.fetch_future_weather(location,day)
                    future_weather+=forecast
            if not forecast:
                self.search_waether_output.text = "Invalid location(city) or weather information not found!"
                return

            conn = sqlite3.connect("weather.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO weather_requests (location, records) VALUES (?, ?)",
                        (location , future_weather))
            conn.commit()
            conn.close()

            self.search_waether_output.text = future_weather
            self.clear_input()
        except Exception as e:
            print(f'Error in search weather: {e}')
            self.search_waether_output.text = str(e)
            self.clear_input()

    # Read from database and show it
    def read_records(self, instance):

        try:
            conn = sqlite3.connect("weather.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM weather_requests")
            rows = cursor.fetchall()
            conn.close()
            self.clear_input()

            if rows:
                result = "All records:\n"
                # print(f'{rows=}')
                for row in rows:
                    result += f"{row[0]}, {row[1]}, {row[2]}, {row[3]}\n"
                self.search_waether_output.text = result
            else:
                self.search_waether_output.text = "Empty record!"
        except Exception as e:
            self.search_waether_output.text = str(e)
            self.clear_input()

    # Output history.json file from database
    def output_file(self,instance):
        try:
            conn = sqlite3.connect("weather.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM weather_requests")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            conn.close()

            data = [dict(zip(column_names, row)) for row in rows]
            # print(data)
            with open("history.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print("output sucessfully")
            self.search_waether_output.text = "Output file sucessfully"

        except Exception as e:
            self.search_waether_output.text = str(e)

    # Update records in database
    def update_record(self, instance):
        record_id = self.id_input.text.strip()
        records = self.location_input.text.strip()

        if not record_id.isdigit():
            self.search_waether_output.text = "Please enter valid ID!"
            return

        if not records:
            self.search_waether_output.text = "Data can not be empty!"
            return
        
        try : 
            conn = sqlite3.connect("weather.db")
            cursor = conn.cursor()
            cursor.execute("Select id From weather_requests")
            all_id_tuple = cursor.fetchall()
            all_id = [item[0] for item in all_id_tuple]

            if int(record_id) not in all_id:
                self.search_waether_output.text = "ID not found!"
                conn.close()
                return
            cursor.execute("""
                UPDATE weather_requests
                SET records=?
                WHERE id = ?
            """, (records, record_id))
            conn.commit()
            conn.close()

            self.search_waether_output.text = f"Record ID {record_id} updated!"
            self.clear_input()
        except Exception as e:
            self.search_waether_output.text = str(e)
            self.clear_input()
            print(e)

    # Delete records in databse
    def delete_record(self, instance):
        record_id = self.id_input.text.strip()

        if not record_id.isdigit():
            self.search_waether_output.text = "Please enter valid ID!"
            return

        try:
            conn = sqlite3.connect("weather.db")
            cursor = conn.cursor()
            cursor.execute("Select id From weather_requests")
            all_id_tuple = cursor.fetchall()
            all_id = [item[0] for item in all_id_tuple]
            if int(record_id) not in all_id:
                self.search_waether_output.text = "ID not found!"
                conn.close()
                return
            cursor.execute("DELETE FROM weather_requests WHERE id = ?", (record_id,))
            conn.commit()
            conn.close()

            self.search_waether_output.text = f"Record ID {record_id} deleted!"
            self.clear_input()
        except Exception as e:
            self.search_waether_output.text = str(e)
            self.clear_input()
            print(e)

    # Clear input text
    def clear_input(self):
        self.location_input.text = ""
        self.start_date_input.text = ""
        self.end_date_input.text = ""
        self.id_input.text = ""
    
    # Show current weather information
    def show_current(self):
        current_city = city()
        if(CE.contains_chinese(current_city)):current_city=CE.translate_to_english(current_city)
        icon,current_weather,forecast_weather = Weather.fetch_forecast_weather(current_city)

        self.forecast_waether_output.text = forecast_weather
        self.weather_icon.source = icon
        self.current_waether_output.text = forecast_weather
    
    # Get a joke
    def get_joke(self):
        return pyjokes.get_joke(language="en", category="all")

    # Update joke on screen
    def update_joke(self, dt=None):
        new_joke = self.get_joke()
        weather_info = self.current_waether_output.text
        self.forecast_waether_output.text = weather_info+new_joke

    # Schedule update joke
    def schedule_joke_update(self):
        Clock.schedule_once(self.update_joke)

    # Set schedule
    def run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    # Change to About screen
    def about_us(self,instance):
        self.manager.current = "about_screen"

# About screen
class AboutScreen(Screen):
    def __init__(self, **kwargs):
        super(AboutScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        pm_description = self.read_text_file("description.txt")
        pma_url = "https://www.linkedin.com/school/pmaccelerator/"
        wwx_url = "https://www.linkedin.com/in/wong-wei-xiang-709722345/"

        # My linkedin
        intro = Label(text="[ref=google][color=0000FF][u]Wong Wei Xiang[/color][/u][/ref]",markup=True)
        intro.bind(on_ref_press=lambda instance, value: self.open_link(wwx_url))

        # PM Accelerator linkedin
        pm_intro = Label(text="[ref=google][color=0000FF][u]Product Manager Accelerator[/color][/u][/ref]",markup=True)
        pm_intro.bind(on_ref_press=lambda instance, value: self.open_link(pma_url))

        # Description
        self.PM_Accelerator = ScrollableLabel(text=pm_description, size_hint=(1, 1))
        back_button = Button(text="Back to Weather")
        back_button.bind(on_press = self.go_back_weather)

        layout.add_widget(intro)
        layout.add_widget(pm_intro)
        layout.add_widget(self.PM_Accelerator)
        layout.add_widget(back_button)

        self.add_widget(layout)
    
    # Open link in browser
    def open_link(self,url):
        webbrowser.open(url)
    
    # Go weather screen
    def go_back_weather(self,instance):
        self.manager.current = "weather_screen"

    # Read description text file
    def read_text_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return "Description not found"
        except Exception as e:
            return f"Error: {e}"

# Weather app
class WeatherApp(App):
    def build(self):
        init_db()
        sm = ScreenManager()
        sm.add_widget(WeatherScreen(name="weather_screen"))
        sm.add_widget(AboutScreen(name="about_screen"))
        sm.current = "weather_screen"
        return sm
if __name__ == '__main__':
    WeatherApp().run()