from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import pandas as pd
import streamlit as st

from api_client import ApiError, MeetingRoomApiClient

st.set_page_config(
    page_title="会議室予約システム フロントエンド",
    page_icon="🏢",
    layout="wide",
)

DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1"


# ---------- session state ----------
def ensure_state() -> None:
    defaults = {
        "api_base_url": DEFAULT_API_BASE_URL,
        "access_token": None,
        "refresh_token": None,
        "user": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def build_client() -> MeetingRoomApiClient:
    return MeetingRoomApiClient(st.session_state.api_base_url)


# ---------- auth helpers ----------
def save_auth_payload(payload: dict[str, Any]) -> None:
    st.session_state.access_token = payload.get("access_token")
    st.session_state.refresh_token = payload.get("refresh_token")
    st.session_state.user = payload.get("user")



def clear_auth_state() -> None:
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user = None



def is_logged_in() -> bool:
    return bool(st.session_state.access_token and st.session_state.user)



def current_user_role() -> str | None:
    user = st.session_state.user or {}
    return user.get("role")


# ---------- ui helpers ----------
def render_sidebar(client: MeetingRoomApiClient) -> None:
    with st.sidebar:
        st.title("⚙️ システム設定")
        api_url = st.text_input("バックエンド API Base URL", value=st.session_state.api_base_url)
        st.caption("デフォルト例：http://localhost:8000/api/v1")
        st.session_state.api_base_url = api_url.rstrip("/")

        st.divider()
        st.subheader("サービス状態")
        if st.button("バックエンド接続確認", use_container_width=True):
            try:
                result = client.health()
                st.success(f"バックエンド接続成功: {result}")
            except Exception as exc:
                st.error(f"接続に失敗しました: {exc}")

        st.divider()
        st.subheader("ログイン状態")
        if is_logged_in():
            user = st.session_state.user or {}
            st.success(f"ログイン中: {user.get('username')}")
            st.write(f"メールアドレス: {user.get('email')}")
            st.write(f"ロール: {user.get('role')}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("トークン更新", use_container_width=True):
                    refresh_token_action(client)
            with col2:
                if st.button("ログアウト", use_container_width=True):
                    logout_action(client)
        else:
            st.info("現在ログインしていません")



def refresh_token_action(client: MeetingRoomApiClient) -> None:
    refresh_token = st.session_state.refresh_token
    if not refresh_token:
        st.warning("現在 refresh token がありません")
        return
    try:
        payload = client.refresh_token(refresh_token)
        save_auth_payload(payload)
        st.success("トークンを更新しました")
    except ApiError as exc:
        st.error(exc.message)
        if exc.status_code == 401:
            clear_auth_state()



def logout_action(client: MeetingRoomApiClient) -> None:
    access_token = st.session_state.access_token
    refresh_token = st.session_state.refresh_token
    try:
        if access_token:
            client.logout(access_token, refresh_token)
    except Exception:
        pass
    finally:
        clear_auth_state()
        st.success("ログアウトしました")



def require_login() -> bool:
    if not is_logged_in():
        st.warning("業務機能を利用する前にログインしてください。")
        return False
    return True



def try_sync_me(client: MeetingRoomApiClient) -> None:
    if not st.session_state.access_token:
        return
    try:
        user = client.me(st.session_state.access_token)
        st.session_state.user = user
    except ApiError:
        pass


# ---------- sections ----------
def auth_section(client: MeetingRoomApiClient) -> None:
    st.subheader("ユーザー認証")
    login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("ユーザー名", key="login_username")
            password = st.text_input("パスワード", type="password", key="login_password")
            submitted = st.form_submit_button("ログイン", use_container_width=True)
            if submitted:
                try:
                    payload = client.login(username=username, password=password)
                    save_auth_payload(payload)
                    st.success("ログインに成功しました")
                except ApiError as exc:
                    st.error(exc.message)

    with register_tab:
        with st.form("register_form"):
            username = st.text_input("新しいユーザー名", key="register_username")
            email = st.text_input("メールアドレス", key="register_email")
            password = st.text_input("パスワード（8文字以上）", type="password", key="register_password")
            submitted = st.form_submit_button("登録してログイン", use_container_width=True)
            if submitted:
                try:
                    payload = client.register(username=username, email=email, password=password)
                    save_auth_payload(payload)
                    st.success("登録が完了し、自動でログインしました")
                except ApiError as exc:
                    st.error(exc.message)



def overview_section(client: MeetingRoomApiClient) -> None:
    st.subheader("システム概要")
    if not require_login():
        return

    user = st.session_state.user or {}
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("現在のユーザー", user.get("username", "-"))
    with col2:
        st.metric("ロール", user.get("role", "-"))
    with col3:
        st.metric("API", st.session_state.api_base_url)

    st.info(
        "この Streamlit フロントエンドでは、ユーザー登録・ログイン・会議室一覧・日別スケジュール確認・予約作成・自分の予約確認・予約キャンセル・管理者向け会議室管理を利用できます。"
    )

    try:
        rooms = client.list_rooms(st.session_state.access_token)
        bookings = client.list_my_bookings(st.session_state.access_token)
        left, right = st.columns(2)
        with left:
            st.metric("利用可能な会議室数", len(rooms))
        with right:
            st.metric("自分の予約件数", len(bookings))
    except ApiError as exc:
        st.error(exc.message)



def rooms_section(client: MeetingRoomApiClient) -> None:
    st.subheader("会議室一覧")
    if not require_login():
        return

    include_inactive = st.toggle("無効化された会議室も表示する", value=False)
    try:
        rooms = client.list_rooms(st.session_state.access_token, include_inactive=include_inactive)
    except ApiError as exc:
        st.error(exc.message)
        return

    if not rooms:
        st.info("現在、会議室データがありません。")
        return

    df = pd.DataFrame(rooms)
    st.dataframe(df, use_container_width=True, hide_index=True)

    room_options = {f"#{room['id']} - {room['name']}": room for room in rooms}
    selected_label = st.selectbox("会議室を選択して当日のスケジュールを確認", list(room_options.keys()))
    selected_room = room_options[selected_label]
    selected_day = st.date_input("対象日", value=date.today())

    try:
        schedule = client.get_room_schedule(
            st.session_state.access_token,
            room_id=selected_room["id"],
            day=selected_day.isoformat(),
        )
    except ApiError as exc:
        st.error(exc.message)
        return

    bookings = schedule.get("bookings", [])
    if bookings:
        schedule_df = pd.DataFrame(bookings)
        st.dataframe(schedule_df, use_container_width=True, hide_index=True)
    else:
        st.success("この日は予約がありません")



def booking_section(client: MeetingRoomApiClient) -> None:
    st.subheader("予約作成")
    if not require_login():
        return

    try:
        rooms = client.list_rooms(st.session_state.access_token)
    except ApiError as exc:
        st.error(exc.message)
        return

    if not rooms:
        st.warning("現在、予約可能な会議室がありません。")
        return

    room_options = {f"#{room['id']} - {room['name']}（定員 {room['capacity']}）": room for room in rooms}

    with st.form("create_booking_form"):
        room_label = st.selectbox("会議室", list(room_options.keys()))
        title = st.text_input("会議タイトル")
        description = st.text_area("会議説明", height=100)
        attendee_count = st.number_input("参加人数", min_value=1, step=1, value=1)

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日", value=date.today(), key="start_date")
            start_clock = st.time_input("開始時刻", value=time(9, 0), key="start_clock")
        with col2:
            end_date = st.date_input("終了日", value=date.today(), key="end_date")
            end_clock = st.time_input("終了時刻", value=time(10, 0), key="end_clock")

        submitted = st.form_submit_button("予約を登録", use_container_width=True)
        if submitted:
            start_dt = datetime.combine(start_date, start_clock)
            end_dt = datetime.combine(end_date, end_clock)
            try:
                created = client.create_booking(
                    st.session_state.access_token,
                    room_id=room_options[room_label]["id"],
                    title=title,
                    description=description,
                    attendee_count=int(attendee_count),
                    start_time=start_dt.isoformat(),
                    end_time=end_dt.isoformat(),
                )
                st.success(f"予約が完了しました。予約ID: {created['id']}")
                st.json(created)
            except ApiError as exc:
                st.error(exc.message)



def my_bookings_section(client: MeetingRoomApiClient) -> None:
    st.subheader("自分の予約")
    if not require_login():
        return

    status_filter = st.selectbox("状態で絞り込み", ["すべて", "confirmed", "cancelled"])
    status_value = None if status_filter == "すべて" else status_filter

    try:
        bookings = client.list_my_bookings(st.session_state.access_token, status_filter=status_value)
    except ApiError as exc:
        st.error(exc.message)
        return

    if not bookings:
        st.info("予約履歴がありません。")
        return

    df = pd.DataFrame(bookings)
    st.dataframe(df, use_container_width=True, hide_index=True)

    confirmed_bookings = [item for item in bookings if item.get("status") == "confirmed"]
    if confirmed_bookings:
        options = {f"#{item['id']} - {item['title']}": item for item in confirmed_bookings}
        label = st.selectbox("キャンセルする予約を選択", list(options.keys()))
        if st.button("予約をキャンセル", type="primary"):
            try:
                result = client.cancel_booking(st.session_state.access_token, options[label]["id"])
                st.success(result.get("message", "予約をキャンセルしました"))
            except ApiError as exc:
                st.error(exc.message)
    else:
        st.caption("現在、キャンセル可能な confirmed 状態の予約はありません。")



def admin_section(client: MeetingRoomApiClient) -> None:
    st.subheader("管理者: 会議室管理")
    if not require_login():
        return

    if current_user_role() != "admin":
        st.info("現在のアカウントは管理者ではないため、会議室管理機能は利用できません。")
        return

    create_tab, update_tab = st.tabs(["会議室を新規作成", "会議室を編集"])

    with create_tab:
        with st.form("create_room_form"):
            name = st.text_input("会議室名")
            location = st.text_input("場所")
            capacity = st.number_input("定員", min_value=1, value=6, step=1)
            submitted = st.form_submit_button("会議室を作成", use_container_width=True)
            if submitted:
                try:
                    room = client.create_room(
                        st.session_state.access_token,
                        name=name,
                        location=location,
                        capacity=int(capacity),
                    )
                    st.success(f"作成に成功しました: {room['name']}")
                    st.json(room)
                except ApiError as exc:
                    st.error(exc.message)

    with update_tab:
        try:
            rooms = client.list_rooms(st.session_state.access_token, include_inactive=True)
        except ApiError as exc:
            st.error(exc.message)
            return

        if not rooms:
            st.info("会議室がありません")
            return

        options = {f"#{room['id']} - {room['name']}": room for room in rooms}
        label = st.selectbox("会議室を選択", list(options.keys()), key="admin_room_select")
        room = options[label]

        with st.form("update_room_form"):
            name = st.text_input("会議室名", value=room.get("name", ""))
            location = st.text_input("場所", value=room.get("location") or "")
            capacity = st.number_input("定員", min_value=1, value=int(room.get("capacity", 1)), step=1)
            is_active = st.checkbox("有効状態", value=bool(room.get("is_active", True)))
            submitted = st.form_submit_button("変更を保存", use_container_width=True)
            if submitted:
                try:
                    payload = {
                        "name": name,
                        "location": location,
                        "capacity": int(capacity),
                        "is_active": is_active,
                    }
                    updated = client.update_room(st.session_state.access_token, room["id"], payload)
                    st.success("会議室情報を更新しました")
                    st.json(updated)
                except ApiError as exc:
                    st.error(exc.message)


# ---------- main ----------
def main() -> None:
    ensure_state()
    client = build_client()
    try_sync_me(client)

    st.title("🏢 会議室予約システム · Streamlit フロントエンド")
    st.caption("FastAPI 企業向け V2 バックエンドと連携するデモ用フロントエンドです")

    render_sidebar(client)

    section_auth, section_overview, section_rooms, section_booking, section_my, section_admin = st.tabs(
        ["認証", "概要", "会議室", "予約作成", "自分の予約", "管理者"]
    )

    with section_auth:
        auth_section(client)
    with section_overview:
        overview_section(client)
    with section_rooms:
        rooms_section(client)
    with section_booking:
        booking_section(client)
    with section_my:
        my_bookings_section(client)
    with section_admin:
        admin_section(client)


if __name__ == "__main__":
    main()
