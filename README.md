# Conference Room Reservation System API

FastAPI を用いた会議室予約システムのバックエンド API と、Streamlit を用いた簡易フロントエンドを含むポートフォリオ向けプロジェクトです。  
単純な CRUD だけではなく、JWT 認証、予約競合チェック、Redis キャッシュ、簡易排他制御、テスト、Alembic 構成を意識した標準的なプロジェクト構成に整理しています。

## プロジェクト概要

本システムは、社内の会議室予約業務を想定した Web アプリケーションです。  
ユーザーはログイン後に会議室一覧を確認し、自分の予約を作成・参照・キャンセルできます。  
予約時には、同一会議室・同一時間帯の重複予約を防止する仕組みを実装しています。

## 主な機能

- ユーザー登録
- ログイン / ログアウト
- JWT アクセストークン / リフレッシュトークン
- 自分のユーザー情報取得
- 会議室一覧取得
- 会議室新規登録
- 予約作成
- 自分の予約一覧取得
- 予約キャンセル
- 予約競合チェック
- Redis キャッシュ
- Redis ロックによる簡易排他制御
- Health / Ready エンドポイント
- Streamlit による簡易 UI

## 技術スタック

### Backend
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL / SQLite
- Redis
- Pydantic v2
- python-jose
- Passlib (bcrypt)
- Alembic
- pytest

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
│  ├─ tests/
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

## クイックスタート

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

### 3. Docker Compose で起動

```bash
docker compose up --build
```

起動後のアクセス先:

- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Frontend: `http://localhost:8501`

## ローカル実行

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows は .venv\Scriptsctivate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend/streamlit_app
python -m venv .venv
source .venv/bin/activate  # Windows は .venv\Scriptsctivate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## API の主なエンドポイント

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

## 設計方針

- **責務分離**: API / Schema / Model / Service / DB 設定を分離
- **セキュリティ**: パスワードハッシュ化と JWT 認証を採用
- **整合性**: 予約作成時に時間帯重複を検査
- **拡張性**: Alembic、tests、Docker を含む構成
- **可視性**: Streamlit フロントエンドで API 動作を確認可能

## 今後の拡張候補

- 管理者権限の追加
- 予約承認ワークフロー
- メール通知
- 監査ログ
- GitHub Actions による CI/CD
- 本番向け Nginx / Reverse Proxy 構成

## 備考

このプロジェクトはポートフォリオおよび学習用途を想定した実装です。  
実運用を行う場合は、認可設計、ログ監視、例外処理、監査、セキュリティポリシーなどを追加で強化してください。
