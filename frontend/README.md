# Frontend

このディレクトリには、会議室予約システムの簡易フロントエンドが含まれています。  
Streamlit を利用して、バックエンド API の疎通確認、ログイン、会議室一覧表示、予約作成、予約一覧確認などを行える構成です。

## 構成

```text
frontend/
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

## 使用技術

- Streamlit
- Requests
- python-dotenv

## セットアップ

### 1. ディレクトリ移動

```bash
cd frontend/streamlit_app
```

### 2. 環境変数ファイル作成

```bash
cp .env.example .env
```

### 3. 仮想環境作成

```bash
python -m venv .venv
```

### 4. 仮想環境有効化

#### Windows

```bash
.venv\Scriptsctivate
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

### 5. パッケージインストール

```bash
pip install -r requirements.txt
```

### 6. 起動

```bash
streamlit run app.py
```

## `.env.example`

```env
BACKEND_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 画面でできること

- ユーザー登録
- ログイン
- ログアウト
- 自分のユーザー情報表示
- 会議室一覧表示
- 会議室追加
- 予約作成
- 自分の予約一覧表示
- 予約キャンセル

## 補足

このフロントエンドは API 確認用のシンプルな UI です。  
将来的に本格的なフロントエンドへ発展させる場合は、React / Next.js などへ置き換えることも可能です。
