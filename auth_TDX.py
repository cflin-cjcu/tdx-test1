import requests
from pprint import pprint
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

app_id = 'cflin-39e3de14-50f0-4586'
app_key = '50ed8a2c-b15c-44c3-b1f3-8be9aa611931'

auth_url="https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
url = "https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/LiveTrainDelay?$top=30&$format=JSON"

class Auth():

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key

    def get_auth_header(self):
        content_type = 'application/x-www-form-urlencoded'
        grant_type = 'client_credentials'

        return{
            'content-type' : content_type,
            'grant_type' : grant_type,
            'client_id' : self.app_id,
            'client_secret' : self.app_key
        }

class data():

    def __init__(self, app_id, app_key, auth_response):
        self.app_id = app_id
        self.app_key = app_key
        self.auth_response = auth_response

    def get_data_header(self):
        auth_JSON = json.loads(self.auth_response.text)
        access_token = auth_JSON.get('access_token')

        return{
            'authorization': 'Bearer ' + access_token,
            'Accept-Encoding': 'gzip'
        }

def fetch_data():
    try:
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    except:
        a = Auth(app_id, app_key)
        auth_response = requests.post(auth_url, a.get_auth_header())
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    return data_response


if __name__ == '__main__':
    try:
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    except:
        a = Auth(app_id, app_key)
        auth_response = requests.post(auth_url, a.get_auth_header())
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())

fig = go.FigureWidget(px.bar(title='Station Delay Time'))
fig.show()

while True:
    data_response = fetch_data()
    df = pd.read_json(data_response.text)
       # 假設 StationName 欄位是字典，並且我們只取 Zh_tw 部分
    df['StationName'] = df['StationName'].apply(lambda x: x['Zh_tw'] if isinstance(x, dict) and 'Zh_tw' in x else None)
    
    # 更新圖表數據
    with fig.batch_update():
        fig.data = []  # 清空現有數據
        fig.add_trace(go.Bar(x=df['StationName'], y=df['DelayTime']))
    
    print(df)
    time.sleep(10)  # 等待兩分鐘



