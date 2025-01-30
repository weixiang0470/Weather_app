from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class LinkApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 顯示超連結
        link_label = Label(
            text='[ref=google][color=0000FF][u]打開 Google[/u][/color][/ref]',
            markup=True,
            size_hint=(None, None),
            size=(200, 50)
        )
        
        # 綁定點擊事件
        link_label.bind(on_ref_press=lambda instance, value: self.open_link(value))

        layout.add_widget(link_label)

        return layout

    def open_link(self, url):
        import webbrowser
        webbrowser.open("https://www.google.com")

if __name__ == '__main__':
    LinkApp().run()
