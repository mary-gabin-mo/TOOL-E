from kivy.uix.modalview import ModalView
from kivymd.uix.button import MDFillRoundFlatButton, MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from datetime import date, timedelta
import calendar

class CalendarPopup(ModalView):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.9)
        self.callback = callback # Function to call when date is confirmed
        self.size_hint = (0.9, 0.7) # Take up 90% width, 70% height
        self.background_color = (0, 0, 0, 0.5) # Dimmed background
        self.auto_dismiss = True
        
        # State
        self.selected_date = None
        self.view_date = date.today()
        
        # Build UI
        self.build_ui()
        self.update_calendar()
        
    def build_ui(self):
        # Main Layout
        layout = MDBoxLayout(orientation='vertical', padding='10dp', spacing='10dp', md_bg_color=(1,1,1,1))
        
        # 1. Header (Month Navigation)
        header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing='10dp')
        header.add_widget(MDIconButton(icon='chevron-left', on_release=lambda x: self.change_month(-1)))
        
        self.month_label = MDLabel(text="", halign='center', font_style='H6', theme_text_color='Primary')
        header.add_widget(self.month_label)
        
        header.add_widget(MDIconButton(icon='chevron-right', on_release=lambda x: self.change_month(1)))
        layout.add_widget(header)
        
        # 2. Days Header (Mo, Tu, We, ...)
        days_header = MDGridLayout(cols=7, size_hint_y=None, height='30dp')
        for day in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Sun"):
            days_header.add_widget(MDLabel(text=day, halign='center', bold=True))
        layout.add_widget(days_header)
        
        # 3. Calendar Grid
        self.grid = MDGridLayout(cols=7, spacing='5dp', row_force_default=True, row_default_height=50)
        layout.add_widget(self.grid)
        
        # 4. Footer (Confirm Button)
        self.confirm_btn = MDFillRoundFlatButton(
            text="CONFIRM", 
            size_hint_x=1,
            disabled=True,
            md_bg_color=(0.2, 0.7, 0.2, 1),
            on_release=self.on_confirm
        )
        layout.add_widget(self.confirm_btn)
        
        self.add_widget(layout)
        
    def change_month(self, delta):
        # Logic to change self.view_date month/year
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
                    self.grid.add_widget(MDLabel(text="", size_hint=(1, 1)))
                else:
                    btn_date = date(year, month, day)
                    is_past = btn_date < today
                    is_selected = self.selected_date == btn_date
                    
                    btn = MDFillRoundFlatButton(
                        text=str(day),
                        font_size="16sp",
                        size_hint=(1, 1)
                    )
                    
                    if is_selected:
                        btn.md_bg_color = (0.2, 0.6, 0.8, 1) #Blue
                    elif is_past:
                        btn.disabled = True
                        btn.md_bg_color = (0.9, 0.9, 0.9, 1)
                    else:
                        btn.md_bg_color = (1, 1, 1, 1) # White
                        btn.text_color = (0,0,0,1)
                        # Bind selection
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