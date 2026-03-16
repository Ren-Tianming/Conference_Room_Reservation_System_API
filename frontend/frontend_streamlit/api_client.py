from __future__ import annotations

from typing import Any

import requests


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MeetingRoomApiClient:
    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _headers(self, access_token: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    def _handle_response(self, response: requests.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.ok:
            return payload

        detail = None
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("message")
        if isinstance(detail, list):
            detail = "; ".join(
                item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                for item in detail
            )
        raise ApiError(detail or f"リクエストに失敗しました（HTTP {response.status_code}）", response.status_code)

    def health(self) -> dict[str, Any]:
        response = requests.get(self._build_url("/health"), timeout=self.timeout)
        return self._handle_response(response)

    def register(self, username: str, email: str, password: str) -> dict[str, Any]:
        response = requests.post(
            self._build_url("/auth/register"),
            json={"username": username, "email": email, "password": password},
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def login(self, username: str, password: str) -> dict[str, Any]:
        response = requests.post(
            self._build_url("/auth/login"),
            data={"username": username, "password": password},
            headers={"Accept": "application/json"},
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        response = requests.post(
            self._build_url("/auth/refresh"),
            json={"refresh_token": refresh_token},
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def logout(self, access_token: str, refresh_token: str | None = None) -> dict[str, Any]:
        response = requests.post(
            self._build_url("/auth/logout"),
            json={"access_token": access_token, "refresh_token": refresh_token},
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def me(self, access_token: str) -> dict[str, Any]:
        response = requests.get(
            self._build_url("/auth/me"),
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def list_rooms(self, access_token: str, include_inactive: bool = False) -> list[dict[str, Any]]:
        response = requests.get(
            self._build_url("/rooms"),
            params={"include_inactive": str(include_inactive).lower()},
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def create_room(
        self,
        access_token: str,
        *,
        name: str,
        location: str | None,
        capacity: int,
    ) -> dict[str, Any]:
        response = requests.post(
            self._build_url("/rooms"),
            json={"name": name, "location": location or None, "capacity": capacity},
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def update_room(
        self,
        access_token: str,
        room_id: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = requests.patch(
            self._build_url(f"/rooms/{room_id}"),
            json=payload,
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get_room_schedule(self, access_token: str, room_id: int, day: str) -> dict[str, Any]:
        response = requests.get(
            self._build_url(f"/rooms/{room_id}/schedule"),
            params={"day": day},
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def list_my_bookings(self, access_token: str, status_filter: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if status_filter:
            params["status"] = status_filter
        response = requests.get(
            self._build_url("/bookings/me"),
            params=params,
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def create_booking(
        self,
        access_token: str,
        *,
        room_id: int,
        title: str,
        description: str | None,
        attendee_count: int,
        start_time: str,
        end_time: str,
    ) -> dict[str, Any]:
        response = requests.post(
            self._build_url("/bookings"),
            json={
                "room_id": room_id,
                "title": title,
                "description": description or None,
                "attendee_count": attendee_count,
                "start_time": start_time,
                "end_time": end_time,
            },
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def cancel_booking(self, access_token: str, booking_id: int) -> dict[str, Any]:
        response = requests.delete(
            self._build_url(f"/bookings/{booking_id}"),
            headers=self._headers(access_token),
            timeout=self.timeout,
        )
        return self._handle_response(response)
