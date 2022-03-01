from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix import MDAdaptiveWidget
import text_about_pollution as tap
import requests
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
import mysql.connector
import datetime
import calendar


class MDFloatLayout(FloatLayout, MDAdaptiveWidget):
    pass

class Content(BoxLayout):
    pass

class dbContent(BoxLayout):
    pass

class score_dialog(BoxLayout):
    pass

class RunningApp(MDApp):
    
    dialog = None
    today = str(datetime.date.today())
    score=''
    statistics = 0
    dialog_score_acivated = 0
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_tables = None

    def build(self):
        self.title = 'SmartActivities'
        self.icon = 'images/runrun.png'
        self.theme_cls.theme_style = 'Light'
        mydb = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        passwd = '1234',
        database = 'db'
        )
        
        c = mydb.cursor()
        c.execute("CREATE DATABASE IF NOT EXISTS db")
        c.execute("""
            CREATE TABLE if not exists a(run_id INT AUTO_INCREMENT PRIMARY KEY, day DATE, distance INT(4), av_speed INT(4))""")

        return Builder.load_file('kivy_file.kv')

    def dialog_text(self):
        dialog_text=MDDialog(title='The scale of pollution',text=tap.text())
        dialog_text.open()

    def show_alert_dialog(self):
        if not self.dialog:
                    self.dialog = MDDialog(
                        type="custom",
                        content_cls=Content(),
                        buttons=[
                            MDFlatButton(
                                text="OK",
                                theme_text_color="Custom",
                                text_color=self.theme_cls.primary_color,
                                on_release= self.confirm_location
                            ),
                        ],
                    )
        self.dialog.open()


    def dialog_add_to_table(self):
        self.table_dialog=MDDialog(content_cls=dbContent(), type='custom')
        self.table_dialog.open()

    def get_inf_from_api(self, city, state, country):
        url = f'http://api.airvisual.com/v2/city?city={city}&state={state}&country={country}&key=d4f52dd4-1587-4bea-b72c-b48ea545656b'
        response = requests.get(url)
        self.data = response.json()
            

    def confirm_location(self,obj):
        self.get_inf_from_api(self.dialog.content_cls.ids.textfield_city.text,self.dialog.content_cls.ids.textfield_state.text,self.dialog.content_cls.ids.textfield_country.text)
        if self.data['status'] == 'fail':
            self.dialog.content_cls.ids.labeltest.text='Localization not found. Try again'
        else:
            city = self.data['data']['city']
            pollution = self.data['data']['current']['pollution']['aqius']
            weather = str(self.data['data']['current']['weather']['tp'])
            wind =round(3.6 * float(self.data['data']['current']['weather']['ws']), 1)
            weather_icon_api = self.data['data']['current']['weather']['ic']
            self.root.ids.weather_icon.icon = f'images/{str(weather_icon_api)}.png'
            self.root.ids.city.secondary_text= str(self.dialog.content_cls.ids.textfield_city.text)
            self.root.ids.pollution.secondary_text = str(pollution)
            self.root.ids.question_mark.icon = 'images/quesmark.png'
            self.root.ids.weather.secondary_text = weather + '°C'
            self.root.ids.wind.secondary_text = str(wind) + ' km/h'

            
            if pollution > 0 and pollution < 51: 
                self.root.ids.pollution.bg_color = get_color_from_hex('98FA4C')
            elif pollution > 50 and pollution < 101:
                self.root.ids.pollution.bg_color = get_color_from_hex('FFFF33')
            elif pollution > 100 and pollution < 151:
                self.root.ids.pollution.bg_color = get_color_from_hex('FF9933')
            elif pollution>150 and pollution < 201:
                self.root.ids.pollution.bg_color = get_color_from_hex('FF6666')
            elif pollution > 200 and pollution < 301:
                self.root.ids.pollution.bg_color = get_color_from_hex('CC99FF')
            else:
                self.root.ids.pollution.bg_color = get_color_from_hex('B685CE')
            
            self.dialog.dismiss()
            Snackbar(text="Click the question mark to see informations about pollution index").open()

    def add_to_db(self):
        mydb = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        passwd = '1234',
        database = 'db'
        )
        c=mydb.cursor()
        distance = str(self.table_dialog.content_cls.ids.table_distance.text)
        speed = str(self.table_dialog.content_cls.ids.table_speed.text)
        data =str(self.table_dialog.content_cls.ids.table_date.text) 
        sql_command = f"INSERT INTO a (day, distance, av_speed) VALUES ('{data}',{distance},{speed})"
        c.execute(sql_command)
        mydb.commit()
        mydb.close()
        RunningApp.add_datatable(self)
        self.table_dialog.dismiss()

    def add_datatable(self):
        mydb = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        passwd = '1234',
        database = 'db'
        )
        c=mydb.cursor()

        c.execute('select * from a order by run_id desc')
        records = c.fetchall()
        data_from_db = []
        empty=''
        for record in records:
            data_from_db.append(record)
        row=[]
        for elements in data_from_db:
            nawias = []
            for element in elements:
                nawias.append(str(element))
            row.append(nawias)

        self.data_tables = MDDataTable(
            size_hint=(0.85, 0.8),
            check = True,
            use_pagination = True,
            pagination_menu_height='240dp',
            column_data=[
                ("Date", dp(30)),
                ("Distance", dp(30)),
                ("Average speed", dp(30)),
                ("Number", dp(30)), 
            ],
            row_data=[(f"{i[1]}", f"{i[2]}", f"{i[3]}", f"{i[0]}")for i in row]
        )
        self.data_tables.bind(on_check_press=self.row_checked)
        self.root.ids.data_layout.add_widget(self.data_tables)
    
    def row_checked(self, instance_table,current_row):
        self.row_to_delete = current_row
        print(self.row_to_delete)
    def delete_row(self):
        mydb = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        passwd = '1234',
        database = 'db'
        )
        c=mydb.cursor()
        c.execute(f'delete from a where run_id ={self.row_to_delete[3]}')
        mydb.commit()
        mydb.close()
        RunningApp.add_datatable(self)

    def update_progress(self):
        mydb = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        passwd = '1234',
        database = 'db'
        )
        c=mydb.cursor()

        today = datetime.date.today()
        day_of_the_week=calendar.day_name[today.weekday()]
        d = datetime.datetime.now()
        day_of_the_month = d.strftime("%d")
        c.execute('select day,distance from a order by run_id desc limit 7;')
        results = c.fetchall()
        self.week_score = 0

        if day_of_the_week == 'Sunday':
            for i in range(6,-1,-1):
                week_ago = today - datetime.timedelta(days=i)
                for row in results:
                    if row[0] ==  week_ago:
                        self.week_score += row[1]
        if day_of_the_week == 'Saturday':
            for i in range(5,-1,-1):
                week_ago = today - datetime.timedelta(days=i)
                for row in results:
                    if row[0] ==  week_ago:
                        self.week_score += row[1]
        if day_of_the_week == 'Friday':
            for i in range(4,-1,-1):
                week_ago = today - datetime.timedelta(days=i)
                for row in results:
                    if row[0] ==  week_ago:
                        self.week_score += row[1]
        if day_of_the_week == 'Thursday':
            for i in range(3,-1,-1):
                week_ago = today - datetime.timedelta(days=i)
                for row in results:
                    if row[0] ==  week_ago:
                        self.week_score += row[1]
        if day_of_the_week == 'Wednesday':
            for i in range(2,-1,-1):
                week_ago = today - datetime.timedelta(days=i)
                for row in results:
                    if row[0] ==  week_ago:
                        self.week_score += row[1]
        if day_of_the_week == 'Tuesday':
            for i in range(1,-1,-1):
                week_ago = today - datetime.timedelta(days=i)
                for row in results:
                    if row[0] ==  week_ago:
                        self.week_score += row[1]
        if day_of_the_week == 'Monday':
            for row in results:
                if row[0] == today:
                    self.week_score += row[1]

        self.score=self.week_score
        date_of_run = results[0][0]
        message = '{:%d}'
        
        self.root.ids.week_km.secondary_text = str(self.week_score)
        if self.dialog_score_acivated == 1:
            RunningApp.update_progress_bar(self)
            self.statistics=1
        today_km = 0
        for row in results:
            if row[0] == today:
                today_km += int(row[1])
        self.root.ids.today_km.secondary_text=str(today_km)
        RunningApp.calculate_calories(self,today_km, self.week_score)

    def choose_week_score(self):
        self.dialog_score=MDDialog(content_cls=score_dialog(), type='custom')
        self.dialog_score.open()
        self.dialog_score_acivated = 1


    def update_progress_bar(self):
        self.statistics == 0
        self.root.ids.my_label.text='Weekly goal progress: \n' + str(self.score)+f' / {self.dialog_score.content_cls.ids.km.text} km'
        self.root.ids.my_progress_bar.value = self.week_score/ int(self.dialog_score.content_cls.ids.km.text)

    def calculate_calories(self, km, week_km):
        # 62kcal na 1km
        today_calories = km * 62
        week_calories = week_km * 62
        self.root.ids.today_calories.secondary_text = str(today_calories)
        self.root.ids.week_calories.secondary_text = str(week_calories)

if __name__ == "__main__":
    RunningApp().run()
