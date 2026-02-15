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

    with st.form(key='conferenceroom'):
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

    # ===============================
    # ユーザー一覧取得
    # ===============================
    url_users = 'http://127.0.0.1:8000/users'
    res = requests.get(url_users)
    users = res.json()

    users_name = {user['user_name']: user['user_id'] for user in users}
    user_id_map = {user['user_id']: user['user_name'] for user in users}

    # ===============================
    # 会議室一覧取得
    # ===============================
    url_rooms = 'http://127.0.0.1:8000/conferencerooms'
    res = requests.get(url_rooms)
    conferencerooms = res.json()

    conferencerooms_name = {
        room['conferenceroom_name']: {
            'conferenceroom_id': room['conferenceroom_id'],
            'conferenceroom_capacity': room['conferenceroom_capacity']
        }
        for room in conferencerooms
    }

    room_id_map = {
        room['conferenceroom_id']: {
            'name': room['conferenceroom_name'],
            'capacity': room['conferenceroom_capacity']
        }
        for room in conferencerooms
    }

    # ===============================
    # 会議室一覧表示
    # ===============================
    st.write('### 会議室一覧')
    df_rooms = pd.DataFrame(conferencerooms)

    if not df_rooms.empty:
        df_rooms.columns = ['会議室ID', '会議室名', '会議室定員']
        st.table(df_rooms)
    else:
        st.info("会議室は登録されていません")

    # ===============================
    # 予約一覧取得
    # ===============================
    url_bookings = 'http://127.0.0.1:8000/bookings'
    res = requests.get(url_bookings)
    bookings = res.json()

    st.write('### 予約一覧')

    if not bookings:
        st.info("現在予約はありません")
    else:
        df_bookings = pd.DataFrame(bookings)

        df_bookings['user_id'] = df_bookings['user_id'].map(
            lambda x: user_id_map.get(x, "不明")
        )
        df_bookings['conferenceroom_id'] = df_bookings['conferenceroom_id'].map(
            lambda x: room_id_map.get(x, {}).get('name', "不明")
        )
        df_bookings['start_datetime'] = df_bookings['start_datetime'].map(
            lambda x: datetime.datetime.fromisoformat(x).strftime('%Y/%m/%d %H:%M')
        )
        df_bookings['end_datetime'] = df_bookings['end_datetime'].map(
            lambda x: datetime.datetime.fromisoformat(x).strftime('%Y/%m/%d %H:%M')
        )

        df_bookings = df_bookings.rename(
            columns={
                'booking_id': '予約番号',
                'user_id': '予約者名',
                'conferenceroom_id': '会議室名',
                'booking_capacity': '予約人数',
                'start_datetime': '開始時刻',
                'end_datetime': '終了時刻'
            }
        )

        st.table(df_bookings)

    # ===============================
    # 予約削除
    # ===============================
    st.write('---')
    st.write('### 予約削除')

    if bookings:
        booking_options = {
            f"{b['booking_id']} | {user_id_map.get(b['user_id'])} | {room_id_map.get(b['conferenceroom_id'], {}).get('name')}":
            b['booking_id']
            for b in bookings
        }

        with st.form(key='delete_booking'):
            selected_label = st.selectbox('削除する予約を選択', booking_options.keys())
            delete_button = st.form_submit_button('予約削除')

        if delete_button:
            delete_id = booking_options[selected_label]
            delete_url = f'http://127.0.0.1:8000/bookings/{delete_id}'

            try:
                res = requests.delete(delete_url)
            except requests.exceptions.ConnectionError:
                st.error("APIサーバーに接続できません")
            else:
                if res.status_code == 200:
                    st.success("予約を削除しました")
                    st.rerun()
                else:
                    st.error("削除に失敗しました")
                    st.json(res.json())
    else:
        st.info("削除できる予約はありません")

    # ===============================
    # 予約登録フォーム（常に表示）
    # ===============================
    st.write('---')
    st.write('### 予約登録')

    if not users_name or not conferencerooms_name:
        st.warning("ユーザーまたは会議室を先に登録してください")
    else:
        with st.form(key='booking'):
            user_name = st.selectbox('予約者名', users_name.keys())
            room_name = st.selectbox('会議室名', conferencerooms_name.keys())
            booking_capacity = st.number_input('予約人数', min_value=1, step=1)

            start_date = st.date_input(
                '予約日付',
                min_value=datetime.date.today()
            )
            start_time = st.time_input(
                '開始時刻',
                value=datetime.time(hour=9)
            )
            end_time = st.time_input(
                '終了時刻',
                value=datetime.time(hour=22)
            )

            submit_button = st.form_submit_button('予約登録')

        if submit_button:
            room_info = conferencerooms_name[room_name]

            if booking_capacity > room_info['conferenceroom_capacity']:
                st.error("定員を超えています")
            elif start_time >= end_time:
                st.error("開始時刻が終了時刻を超えています")
            elif start_time < datetime.time(9, 0) or end_time > datetime.time(22, 0):
                st.error("利用時間は 9:00 ~ 22:00 です")
            else:
                data = {
                    'user_id': users_name[user_name],
                    'conferenceroom_id': room_info['conferenceroom_id'],
                    'booking_capacity': booking_capacity,
                    'start_datetime': datetime.datetime.combine(start_date, start_time).isoformat(),
                    'end_datetime': datetime.datetime.combine(start_date, end_time).isoformat()
                }

                try:
                    res = requests.post(
                        'http://127.0.0.1:8000/bookings',
                        json=data
                    )
                except requests.exceptions.ConnectionError:
                    st.error("APIサーバーに接続できません")
                else:
                    if res.status_code == 200:
                        st.success("予約完了しました")
                        st.rerun()
                    else:
                        st.error("予約に失敗しました")
                        st.json(res.json())
