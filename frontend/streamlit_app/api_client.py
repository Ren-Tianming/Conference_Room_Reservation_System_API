from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BACKEND_BASE_URL', 'http://127.0.0.1:8000/api/v1').rstrip('/')
TIMEOUT = 10


class ApiClient:
    def __init__(self) -> None:
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    def set_tokens(self, access_token: str | None, refresh_token: str | None) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> tuple[bool, Any]:
        try:
            response = requests.request(
                method=method,
                url=f'{BASE_URL}{path}',
                json=json,
                headers=self._headers(),
                timeout=TIMEOUT,
            )
            data = response.json() if response.content else {}
            if response.ok:
                return True, data
            return False, data
        except requests.RequestException as exc:
            return False, {'detail': f'通信エラー: {exc}'}

    def register(self, username: str, password: str) -> tuple[bool, Any]:
        return self._request('POST', '/auth/register', {'username': username, 'password': password})

    def login(self, username: str, password: str) -> tuple[bool, Any]:
        return self._request('POST', '/auth/login', {'username': username, 'password': password})

    def refresh(self) -> tuple[bool, Any]:
        if not self.refresh_token:
            return False, {'detail': 'リフレッシュトークンがありません。'}
        return self._request('POST', '/auth/refresh', {'refresh_token': self.refresh_token})

    def logout(self) -> tuple[bool, Any]:
        if not self.access_token:
            return False, {'detail': 'アクセストークンがありません。'}
        return self._request(
            'POST',
            '/auth/logout',
            {'access_token': self.access_token, 'refresh_token': self.refresh_token},
        )

    def me(self) -> tuple[bool, Any]:
        return self._request('GET', '/users/me')

    def list_rooms(self) -> tuple[bool, Any]:
        return self._request('GET', '/rooms')

    def create_room(self, name: str, capacity: int, location: str, description: str | None) -> tuple[bool, Any]:
        return self._request(
            'POST',
            '/rooms',
            {
                'name': name,
                'capacity': capacity,
                'location': location,
                'description': description,
            },
        )

    def create_booking(
        self,
        room_id: int,
        title: str,
        purpose: str | None,
        attendee_count: int,
        start_time: str,
        end_time: str,
    ) -> tuple[bool, Any]:
        return self._request(
            'POST',
            '/bookings',
            {
                'room_id': room_id,
                'title': title,
                'purpose': purpose,
                'attendee_count': attendee_count,
                'start_time': start_time,
                'end_time': end_time,
            },
        )

    def list_my_bookings(self) -> tuple[bool, Any]:
        return self._request('GET', '/bookings/me')

    def cancel_booking(self, booking_id: int) -> tuple[bool, Any]:
        return self._request('DELETE', f'/bookings/{booking_id}')
