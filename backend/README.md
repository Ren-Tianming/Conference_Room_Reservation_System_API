# Backend

このディレクトリには、会議室予約システムのバックエンド API が含まれています。
FastAPI を中心に、ユーザー認証、会議室管理、予約管理、Redis キャッシュ、予約競合防止、管理者権限、MySQL マイグレーションを提供します。

## 使用技術

- FastAPI
- SQLAlchemy 2.x
- MySQL 8.4
- PyMySQL
- Redis
- Pydantic v2 / pydantic-settings
- Passlib (bcrypt)
- python-jose
- Alembic
- pytest / httpx

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
│     └─ 20260513_0001_initial_schema.py
├─ tests/
│  ├─ conftest.py
│  ├─ test_auth_rooms_bookings.py
│  └─ test_health.py
└─ app/
   ├─ main.py
   ├─ api/
   │  ├─ deps.py
   │  ├─ router.py
   │  └─ routes/
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
- リフレッシュトークンのローテーション
- token blacklist によるログアウト後 access token 無効化
- 自分のユーザー情報取得
- 会議室一覧取得
- 管理者による会議室登録
- 予約作成 / 自分の予約一覧 / 予約キャンセル
- 予約競合チェック
- Redis キャッシュ
- Redis ロックによる簡易排他制御
- Redis 障害時の graceful fallback / fail-closed 切り替え
- Health / Ready エンドポイント
- MySQL 用 Alembic マイグレーション
- bootstrap admin の任意作成

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
.venv\Scripts\activate
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

### 4. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 5. MySQL / Redis 起動

リポジトリルートから以下を実行します。

```bash
docker compose up -d db redis
```

### 6. マイグレーション実行

```bash
alembic upgrade head
```

### 7. アプリ起動

```bash
uvicorn app.main:app --reload
```

## `.env.example` の内容

```env
APP_NAME=Conference Room Reservation System API
ENV=dev
DEBUG=true
LOG_LEVEL=INFO
API_V1_PREFIX=/api/v1
SECRET_KEY=change-this-to-a-strong-secret
ALGORITHM=HS256
JWT_ISSUER=conference-room-api
JWT_AUDIENCE=conference-room-users
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
# BOOTSTRAP_ADMIN_USERNAME=admin
# BOOTSTRAP_ADMIN_PASSWORD=change-this-admin-password
# DATABASE_URL を指定した場合は以下の DATABASE_* より優先されます。
# DATABASE_URL=sqlite:///./local.db
DATABASE_DRIVER=mysql+pymysql
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_NAME=conference_room
DATABASE_USER=conference_user
DATABASE_PASSWORD=conference_password
DATABASE_QUERY=charset=utf8mb4
REDIS_URL=redis://localhost:6379/0
REQUIRE_REDIS_FOR_LOCKS=false
REQUIRE_REDIS_FOR_TOKEN_BLACKLIST=false
AUTO_CREATE_TABLES=true
CORS_ORIGINS=["http://localhost:8501","http://127.0.0.1:8501"]
```

## Docker 実行

### build

```bash
docker build -t conference-room-backend .
```

### run

単体で起動する場合は、MySQL / Redis に接続できる `DATABASE_*` または `DATABASE_URL` と `REDIS_URL` を指定してください。

```bash
docker run --env-file .env -p 8000:8000 conference-room-backend
```

Docker Compose で起動する場合は、リポジトリルートで以下を実行します。

```bash
cp .env.example .env
docker compose up --build
```

Compose ではリポジトリルートの `.env` から MySQL / JWT / CORS 設定を読み込み、バックエンドコンテナ向けに `DATABASE_*` と `REDIS_URL` を設定します。
バックエンドコンテナは起動時に `alembic upgrade head` を実行してから FastAPI を起動します。

## Alembic

初期マイグレーションは `alembic/versions/20260513_0001_initial_schema.py` です。

```bash
alembic upgrade head
```

新しいモデル変更を追加する場合の例:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

学習用途として `AUTO_CREATE_TABLES=true` の場合は起動時に `Base.metadata.create_all()` を実行できます。
本番運用では Alembic を中心に移行管理し、`AUTO_CREATE_TABLES=false` を推奨します。

## テスト

```bash
pytest -q
```

テストでは `tests/conftest.py` により SQLite ファイル DB を使用し、各テストでテーブルを作り直します。標準実行環境は MySQL です。

## API エンドポイント

### 認証

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### ユーザー

- `GET /api/v1/users/me`

### 会議室

- `GET /api/v1/rooms`
- `POST /api/v1/rooms`（管理者のみ）

### 予約

- `GET /api/v1/bookings/me`
- `POST /api/v1/bookings`
- `DELETE /api/v1/bookings/{booking_id}`

### ヘルスチェック

- `GET /api/v1/health`
- `GET /api/v1/ready`

## データモデル概要

### users

- `id`
- `username`
- `password_hash`
- `role`: `user` / `admin`
- `is_active`
- `created_at`

### rooms

- `id`
- `name`
- `capacity`
- `location`
- `description`
- `created_at`

### bookings

- `id`
- `title`
- `purpose`
- `attendee_count`
- `start_time`
- `end_time`
- `status`: `active` / `cancelled` / `completed`
- `user_id`
- `room_id`
- `created_at`

### refresh_tokens

- `id`
- `token_jti`
- `expires_at`
- `revoked`
- `user_id`
- `created_at`

## 設計メモ

- `api/`: ルーティングと依存関係
- `core/`: 設定、セキュリティ、Redis、ログ
- `db/`: DB 接続と Base 定義
- `models/`: SQLAlchemy モデル
- `schemas/`: Pydantic スキーマ
- `services/`: ビジネスロジック

## 運用上の注意

- 本番環境では `SECRET_KEY` を必ず変更してください。
- 本番環境では `DEBUG=false` を設定してください。
- 本番環境では `AUTO_CREATE_TABLES=false` とし、Alembic で migration を管理してください。
- Redis を必須コンポーネントとして扱う場合は、`REQUIRE_REDIS_FOR_LOCKS=true` と `REQUIRE_REDIS_FOR_TOKEN_BLACKLIST=true` を検討してください。
