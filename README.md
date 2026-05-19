# Conference Room Reservation System API

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
- python-jose
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
- 環境変数ベース設定

## ディレクトリ構成

```text
Conference_Room_Reservation_System_API/
├─ README.md
├─ .gitignore
├─ docker-compose.yml
├─ backend/
│  ├─ README.md
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ .env.example
│  ├─ alembic.ini
│  ├─ alembic/
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions/
│  │     └─ 20260513_0001_initial_schema.py
│  ├─ tests/
│  │  ├─ conftest.py
│  │  ├─ test_auth_rooms_bookings.py
│  │  └─ test_health.py
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     ├─ core/
│     ├─ db/
│     ├─ models/
│     ├─ schemas/
│     └─ services/
└─ frontend/
   ├─ README.md
   └─ streamlit_app/
      ├─ Dockerfile
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
git clone https://github.com/Ren-Tianming/Conference_Room_Reservation_System_API.git
cd Conference_Room_Reservation_System_API
```

### 2. 環境変数ファイルを作成

```bash
cp backend/.env.example backend/.env
cp frontend/streamlit_app/.env.example frontend/streamlit_app/.env
```

Docker Compose では `docker-compose.yml` 側で、バックエンドコンテナ用の `DATABASE_URL` と `REDIS_URL` を `db` / `redis` サービス向けに上書きします。

### 3. 起動

```bash
docker compose up --build
```

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
| `API_V1_PREFIX` | API prefix | `/api/v1` |
| `SECRET_KEY` | JWT 署名鍵。本番では必ず変更 | `change-this-to-a-strong-secret` |
| `DATABASE_URL` | SQLAlchemy 用 MySQL 接続 URL | `mysql+pymysql://conference_user:conference_password@127.0.0.1:3306/conference_room?charset=utf8mb4` |
| `REDIS_URL` | Redis 接続 URL | `redis://localhost:6379/0` |
| `AUTO_CREATE_TABLES` | 学習用の自動テーブル作成 | `true` |
| `BOOTSTRAP_ADMIN_USERNAME` | 初期管理者ユーザー名（任意） | `admin` |
| `BOOTSTRAP_ADMIN_PASSWORD` | 初期管理者パスワード（任意） | `change-this-admin-password` |
| `REQUIRE_REDIS_FOR_LOCKS` | Redis ロックを必須化 | `false` |
| `REQUIRE_REDIS_FOR_TOKEN_BLACKLIST` | token blacklist 用 Redis を必須化 | `false` |
| `CORS_ORIGINS` | CORS 許可 origin | `["http://localhost:8501"]` |

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

## データベース

本プロジェクトの標準 DB は MySQL 8.4 です。
SQLAlchemy モデルを定義し、Alembic の初期マイグレーションで以下のテーブルを作成します。

- `users`: ユーザー、パスワードハッシュ、ロール、状態
- `rooms`: 会議室名、定員、場所、説明
- `bookings`: 予約タイトル、時間帯、状態、ユーザー、会議室
- `refresh_tokens`: refresh token の JTI、期限、無効化状態

## テスト

```bash
cd backend
pytest -q
```

テストでは高速で分離しやすい SQLite ファイル DB を利用しています。アプリケーションの標準実行環境は MySQL です。

## 設計方針

- **責務分離**: API / Schema / Model / Service / DB 設定を分離
- **セキュリティ**: パスワードハッシュ化、JWT、refresh token rotation、管理者権限を採用
- **整合性**: 予約作成時に時間帯重複を検査し、DB 制約とインデックスを追加
- **可用性**: Redis 障害時の graceful fallback と fail-closed 設定を選択可能
- **拡張性**: Alembic、tests、Docker Compose を含む構成
- **可視性**: Health / Ready endpoint とログ設定を用意

## 今後の拡張候補

- 会議室検索・空き時間検索
- 予約承認ワークフロー
- メール通知
- 監査ログ
- GitHub Actions による CI/CD
- 本番向け Nginx / Reverse Proxy 構成
- MySQL での予約排他制御とトランザクション設計のさらなる強化

## 備考

このプロジェクトはポートフォリオおよび学習用途を想定した実装です。
実運用を行う場合は、認可設計、ログ監視、例外処理、監査、セキュリティポリシー、バックアップ、秘密情報管理などを追加で強化してください。
