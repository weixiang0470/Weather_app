import kivy
import pyjokes
import schedule
import threading
import time

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

kivy.require('2.1.0')  # 指定 Kivy 版本

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 顯示使用者的名字
        self.name_label = Label(text="你的名字: 小明", font_size='24sp', bold=True, halign='center')
        layout.add_widget(self.name_label)

        # 按鈕來打開笑話頁面
        joke_button = Button(text="打開笑話頁面", size_hint=(None, None), size=(200, 50))
        joke_button.bind(on_press=self.open_joke_screen)
        layout.add_widget(joke_button)

        self.add_widget(layout)

    def open_joke_screen(self, instance):
        self.manager.current = "joke_screen"  # 切換到笑話頁面

class JokeScreen(Screen):
    def __init__(self, **kwargs):
        super(JokeScreen, self).__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 笑話標籤
        self.joke_label = Label(text="載入中...", font_size='20sp', halign='center', valign='middle')
        self.joke_label.bind(size=self.joke_label.setter('text_size'))  # 自動換行
        layout.add_widget(self.joke_label)

        # 返回按鈕
        back_button = Button(text="返回主頁面", size_hint=(None, None), size=(200, 50))
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

        # 立即顯示笑話
        self.update_joke()

        # 設定定時器，每 5 分鐘更新一次
        schedule.every(5).minutes.do(self.schedule_joke_update)

        # 在背景執行定時器
        threading.Thread(target=self.run_schedule, daemon=True).start()

    def get_joke(self):
        """取得隨機笑話"""
        return pyjokes.get_joke(language="en", category="all")

    def update_joke(self, dt=None):
        """更新 UI 上的笑話"""
        new_joke = self.get_joke()
        self.joke_label.text = new_joke

    def schedule_joke_update(self):
        """讓 UI 在主執行緒上更新笑話"""
        Clock.schedule_once(self.update_joke)

    def run_schedule(self):
        """定時執行 `schedule.run_pending()`"""
        while True:
            schedule.run_pending()
            time.sleep(1)

    def go_back(self, instance):
        self.manager.current = "main_screen"  # 返回主頁面

class JokeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main_screen"))
        sm.add_widget(JokeScreen(name="joke_screen"))
        return sm

if __name__ == '__main__':
    JokeApp().run()
