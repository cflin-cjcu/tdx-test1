import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# 配置常數
APP_ID = 'cflin-39e3de14-50f0-4586'
APP_KEY = '50ed8a2c-b15c-44c3-b1f3-8be9aa611931'
AUTH_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
API_URL = "https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/LiveTrainDelay?$top=30&$format=JSON"

class Auth:
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self._token = None
        self._token_expires_at = 0

    def get_auth_header(self):
        """獲取驗證用的 header"""
        return {
            'content-type': 'application/x-www-form-urlencoded',
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_key
        }

    def get_access_token(self):
        """獲取並管理 access token"""
        current_time = time.time()
        
        # 如果 token 還有效，直接返回
        if self._token and current_time < self._token_expires_at:
            return self._token

        try:
            # 重新獲取 token
            response = requests.post(AUTH_URL, self.get_auth_header())
            response.raise_for_status()  # 確認請求成功
            
            auth_data = response.json()
            self._token = auth_data.get('access_token')
            # 設定 token 過期時間（預留 60 秒緩衝）
            self._token_expires_at = current_time + auth_data.get('expires_in', 3600) - 60
            
            return self._token
        except requests.exceptions.RequestException as e:
            print(f"Error getting access token: {e}")
            raise

def fetch_data(auth):
    """獲取列車延誤資料"""
    try:
        token = auth.get_access_token()
        headers = {
            'authorization': f'Bearer {token}',
            'Accept-Encoding': 'gzip'
        }
        
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()  # 確認請求成功
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        raise

def create_app():
    """創建並配置 Dash 應用"""
    app = dash.Dash(__name__)
    auth = Auth(APP_ID, APP_KEY)

    app.layout = html.Div([
        html.H1('台鐵列車延誤即時資訊', className='header'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=2*60*1000,  # 每兩分鐘更新一次
            n_intervals=0
        )
    ])

    @app.callback(
        Output('live-update-graph', 'figure'),
        Input('interval-component', 'n_intervals')
    )
    def update_graph_live(n):
        try:
            # 獲取資料
            data = fetch_data(auth)
            if not data:
                raise ValueError("No data received")

            # 處理資料
            df = pd.DataFrame(data)
            
            # 處理車站名稱
            df['StationName'] = df['StationName'].apply(
                lambda x: x.get('Zh_tw') if isinstance(x, dict) else str(x)
            )
            
            # 創建圖表
            fig = px.bar(
                df,
                x='StationName',
                y='DelayTime',
                title='列車延誤時間（分鐘）',
                labels={'StationName': '車站', 'DelayTime': '延誤時間'}
            )
            
            # 自定義圖表樣式
            fig.update_layout(
                xaxis_tickangle=-45,
                margin=dict(l=50, r=50, t=50, b=50),
                height=600
            )
            
            return fig
        except Exception as e:
            print(f"Error updating graph: {e}")
            # 返回錯誤提示圖
            return go.Figure().add_annotation(
                text=f"無法更新資料: {str(e)}",
                showarrow=False,
                font=dict(size=20)
            )

    return app

if __name__ == '__main__':
    app = create_app()
    app.run_server(debug=True)