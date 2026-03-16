# Backend

このディレクトリには、会議室予約システムのバックエンド API が含まれています。  
FastAPI を中心に、ユーザー認証、会議室管理、予約管理、Redis キャッシュ、予約競合防止の機能を提供します。

## 使用技術

- FastAPI
- SQLAlchemy 2.x
- PostgreSQL / SQLite
- Redis
- Pydantic v2
- Passlib (bcrypt)
- python-jose
- Alembic
- pytest

## ディレクトリ構成

```text
backend/
├─ README.md
├─ Dockerfile
├─ requirements.txt
├─ .env.example
├─ alembic.ini
├─ alembic/
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions/
├─ tests/
│  └─ test_health.py
└─ app/
   ├─ main.py
   ├─ api/
   ├─ core/
   ├─ db/
   ├─ models/
   ├─ schemas/
   └─ services/
```

## 主な機能

- ユーザー登録
- ログイン / ログアウト
- JWT アクセストークン発行
- リフレッシュトークン発行
- トークン再発行
- 自分のユーザー情報取得
- 会議室一覧取得 / 会議室登録
- 予約作成 / 自分の予約一覧 / 予約キャンセル
- 予約競合チェック
- Redis キャッシュ
- Redis ロックによる簡易排他制御
- Health / Ready エンドポイント

## セットアップ

### 1. 環境変数ファイル作成

```bash
cp .env.example .env
```

### 2. 仮想環境作成

```bash
python -m venv .venv
```

### 3. 仮想環境有効化

#### Windows

```bash
.venv\Scriptsctivate
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

### 4. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 5. アプリ起動

```bash
uvicorn app.main:app --reload
```

## `.env.example` の内容

```env
APP_NAME=Conference Room Reservation System API
ENV=dev
DEBUG=true
API_V1_PREFIX=/api/v1
SECRET_KEY=change-this-to-a-strong-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=sqlite:///./conference_room.db
REDIS_URL=redis://localhost:6379/0
AUTO_CREATE_TABLES=true
CORS_ORIGINS=["http://localhost:8501","http://127.0.0.1:8501"]
```

## Docker 実行

### build

```bash
docker build -t conference-room-backend .
```

### run

```bash
docker run --env-file .env -p 8000:8000 conference-room-backend
```

## Alembic

初回初期化例:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

現在の実装では、学習と動作確認をしやすくするため `AUTO_CREATE_TABLES=true` の場合に起動時テーブル生成も可能にしています。  
本番運用では Alembic を中心に移行管理することを推奨します。

## テスト

```bash
pytest -v
```

## 設計メモ

- `api/`: ルーティング
- `core/`: 設定、セキュリティ、Redis ヘルパー
- `db/`: DB 接続と Base 定義
- `models/`: SQLAlchemy モデル
- `schemas/`: Pydantic スキーマ
- `services/`: ビジネスロジック

## エンドポイント

### 認証
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### ユーザー
- `GET /api/v1/users/me`

### 会議室
- `GET /api/v1/rooms`
- `POST /api/v1/rooms`

### 予約
- `GET /api/v1/bookings/me`
- `POST /api/v1/bookings`
- `DELETE /api/v1/bookings/{booking_id}`

### ヘルスチェック
- `GET /api/v1/health`
- `GET /api/v1/ready`
