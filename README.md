# Conferenceroom_Reservation_System

FastAPI を用いた会議室予約システム API と、Streamlit を用いた簡易フロントエンドを含むポートフォリオ向けプロジェクトです。
JWT 認証、リフレッシュトークン、管理者権限、予約競合チェック、Redis キャッシュ、Redis ロック、Alembic マイグレーション、Docker Compose、テストを備えた構成にしています。

## プロジェクト概要

本システムは、社内の会議室予約業務を想定した Web アプリケーションです。
ユーザーはログイン後に会議室一覧を確認し、自分の予約を作成・参照・キャンセルできます。管理者は会議室を追加できます。
予約時には、同一会議室・同一時間帯の重複予約を防止します。

## 主な機能

- ユーザー登録
- ログイン / ログアウト
- JWT アクセストークン / リフレッシュトークン
- リフレッシュトークンのローテーション
- 自分のユーザー情報取得
- 会議室一覧取得
- 管理者による会議室新規登録
- 予約作成
- 自分の予約一覧取得
- 予約キャンセル
- 予約競合チェック
- Redis キャッシュ
- Redis ロックによる簡易排他制御
- Redis を必須化できる fail-closed 設定
- Health / Ready エンドポイント
- Request ID 付き JSON ログと操作監査ログ
- Prometheus 形式の HTTP 指標エンドポイント
- Streamlit による簡易 UI
- Alembic による DB マイグレーション
- pytest による API テスト

## 技術スタック

### Backend

- FastAPI
- SQLAlchemy 2.x
- MySQL 8.4
- PyMySQL
- Redis
- Pydantic v2 / pydantic-settings
- PyJWT
- Passlib (bcrypt)
- Alembic
- pytest / httpx

### Frontend

- Streamlit
- Requests
- python-dotenv

### Dev / Infra

- Docker
- Docker Compose
- GitHub Actions
- 環境変数ベース設定

## システムアーキテクチャ

```mermaid
flowchart LR
    user[利用者 / 管理者] --> browser[Browser]
    browser --> frontend[Streamlit Frontend<br/>localhost:8501]
    frontend -->|HTTP /api/v1| backend[FastAPI Backend<br/>localhost:8000]

    subgraph application[Backend Application]
        backend --> routes[API Routes / Dependencies]
        routes --> services[Service Layer]
        services --> models[SQLAlchemy Models]
        routes --> ready[Health / Ready / Metrics]
    end

    models -->|READ COMMITTED<br/>SELECT FOR UPDATE| mysql[(MySQL 8.4)]
    services -->|Cache / Room Lock / Token Blacklist| redis[(Redis 7)]
    ready --> mysql
    ready --> redis
    migrations[Alembic Migrations] --> mysql

    subgraph delivery[Quality Gate]
        actions[GitHub Actions CI] --> static[Ruff / mypy / pip-audit]
        actions --> units[SQLite Unit Tests]
        actions --> integration[Docker Compose Integration Tests]
        integration --> testdb[(MySQL Test DB)]
        integration --> testredis[(Redis Test)]
    end
```

- Docker Compose と本番想定のアプリケーション実行は MySQL と Redis を利用します。高速な単体テストのみ SQLite を利用します。
- 本番設定では予約ロックと token blacklist の Redis を必須化し、依存サービス障害時に fail-closed で処理します。
- `/api/v1/ready` は MySQL または必須 Redis が利用不可の場合に `503` を返します。

## 主要ディレクトリ構成

```text
Conferenceroom_Reservation_System/
├─ README.md
├─ DEPLOYMENT.md
├─ .gitignore
├─ .env.example
├─ .dockerignore
├─ .github/
│  └─ workflows/
│     └─ ci.yml
├─ docker-compose.yml
├─ docker-compose.test.yml
├─ backend/
│  ├─ README.md
│  ├─ Dockerfile
│  ├─ .dockerignore
│  ├─ requirements.txt
│  ├─ requirements-dev.txt
│  ├─ mypy.ini
│  ├─ pytest.ini
│  ├─ .env.example
│  ├─ alembic.ini
│  ├─ alembic/
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions/
│  │     ├─ 20260513_0001_initial_schema.py
│  │     └─ 20260527_0002_refresh_session_security.py
│  ├─ tests/
│  │  ├─ conftest.py
│  │  ├─ unit/
│  │  │  ├─ test_auth_rooms_bookings.py
│  │  │  ├─ test_config.py
│  │  │  ├─ test_health.py
│  │  │  └─ test_migrations.py
│  │  ├─ integration/
│  │  │  ├─ test_mysql_booking_conflict.py
│  │  │  ├─ test_refresh_token_rotation_mysql.py
│  │  │  ├─ test_redis_lock_required.py
│  │  │  └─ test_mysql_migrations.py
│  │  └─ e2e/
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     ├─ core/ (logging / observability / security / Redis)
│     ├─ db/
│     ├─ models/
│     ├─ schemas/
│     └─ services/
└─ frontend/
   ├─ README.md
   └─ streamlit_app/
      ├─ Dockerfile
      ├─ .dockerignore
      ├─ app.py
      ├─ api_client.py
      ├─ requirements.txt
      ├─ .env.example
      └─ .streamlit/
         └─ config.toml
```

## クイックスタート（Docker Compose）

### 1. リポジトリを取得

```bash
git clone https://github.com/Ren-Tianming/Conferenceroom_Reservation_System.git
cd Conferenceroom_Reservation_System
```

### 2. 環境変数ファイルを作成

```bash
cp .env.example .env
```

`.env` は Git に含めず、`MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`、`SECRET_KEY`、管理者初期パスワードなどを必ず変更してください。
Docker Compose では `.env` の値を使って MySQL、Redis、Backend、Frontend を起動します。

### 3. 起動

```bash
docker compose up --build
```

バックエンドコンテナは起動時に `alembic upgrade head` を実行してから FastAPI を起動します。

起動後のアクセス先:

- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Frontend: `http://localhost:8501`
- MySQL: `localhost:3306`
- Redis: `localhost:6379`

## ローカル実行

Docker Compose で MySQL と Redis だけを先に起動します。

```bash
docker compose up -d db redis
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows は .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

ローカル実行時の DB 接続先は `.env.example` の通り、`127.0.0.1:3306` を想定しています。

### Frontend

```bash
cd frontend/streamlit_app
python -m venv .venv
source .venv/bin/activate  # Windows は .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## 環境変数

| 変数 | 説明 | 例 |
|---|---|---|
| `APP_NAME` | FastAPI アプリ名 | `Conference Room Reservation System API` |
| `ENV` | 実行環境。`prod` / `production` では安全設定を検証 | `dev` |
| `DEBUG` | デバッグモード | `true` |
| `LOG_LEVEL` | ログレベル | `INFO` |
| `API_V1_PREFIX` | API prefix | `/api/v1` |
| `SECRET_KEY` | JWT 署名鍵。本番では必ず変更 | `change-this-to-a-strong-secret` |
| `JWT_ISSUER` | JWT issuer | `conference-room-api` |
| `JWT_AUDIENCE` | JWT audience | `conference-room-users` |
| `REFRESH_TOKEN_CLEANUP_INTERVAL_SECONDS` | 期限切れ refresh session の削除間隔 | `3600` |
| `DATABASE_URL` | SQLAlchemy 接続 URL。指定時は `DATABASE_*` より優先 | `sqlite:///./local.db` |
| `DATABASE_DRIVER` | SQLAlchemy database driver | `mysql+pymysql` |
| `DATABASE_HOST` | Database host | `127.0.0.1` |
| `DATABASE_PORT` | Database port | `3306` |
| `DATABASE_NAME` | Database name | `conference_room` |
| `DATABASE_USER` | Database user | `conference_user` |
| `DATABASE_PASSWORD` | Database password | `conference_password` |
| `DATABASE_QUERY` | Database URL query | `charset=utf8mb4` |
| `REDIS_URL` | Redis 接続 URL | `redis://localhost:6379/0` |
| `AUTO_CREATE_TABLES` | 学習用の自動テーブル作成 | `true` |
| `BOOTSTRAP_ADMIN_USERNAME` | 初期管理者ユーザー名（任意） | `admin` |
| `BOOTSTRAP_ADMIN_PASSWORD` | 初期管理者パスワード（任意） | `change-this-admin-password` |
| `REQUIRE_REDIS_FOR_LOCKS` | Redis ロックを必須化 | `false` |
| `REQUIRE_REDIS_FOR_TOKEN_BLACKLIST` | token blacklist 用 Redis を必須化 | `false` |
| `CORS_ORIGINS` | CORS 許可 origin | `["http://localhost:8501"]` |

Docker Compose では以下も使用します。

| 変数 | 説明 | 例 |
|---|---|---|
| `MYSQL_DATABASE` | MySQL database | `conference_room` |
| `MYSQL_USER` | MySQL application user | `conference_user` |
| `MYSQL_PASSWORD` | MySQL application password | `change-this-mysql-password` |
| `MYSQL_ROOT_PASSWORD` | MySQL root password | `change-this-root-password` |
| `TZ` | コンテナ timezone | `Asia/Tokyo` |

## API エンドポイント

### 認証

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`（`Authorization: Bearer` と body の `refresh_token` を使用）
- `POST /api/v1/auth/logout-all`（全端末の refresh session を無効化）

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
- `GET /api/v1/ready`（DB または必須 Redis 障害時は `503`。任意 Redis 障害時は `200` / `degraded`）
- `GET /api/v1/metrics`（Prometheus text format の HTTP リクエスト数 / 処理時間）

## API フロー

### 認証とセッション管理

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant UI as Streamlit / Client
    participant API as FastAPI Auth API
    participant DB as MySQL
    participant Redis as Redis

    User->>UI: ユーザー名・パスワード入力
    UI->>API: POST /auth/login
    API->>DB: 資格情報を検証
    API->>DB: refresh token hash と端末情報を保存
    API-->>UI: access token + refresh token

    opt Access token の更新
        UI->>API: POST /auth/refresh (refresh token)
        API->>DB: 旧 session を revoke して新 session を保存
        API->>Redis: 旧 JTI を blacklist
        API-->>UI: 新 access token + refresh token
    end

    alt 単一端末ログアウト
        UI->>API: POST /auth/logout<br/>Authorization: Bearer access_token<br/>{ refresh_token }
        API->>Redis: access / refresh JTI を blacklist
        API->>DB: 対象 session を revoke
    else 全端末ログアウト
        UI->>API: POST /auth/logout-all<br/>Authorization: Bearer access_token
        API->>DB: ユーザーの全 session を revoke
        API->>Redis: 各 JTI を blacklist
    end
    API-->>UI: 200 OK
```

### 予約作成と競合制御

```mermaid
sequenceDiagram
    autonumber
    participant UI as Streamlit / Client
    participant API as FastAPI Booking API
    participant Redis as Redis
    participant DB as MySQL (READ COMMITTED)

    UI->>API: POST /bookings<br/>Authorization: Bearer access_token
    API->>Redis: room lock を取得
    alt Redis が必須で利用不可
        API-->>UI: 503 Service Unavailable
    else Lock 取得成功または optional fallback
        API->>DB: SELECT room FOR UPDATE
        API->>DB: 重複時間帯を SELECT FOR UPDATE
        alt 競合予約あり
            API->>Redis: room lock を解放
            API-->>UI: 409 Conflict
        else 空きあり
            API->>DB: booking INSERT / COMMIT
            API->>Redis: room lock を解放
            API-->>UI: 201 Created
        end
    end
```

## データベース

本プロジェクトの標準 DB は MySQL 8.4 です。
SQLAlchemy モデルを定義し、Alembic の初期マイグレーションで以下のテーブルを作成します。

- `users`: ユーザー、パスワードハッシュ、ロール、状態
- `rooms`: 会議室名、定員、場所、説明
- `bookings`: 予約タイトル、時間帯、状態、ユーザー、会議室。MySQL では会議室行をロックして競合予約を直列化
- `refresh_tokens`: refresh token の JTI と SHA-256 hash、端末メタデータ、期限、無効化状態

MySQL 接続では予約競合の扱いを明示するため、トランザクション分離レベルを `READ COMMITTED` に設定しています。refresh session の期限切れレコードは、新規発行時と設定された間隔のバックグラウンド処理で削除されます。

## テスト

高速な API / 設定テストは SQLite を使って実行します。

```bash
cd backend
pytest -q tests/unit
```

予約競合、トークンローテーション、Redis 必須動作、migration は実際の MySQL / Redis 上で検証します。リポジトリルートから専用の一時テストサービスを起動してください。

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from integration-tests
docker compose -f docker-compose.test.yml down
```

ローカルで既にテスト専用 MySQL / Redis が稼働している場合は、次のようにも実行できます。`MYSQL_TEST_DATABASE_URL` のデータベース名には安全保護のため `test` が必要で、テスト中に schema を再作成します。

```bash
cd backend
MYSQL_TEST_DATABASE_URL='mysql+pymysql://conference_test_user:conference_test_password@127.0.0.1:3306/conference_room_test?charset=utf8mb4' \
REDIS_TEST_URL='redis://127.0.0.1:6379/15' \
pytest -q tests/integration
```

## CI

GitHub Actions の `.github/workflows/ci.yml` は、push、pull request、手動実行で以下の品質ゲートを実行します。

- `ruff check .` による Python lint
- `mypy .` によるバックエンドの型チェック
- `pytest -q tests/unit` による高速テスト
- `pip-audit` による backend / frontend 依存関係の脆弱性検査
- backend / frontend Docker image の build
- `docker-compose.test.yml` による MySQL / Redis 統合テストと Alembic migration 検証

lint、型チェック、単体テストをローカルで同じように実行する場合:

```bash
cd backend
python -m pip install -r requirements-dev.txt
ruff check .
mypy .
pytest -q tests/unit
```

MySQL / Redis を含む CI 相当の統合チェックは、リポジトリルートで実行します。

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from integration-tests
docker compose -f docker-compose.test.yml down --volumes --remove-orphans
```

## Docker / デプロイ

AWS EC2 への配置、TLS、Security Group、バックアップ、監視収集の手順は [`DEPLOYMENT.md`](./DEPLOYMENT.md) を参照してください。

### ローカル Docker 起動

```bash
cp .env.example .env
# .env のパスワードと SECRET_KEY を変更
docker compose up --build
```

状態確認:

```bash
docker compose ps
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
curl http://localhost:8000/api/v1/metrics
```

停止:

```bash
docker compose down
```

データ volume も削除する場合:

```bash
docker compose down -v
```

### 本番環境の注意事項

- `.env` は Git に含めないでください。
- `ENV=production`、`DEBUG=false`、`AUTO_CREATE_TABLES=false` を設定してください。
- `SECRET_KEY` は 32 文字以上の十分にランダムな値にしてください。
- `MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`、`BOOTSTRAP_ADMIN_PASSWORD` は推測困難な値にしてください。
- `CORS_ORIGINS` は実際のフロントエンド origin のみに絞ってください。
- `REQUIRE_REDIS_FOR_LOCKS=true` と `REQUIRE_REDIS_FOR_TOKEN_BLACKLIST=true` を設定し、Redis 障害時は fail-closed にしてください。
- 本番では MySQL / Redis の port をインターネットへ直接公開しないでください。
- JSON ログを CloudWatch Logs 等に転送し、`/api/v1/metrics` と `/api/v1/ready` を監視してください。
- TLS 終端、reverse proxy、バックアップ、アラート、デプロイ先に応じた CD は別途用意してください。
- 初回管理者作成後は `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD` を外す運用を推奨します。

## 設計方針

- **責務分離**: API / Schema / Model / Service / DB 設定を分離
- **セキュリティ**: パスワードハッシュ化、JWT、refresh token rotation、管理者権限を採用
- **整合性**: 予約作成時に時間帯重複を検査し、DB 制約とインデックスを追加
- **可用性**: Redis 障害時の graceful fallback と fail-closed 設定を選択可能
- **拡張性**: Alembic、tests、Docker Compose を含む構成
- **可視性**: Request ID 付き JSON ログ、操作監査イベント、Health / Ready / Metrics endpoint を用意

## 今後の拡張候補

- 会議室検索・空き時間検索
- 予約承認ワークフロー
- メール通知
- 外部 Prometheus / CloudWatch ダッシュボードとアラート
- 配備先に応じた GitHub Actions CD
- 本番向け Nginx / Reverse Proxy 構成
- MySQL での予約排他制御とトランザクション設計のさらなる強化

## 備考

このプロジェクトはポートフォリオおよび学習用途を想定した実装です。
実運用を行う場合は、認可設計、ログ監視、例外処理、監査、セキュリティポリシー、バックアップ、秘密情報管理などを追加で強化してください。
