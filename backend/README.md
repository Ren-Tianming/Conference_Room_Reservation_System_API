# Backend - conference-room-reservation-system

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
- PyJWT
- Alembic
- pytest / httpx（dev / test）

## ディレクトリ構成

```text
backend/
├─ README.md
├─ Dockerfile
├─ requirements.txt
├─ requirements-dev.txt
├─ .env.example
├─ alembic.ini
├─ alembic/
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions/
├─ tests/
│  ├─ conftest.py
│  ├─ unit/
│  ├─ integration/
│  │  ├─ test_mysql_booking_conflict.py
│  │  ├─ test_refresh_token_rotation_mysql.py
│  │  ├─ test_redis_lock_required.py
│  │  └─ test_mysql_migrations.py
│  └─ e2e/
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
- Redis ロックと開発用プロセス内フォールバックによる排他制御
- Redis 障害時の開発用プロセス内ロック / fail-closed 切り替え
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

## 環境変数

最新の設定例は [backend/.env.example](./.env.example) を参照してください。主な設定は JWT、MySQL、Redis、CORS、refresh session cleanup、最大予約時間、bootstrap admin です。

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

SQLite を使う高速な API / 設定テスト:

```bash
pytest -q tests/unit
```

MySQL のロックとトランザクション、Redis ロック、refresh token の並行ローテーション、Alembic migration を検証する統合テストは、リポジトリルートで専用 Compose スタックを使って実行します。

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from integration-tests
docker compose -f docker-compose.test.yml down
```

手元の専用テストサービスを使用する場合:

```bash
MYSQL_TEST_DATABASE_URL='mysql+pymysql://conference_test_user:conference_test_password@127.0.0.1:3306/conference_room_test?charset=utf8mb4' \
REDIS_TEST_URL='redis://127.0.0.1:6379/15' \
pytest -q tests/integration
```

`MYSQL_TEST_DATABASE_URL` のデータベース名には `test` を含めてください。統合テストは各ケースの前にその schema を migration で作り直します。

### CI 品質チェック

GitHub Actions は `requirements-dev.txt` のツールを使って lint、型チェック、単体テストを実行します。ローカルで確認する場合:

```bash
python -m pip install -r requirements-dev.txt
ruff check .
mypy .
pytest -q tests/unit
```

依存関係の脆弱性検査はリポジトリルートから次のように実行できます。

```bash
pip-audit -r backend/requirements.txt
pip-audit -r frontend/streamlit_app/requirements.txt
```

## API エンドポイント

### 認証

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`（access token は `Authorization: Bearer`、body は `refresh_token` のみ）
- `POST /api/v1/auth/logout-all`（全端末の refresh session を無効化）

### ユーザー

- `GET /api/v1/users/me`

### 会議室

- `GET /api/v1/rooms`
- `POST /api/v1/rooms`（管理者のみ）

### 予約

- `GET /api/v1/bookings/me`
- `POST /api/v1/bookings`（timezone 付き未来日時、最大予約時間内のみ）
- `DELETE /api/v1/bookings/{booking_id}`

### ヘルスチェック

- `GET /api/v1/health`
- `GET /api/v1/ready`（DB または必須 Redis 障害時は `503`。任意 Redis 障害時は `200` / `degraded`）
- `GET /api/v1/metrics`（Prometheus text format の HTTP リクエスト数 / 処理時間）

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
- `token_hash`: refresh token の SHA-256 hash
- `expires_at`
- `revoked`
- `user_agent`
- `ip_address`
- `device_name`
- `user_id`
- `created_at`

## 設計メモ

- `api/`: ルーティングと依存関係
- `core/`: 設定、セキュリティ、Redis、JSON ログ、Prometheus 形式の可観測性
- `db/`: DB 接続と Base 定義
- `models/`: SQLAlchemy モデル
- `schemas/`: Pydantic スキーマ
- `services/`: ビジネスロジック

MySQL 接続は `READ COMMITTED` で実行し、予約作成時は対象の `rooms` 行を `SELECT ... FOR UPDATE` でロックして、同一会議室の重複判定を直列化します。予約時刻は timezone 付き、未来時刻、`MAX_BOOKING_DURATION_HOURS` 以内で検証します。期限切れの refresh session は token 発行時と `REFRESH_TOKEN_CLEANUP_INTERVAL_SECONDS` 間隔のバックグラウンド処理で削除されます。

各 HTTP 応答には `X-Request-ID` が含まれ、ログは JSON 形式で `method`、`path`、`status_code`、`duration_ms` を記録します。ログイン失敗、予約作成 / キャンセル、管理者による会議室作成は監査対象イベントとして出力されます。

## 運用上の注意

- 本番環境では `SECRET_KEY` を必ず変更してください。
- 本番環境では `DEBUG=false` を設定してください。
- 本番環境では `AUTO_CREATE_TABLES=false` とし、Alembic で migration を管理してください。
- Redis を必須コンポーネントとして扱う場合は、`REQUIRE_REDIS_FOR_LOCKS=true` と `REQUIRE_REDIS_FOR_TOKEN_BLACKLIST=true` を検討してください。
