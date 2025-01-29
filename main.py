import re
import sqlite3
import requests
import pyjokes
import schedule
import threading
import json
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from datetime import datetime,timedelta
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy.clock import Clock

import currentcity
import Chi2Eng as CE
import Weather

# 初始化資料庫
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

def city():
    city = currentcity.get_city()
    return city

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

class WeatherApp(App):
    def build(self):
        init_db()

        # 主佈局
        input_layout = BoxLayout(orientation='vertical', padding=5, spacing=5)

        # 輸入框
        self.location_input = TextInput(hint_text='Enter city (ex: Taipei, London)', multiline=False, size_hint=(1, 0.1))
        self.start_date_input = TextInput(hint_text='Start data (YYYY-MM-DD, ex:2025-01-20)', multiline=False, size_hint=(1, 0.1))
        self.end_date_input = TextInput(hint_text='End date (YYYY-MM-DD, ex:2025-01-25)', multiline=False, size_hint=(1, 0.1))
        self.id_input = TextInput(hint_text='Enter record ID (For update or delete)', multiline=False, size_hint=(1, 0.1))
        #TextInput(hint_text='Enter how many days', multiline=False, size_hint=(1, 0.1), input_filter="int")
        input_layout.add_widget(self.location_input)
        input_layout.add_widget(self.start_date_input)
        input_layout.add_widget(self.end_date_input)
        input_layout.add_widget(self.id_input)

        # 操作按鈕
        button_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        search_button = Button(text='Search', size_hint=(1, 0.1))
        search_button.bind(on_press=self.search_weather)
        button_layout.add_widget(search_button)

        # save_button = Button(text='Add to History', size_hint=(1, 0.1))

        read_button = Button(text='History', size_hint=(1, 0.1))
        read_button.bind(on_press=self.read_records)
        button_layout.add_widget(read_button)

        update_button = Button(text='Update (ID)', size_hint=(1, 0.1))
        update_button.bind(on_press=self.update_record)
        button_layout.add_widget(update_button)

        delete_button = Button(text='Delete (ID)', size_hint=(1, 0.1))
        delete_button.bind(on_press=self.delete_record)
        button_layout.add_widget(delete_button)

        input_both_layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        input_both_layout.add_widget(input_layout)
        input_both_layout.add_widget(button_layout)

        # 結果顯示
        output_layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)
        # font_name="NotoSansCJK-Regular.ttf"
        # output_layout_left1 = BoxLayout(orientation='vertical', spacing=10, padding=5)
        self.current_waether_output = Label(text='Current Weather:', size_hint=(1, 0.5),pos_hint={'center_x': 0.5, 'center_y': 0.5})
        

        # 天氣圖標
        self.weather_icon = AsyncImage(size_hint=(1, 0.1),pos_hint={'center_x': 0.5, 'center_y': 0.5},allow_stretch= True)
        # output_layout_left1.add_widget(self.weather_icon)
        # output_layout_left1.add_widget(self.current_waether_output)

        output_layout_left2 = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.forecast_waether_output = ScrollableLabel(text='Forecast Weather:', size_hint=(1, 0.5))
        output_layout_left2.add_widget(self.weather_icon)
        output_layout_left2.add_widget(self.forecast_waether_output)


        self.search_waether_output = ScrollableLabel(text='Search Weather:', size_hint=(1, 1))

        output_file_b = Button(text='Output history')
        output_file_b.bind(on_press=self.output_file)


        output_layout.add_widget(output_layout_left2)
        output_layout.add_widget(self.search_waether_output)
        output_layout.add_widget(output_file_b)

        main_layout = BoxLayout(orientation='vertical', spacing=10)
        main_layout.add_widget(input_both_layout)
        main_layout.add_widget(output_layout)
        self.show_current()
        self.update_joke()
        # 設定定時器，每30秒更新一次
        schedule.every(0.5).minutes.do(self.schedule_joke_update)
        # 在背景執行定時器
        threading.Thread(target=self.run_schedule, daemon=True).start()

        return main_layout

    def validate_date_range(self, start, end,today):
        try:
            # start = datetime.strptime(start_date, "%Y-%m-%d")
            
            # end = datetime.strptime(end_date, "%Y-%m-%d")
            r = end-start
            # print(f'{start=}, {end=}, {end-start}, {range.days=}')
            # if range.days>14: what_condition="future"
            # else: what_condition="forecast"
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
            # delta = end - start
            # print(f'{delta=}, {delta.days=}, type:{type(delta.days)}')
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
                    if cnt<=(start-today).days or cnt>14:continue
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
                    # print(day)
                    forecast = Weather.fetch_future_weather(location,day)
                    future_weather+=forecast
            # print(f'{forecast=}')
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
        except Exception as e:
            print(f'Error in search weather: {e}')
            self.search_waether_output.text = str(e)

    def read_records(self, instance):

        try:
            conn = sqlite3.connect("weather.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM weather_requests")
            rows = cursor.fetchall()
            conn.close()

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

        except Exception as e:
            self.search_waether_output.text = str(e)

    def update_record(self, instance):
        record_id = self.id_input.text.strip()
        records = self.location_input.text.strip()
        # start_date = self.start_date_input.text.strip()
        # end_date = self.end_date_input.text.strip()

        if not record_id.isdigit():
            self.search_waether_output.text = "Please enter valid ID!"
            return

        if not records:
            self.search_waether_output.text = "Data can not be empty!"
            return
        # if not self.validate_date_range(start_date, end_date):
        #     self.search_waether_output.text = "Date range invalid! Please enter correct date."
        #     return
        
        # forecast = self.fetch_weather(location, start_date, end_date)
        # if not forecast:
        #     self.search_waether_output.text = "Invalid location(city) or weather information not found!"
        #     return
        try : 
            conn = sqlite3.connect("weather.db")
            cursor = conn.cursor()
            cursor.execute("Select id From weather_requests")
            all_id_tuple = cursor.fetchall()
            all_id = [item[0] for item in all_id_tuple]
            # print(record_id,type(record_id))
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
        
        except Exception as e:
            self.search_waether_output.text = str(e)
            print(e)

    def delete_record(self, instance):
        record_id = self.id_input.text.strip()

        # print(f'id input = {record_id}')
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
        except Exception as e:
            self.search_waether_output.text = str(e)
            print(e)

    def show_current(self):
        current_city = city()
        if(CE.contains_chinese(current_city)):current_city=CE.translate_to_english(current_city)
        # url_forecast = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={current_city}&days=5"
        icon,current_weather,forecast_weather = Weather.fetch_forecast_weather(current_city)

        # self.current_waether_output.text=current_weather
        self.forecast_waether_output.text = forecast_weather
        self.weather_icon.source = icon
        self.current_waether_output.text = forecast_weather
    
    def get_joke(self):
        """取得隨機笑話"""
        return pyjokes.get_joke(language="en", category="all")

    def update_joke(self, dt=None):
        """更新 UI 上的笑話"""
        new_joke = self.get_joke()
        weather_info = self.current_waether_output.text
        self.forecast_waether_output.text = weather_info+new_joke

    def schedule_joke_update(self):
        """讓 UI 在主執行緒上更新笑話"""
        Clock.schedule_once(self.update_joke)

    def run_schedule(self):
        """定時執行 `schedule.run_pending()`"""
        while True:
            schedule.run_pending()
            time.sleep(1)



if __name__ == '__main__':
    WeatherApp().run()
    # WeatherApp.show_current()