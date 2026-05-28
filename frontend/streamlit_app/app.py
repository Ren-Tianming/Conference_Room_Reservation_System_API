from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from api_client import ApiClient

st.set_page_config(page_title='会議室予約システム', page_icon='📅', layout='wide')

if 'client' not in st.session_state:
    st.session_state.client = ApiClient()
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = None

client: ApiClient = st.session_state.client
client.set_tokens(st.session_state.access_token, st.session_state.refresh_token)


def sync_tokens_from_client(access_token: str | None, refresh_token: str | None) -> None:
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token


client.set_token_update_callback(sync_tokens_from_client)


def save_tokens(data: dict) -> None:
    st.session_state.access_token = data.get('access_token')
    st.session_state.refresh_token = data.get('refresh_token')
    client.set_tokens(st.session_state.access_token, st.session_state.refresh_token)


def clear_tokens() -> None:
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    client.set_tokens(None, None)


def show_result(success: bool, data: dict | list | str) -> None:
    if success:
        st.success('操作が成功しました。')
        st.write(data)
    else:
        detail = data.get('detail') if isinstance(data, dict) else data
        st.error(f'操作に失敗しました: {detail}')


st.title('📅 会議室予約システム')
st.caption('FastAPI + MySQL + Redis + Streamlit')

with st.sidebar:
    st.subheader('認証')
    if st.session_state.access_token:
        st.success('ログイン中')
        if st.button('ログアウト'):
            ok, data = client.logout()
            if ok:
                clear_tokens()
                st.success('ログアウトしました。')
                st.rerun()
            else:
                st.warning(data.get('detail', 'ログアウト API 呼び出しに失敗しました。ローカル状態をクリアします。'))
                clear_tokens()
                st.rerun()
    else:
        st.info('未ログイン')

login_tab, register_tab = st.tabs(['ログイン', 'ユーザー登録'])

with login_tab:
    with st.form('login_form'):
        username = st.text_input('ユーザー名', key='login_username')
        password = st.text_input('パスワード', type='password', key='login_password')
        submitted = st.form_submit_button('ログイン')
        if submitted:
            ok, data = client.login(username, password)
            if ok:
                save_tokens(data)
                st.success('ログインしました。')
                st.rerun()
            else:
                st.error(data.get('detail', 'ログインに失敗しました。'))

with register_tab:
    with st.form('register_form'):
        username = st.text_input('新規ユーザー名', key='register_username')
        password = st.text_input('新規パスワード', type='password', key='register_password')
        submitted = st.form_submit_button('登録')
        if submitted:
            ok, data = client.register(username, password)
            show_result(ok, data)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader('自分の情報')
    if st.button('取得する'):
        ok, data = client.me()
        show_result(ok, data)

    st.subheader('会議室追加（管理者のみ）')
    with st.form('create_room_form'):
        room_name = st.text_input('会議室名')
        capacity = st.number_input('定員', min_value=1, max_value=500, value=6)
        location = st.text_input('場所', value='東京本社')
        description = st.text_area('説明', value='')
        submitted_room = st.form_submit_button('会議室を追加')
        if submitted_room:
            ok, data = client.create_room(room_name, int(capacity), location, description or None)
            show_result(ok, data)

with col2:
    st.subheader('会議室一覧')
    if st.button('会議室を読み込む'):
        ok, data = client.list_rooms()
        if ok:
            st.dataframe(data, use_container_width=True)
        else:
            st.error(data.get('detail', '会議室一覧の取得に失敗しました。'))

st.divider()

st.subheader('予約作成')
with st.form('create_booking_form'):
    room_id = st.number_input('会議室 ID（一覧から選択した ID）', min_value=1, step=1, value=1)
    title = st.text_input('予約タイトル', value='定例ミーティング')
    purpose = st.text_input('利用目的', value='進捗確認')
    attendee_count = st.number_input('参加人数', min_value=1, max_value=500, value=2)

    default_start = datetime.combine(date.today() + timedelta(days=1), time(hour=10, minute=0))
    default_end = datetime.combine(date.today() + timedelta(days=1), time(hour=11, minute=0))

    start_date = st.date_input('開始日', value=default_start.date())
    start_clock = st.time_input('開始時刻', value=default_start.time())
    end_date = st.date_input('終了日', value=default_end.date())
    end_clock = st.time_input('終了時刻', value=default_end.time())

    submitted_booking = st.form_submit_button('予約する')
    if submitted_booking:
        app_timezone = ZoneInfo('Asia/Tokyo')
        start_dt = datetime.combine(start_date, start_clock, tzinfo=app_timezone).isoformat()
        end_dt = datetime.combine(end_date, end_clock, tzinfo=app_timezone).isoformat()
        ok, data = client.create_booking(
            room_id=int(room_id),
            title=title,
            purpose=purpose or None,
            attendee_count=int(attendee_count),
            start_time=start_dt,
            end_time=end_dt,
        )
        show_result(ok, data)

st.divider()

st.subheader('自分の予約一覧')
if st.button('予約一覧を取得'):
    ok, data = client.list_my_bookings()
    if ok:
        st.dataframe(data, use_container_width=True)
    else:
        st.error(data.get('detail', '予約一覧の取得に失敗しました。'))

st.subheader('予約キャンセル')
with st.form('cancel_booking_form'):
    booking_id = st.number_input('キャンセルする予約 ID', min_value=1, step=1, value=1)
    submitted_cancel = st.form_submit_button('予約をキャンセル')
    if submitted_cancel:
        ok, data = client.cancel_booking(int(booking_id))
        show_result(ok, data)
