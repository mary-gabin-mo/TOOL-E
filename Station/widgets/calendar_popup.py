from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from datetime import date
import calendar

class CalendarPopup(ModalView):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.7)  # Take up 90% width, 70% height
        self.callback = callback  # Function to call when date is confirmed
        self.background_color = (0, 0, 0, 0.5)  # Dimmed background
        self.auto_dismiss = True

        # State
        self.selected_date = None
        self.view_date = date.today()

        # Build UI
        self.build_ui()
        self.update_calendar()

    def build_ui(self):
        # Main Layout with white background
        layout = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        with layout.canvas.before:
            Color(1, 1, 1, 1)
            bg_rect = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(
            pos=lambda inst, val: setattr(bg_rect, 'pos', val),
            size=lambda inst, val: setattr(bg_rect, 'size', val)
        )

        # 1. Header (Month Navigation)
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing='10dp')

        btn_prev = Button(text='<', size_hint_x=None, width='48dp',
                          background_normal='', background_color=(0.85, 0.85, 0.85, 1), color=(0, 0, 0, 1))
        btn_prev.bind(on_release=lambda x: self.change_month(-1))
        header.add_widget(btn_prev)

        self.month_label = Label(text="", halign='center', font_size='20sp', color=(0, 0, 0, 1))
        header.add_widget(self.month_label)

        btn_next = Button(text='>', size_hint_x=None, width='48dp',
                          background_normal='', background_color=(0.85, 0.85, 0.85, 1), color=(0, 0, 0, 1))
        btn_next.bind(on_release=lambda x: self.change_month(1))
        header.add_widget(btn_next)
        layout.add_widget(header)

        # 2. Days Header (Mo, Tu, We, ...)
        days_header = GridLayout(cols=7, size_hint_y=None, height='30dp')
        for day in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Sun"):
            days_header.add_widget(Label(text=day, halign='center', bold=True, color=(0, 0, 0, 1)))
        layout.add_widget(days_header)

        # 3. Calendar Grid
        self.grid = GridLayout(cols=7, spacing='5dp', row_force_default=True, row_default_height=50)
        layout.add_widget(self.grid)

        # 4. Footer (Confirm Button)
        self.confirm_btn = Button(
            text="CONFIRM",
            size_hint=(0.33, None),
            height='48dp',
            pos_hint={'center_x': 0.5},
            disabled=True,
            background_normal='',
            background_color=(0.2, 0.7, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        self.confirm_btn.bind(on_release=self.on_confirm)

        footer = BoxLayout(size_hint_y=None, height='48dp')
        footer.add_widget(self.confirm_btn)
        layout.add_widget(footer)

        self.add_widget(layout)

    def change_month(self, delta):
        month = self.view_date.month + delta
        year = self.view_date.year
        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        self.view_date = date(year, month, 1)
        self.update_calendar()

    def update_calendar(self):
        self.grid.clear_widgets()
        year = self.view_date.year
        month = self.view_date.month

        self.month_label.text = f"{calendar.month_name[month]} {year}"

        cal = calendar.monthcalendar(year, month)
        today = date.today()

        for week in cal:
            for day in week:
                if day == 0:
                    self.grid.add_widget(Label(text="", size_hint=(1, 1)))
                else:
                    btn_date = date(year, month, day)
                    is_past = btn_date < today
                    is_selected = self.selected_date == btn_date

                    btn = Button(
                        text=str(day),
                        font_size="16sp",
                        size_hint=(1, 1),
                        background_normal=''
                    )

                    if is_selected:
                        btn.background_color = (0.2, 0.6, 0.8, 1)  # Blue
                        btn.color = (1, 1, 1, 1)
                    elif is_past:
                        btn.disabled = True
                        btn.background_color = (0.9, 0.9, 0.9, 1)
                        btn.color = (0.5, 0.5, 0.5, 1)
                    else:
                        btn.background_color = (1, 1, 1, 1)  # White
                        btn.color = (0, 0, 0, 1)
                        btn.bind(on_release=lambda x, d=btn_date: self.select_date(d))
                    self.grid.add_widget(btn)

    def select_date(self, date_obj):
        self.selected_date = date_obj
        self.confirm_btn.disabled = False
        self.update_calendar()

    def on_confirm(self, *args):
        if self.selected_date and self.callback:
            self.callback(self.selected_date)
        self.dismiss()