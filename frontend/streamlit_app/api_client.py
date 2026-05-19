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

    def _decode_response(self, response: requests.Response) -> Any:
        if not response.content:
            return {}
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            return response.json()
        return {'detail': response.text or response.reason}

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        *,
        retry_on_unauthorized: bool = True,
    ) -> tuple[bool, Any]:
        try:
            response = requests.request(
                method=method,
                url=f'{BASE_URL}{path}',
                json=json,
                headers=self._headers(),
                timeout=TIMEOUT,
            )
            data = self._decode_response(response)
            if response.ok:
                return True, data
            if response.status_code == 401 and retry_on_unauthorized and path != '/auth/refresh':
                refreshed, token_data = self.refresh()
                if refreshed:
                    self.access_token = token_data.get('access_token')
                    self.refresh_token = token_data.get('refresh_token')
                    return self._request(method, path, json, retry_on_unauthorized=False)
            return False, data
        except ValueError as exc:
            return False, {'detail': f'レスポンス解析エラー: {exc}'}
        except requests.RequestException as exc:
            return False, {'detail': f'通信エラー: {exc}'}

    def register(self, username: str, password: str) -> tuple[bool, Any]:
        return self._request('POST', '/auth/register', {'username': username, 'password': password})

    def login(self, username: str, password: str) -> tuple[bool, Any]:
        return self._request('POST', '/auth/login', {'username': username, 'password': password})

    def refresh(self) -> tuple[bool, Any]:
        if not self.refresh_token:
            return False, {'detail': 'リフレッシュトークンがありません。'}
        return self._request('POST', '/auth/refresh', {'refresh_token': self.refresh_token}, retry_on_unauthorized=False)

    def logout(self) -> tuple[bool, Any]:
        if not self.access_token:
            return False, {'detail': 'アクセストークンがありません。'}
        return self._request(
            'POST',
            '/auth/logout',
            {'access_token': self.access_token, 'refresh_token': self.refresh_token},
            retry_on_unauthorized=False,
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
