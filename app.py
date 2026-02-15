import streamlit as st
import datetime
import requests
import json
import pandas as pd

page = st.sidebar.selectbox('ページを選択してください:',['ユーザー登録画面','会議室登録画面','予約登録画面'])

if page == 'ユーザー登録画面':

    st.title('ユーザー登録画面')

    with st.form(key='user'):
        user_name: str = st.text_input('ユーザー名', max_chars=64)
        data = {
            'user_name': user_name
        }
        submit_button = st.form_submit_button(label='ユーザー登録')

    if submit_button:
        st.write('## レスポンス結果')
        url = 'http://127.0.0.1:8000/users'
        try:
            res = requests.post(
                url,
                json=data
            )
        except requests.exceptions.ConnectionError:
            st.error("APIサーバーに接続できません")

        if res.status_code == 200 :
            st.success('ユーザ登録完了')
        st.write(res.status_code)
        st.json(res.json())

elif page == '会議室登録画面':

    st.title('会議室登録画面')

    with st.form(key = 'conferenceroom'):
        conferenceroom_name: str = st.text_input('会議室名', max_chars=32)
        conferenceroom_capacity: int = st.number_input('定員', step=1)
        data = {
            'conferenceroom_name': conferenceroom_name,
            'conferenceroom_capacity': conferenceroom_capacity
        }
        submit_button = st.form_submit_button(label='会議室登録')

    if submit_button:
        st.write('## レスポンス結果')
        url = 'http://127.0.0.1:8000/conferencerooms'
        try:
            res = requests.post(
                url,
                json=data
            )
        except requests.exceptions.ConnectionError:
            st.error("APIサーバーに接続できません")

        if res.status_code == 200 :
            st.success('会議室登録完了')
        st.write(res.status_code)
        st.json(res.json())

elif page == '予約登録画面':

    st.title('予約登録画面')
    # ユーザー一覧取得
    url_users = 'http://127.0.0.1:8000/users'
    res = requests.get(url_users)
    users = res.json()

    # ユーザー名はキー、ユーザーIDはバリュー
    users_name = {}
    for user in users:
        users_name[user['user_name']] = user['user_id']

    # 会議室一覧取得
    url_conferencerooms = 'http://127.0.0.1:8000/conferencerooms'
    res = requests.get(url_conferencerooms)
    conferencerooms = res.json()

    conferencerooms_name = {}
    for conferenceroom in conferencerooms:
        conferencerooms_name[conferenceroom['conferenceroom_name']] = {
            'conferenceroom_id': conferenceroom['conferenceroom_id'],
            'conferenceroom_capacity': conferenceroom['conferenceroom_capacity']
        }
    
    st.write('### 会議室一覧')
    df_conferencerooms = pd.DataFrame(conferencerooms)
    df_conferencerooms.columns = ['会議室ID', '会議室名', '会議室定員']
    st.table(df_conferencerooms)

    # 予約一覧取得
    url_bookings = 'http://127.0.0.1:8000/bookings'
    res = requests.get(url_bookings)
    bookings = res.json()

    st.write('### 予約一覧')
    df_bookings = pd.DataFrame(bookings)

    user_id = {}
    for user in users:
        user_id[user['user_id']] = user['user_name']
    
    conferenceroom_id = {}
    for conferenceroom in conferencerooms:
        conferenceroom_id[conferenceroom['conferenceroom_id']] = {
            'conferenceroom_name': conferenceroom['conferenceroom_name'],
            'conferenceroom_capacity': conferenceroom['conferenceroom_capacity']
            }
    
    # IDを各値に変換
    to_user_name = lambda x: user_id[x]
    to_conferenceroom_name = lambda x: conferenceroom_id[x]['conferenceroom_name']
    to_datetime = lambda x: datetime.datetime.fromisoformat(x).strftime('%Y/%m/%d %H:%M')

    # 特定の列に適用
    df_bookings['user_id'] = df_bookings['user_id'].map(to_user_name)
    df_bookings['conferenceroom_id'] = df_bookings['conferenceroom_id'].map(to_conferenceroom_name)
    df_bookings['start_datetime'] = df_bookings['start_datetime'].map(to_datetime)
    df_bookings['end_datetime'] = df_bookings['end_datetime'].map(to_datetime)

    df_bookings = df_bookings.rename(
        columns={
            'user_id': '予約者名',
            'conferenceroom_id': '会議室名',
            'booking_capacity': '予約人数',
            'start_datetime': '開始時刻',
            'end_datetime': '終了時刻',
            'booking_id': '予約番号'
        }
    )
    st.table(df_bookings)

    with st.form(key='booking'):
        user_name: str = st.selectbox('予約者名', users_name.keys())
        conferenceroom_name: str = st.selectbox('会議室名', conferencerooms_name.keys())
        booking_capacity: int = st.number_input('予約人数', step=1, min_value=1)
        start_date = st.date_input('会議室の予約日付を入力してください:',min_value=datetime.date.today())
        start_time = st.time_input('会議室の予約開始時刻を入力してください:',value=datetime.time(hour=9,minute=0))
        end_time = st.time_input('会議室の予約終了時刻を入力してください:',value=datetime.time(hour=22,minute=0))

        submit_button = st.form_submit_button(label='予約登録')

    if submit_button:
        user_id = users_name[user_name]
        conferenceroom_id = conferencerooms_name[conferenceroom_name]['conferenceroom_id']
        conferenceroom_capacity = conferencerooms_name[conferenceroom_name]['conferenceroom_capacity']
        data = {
            'user_id': user_id,
            'conferenceroom_id': conferenceroom_id,
            'booking_capacity': booking_capacity,
            'start_datetime': datetime.datetime(
                year=start_date.year,
                month=start_date.month,
                day=start_date.day,
                hour=start_time.hour,
                minute=start_time.minute
            ).isoformat(),
            'end_datetime':datetime.datetime(
                year=start_date.year,
                month=start_date.month,
                day=start_date.day,
                hour=end_time.hour,
                minute=end_time.minute
            ).isoformat()
        }

        # 定員より多い予約人数の場合
        if booking_capacity > conferenceroom_capacity:
            st.error(f'{conferenceroom_name}の定員は、{conferenceroom_capacity}名です。{conferenceroom_capacity}名以下の予約人数のみ受け付けております。')
        
        elif start_time >= end_time:
            st.error('開始時刻が終了時刻を超えています。')
        
        elif start_time < datetime.time(hour = 9, minute = 0, second = 0) or end_time > datetime.time(hour = 22, minute = 0, second = 0):
            st.error('利用時間は9:00 ~ 22:00になります。')

        else:
            # 会議室の予約を行う
            url = 'http://127.0.0.1:8000/bookings'
            try:
                res = requests.post(
                    url,
                    json=data
                )
            except requests.exceptions.ConnectionError:
                st.error("APIサーバーに接続できません")
                
            if res.status_code == 200: 
                st.success('予約完了しました！')
            elif res.status_code == 409 and res.json()['detail'] == "Already booked": 
                st.error('指定の時間には既に予約が入っています。')
            
            st.json(res.json())
