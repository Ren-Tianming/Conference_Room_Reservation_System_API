import streamlit as st
import random
import datetime
import requests
import json

page = st.sidebar.selectbox('ページを選択してください:',['ユーザ情報入力','会議室情報入力','予約情報入力'])

if page == 'ユーザ情報入力':
    st.title('APIテスト画面(ユーザ情報入力)')

    with st.form(key='user'):
        user_id: int = random.randint(0,10)
        user_name: str = st.text_input('ユーザー名', max_chars=64)
        data = {
            'user_id': user_id,
            'user_name': user_name
        }
        submit_button = st.form_submit_button(label='リクエスト送信')

    if submit_button:
        st.write('## 送信データ')
        st.json(data)
        st.write('## レスポンス結果')
        url = 'http://127.0.0.1:8000/users'
        res = requests.post(
            url,
            data=json.dumps(data)
        )
        st.json(res.json())

elif page == '会議室情報入力':

    st.title('APIテスト画面(会議室情報入力)')

    with st.form(key='room'):
        conferenceroom_id: int = random.randint(0,10)
        conferenceroom_name: str = st.text_input('会議室名', max_chars=32)
        conferenceroom_capacity: int = st.number_input('定員', step=1)
        data = {
            'conferenceroom_id': conferenceroom_id,
            'conferenceroom_name': conferenceroom_name,
            'conferenceroom_capacity': conferenceroom_capacity
        }
        submit_button = st.form_submit_button(label='リクエスト送信')

    if submit_button:
        st.write('## 送信データ')
        st.json(data)
        st.write('## レスポンス結果')
        url = 'http://127.0.0.1:8000/conferencerooms'
        res = requests.post(
            url,
            data=json.dumps(data)
        )
        st.json(res.json())

elif page == '予約情報入力':

    st.title('APIテスト画面(予約情報入力)')

    with st.form(key='booking'):
        booking_id: int = random.randint(0,10)
        user_id: int = random.randint(0,10)
        conferenceroom_id: int = random.randint(0,10)
        booking_capacity: int = st.number_input('予約人数', step=1)
        start_date = st.date_input('会議室の予約日付を入力してください:',min_value=datetime.date.today())
        start_time = st.time_input('会議室の予約開始時刻を入力してください:',value=datetime.time(hour=9,minute=0))
        end_time = st.time_input('会議室の予約終了時刻を入力してください:',value=datetime.time(hour=22,minute=0))

        data = {
            'booking_id': booking_id,
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
        submit_button = st.form_submit_button(label='リクエスト送信')

    if submit_button:
        st.write('## 送信データ')
        st.json(data)
        st.write('## レスポンス結果')
        url = 'http://127.0.0.1:8000/bookings'
        res = requests.post(
            url,
            data=json.dumps(data)
        )
        st.json(res.json())