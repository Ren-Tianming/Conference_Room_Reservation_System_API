# Streamlit フロントエンド

これは `meeting_room_v2` バックエンドに対応する Streamlit フロントエンドです。

## 主な機能

- ユーザー登録 / ログイン
- トークン更新 / ログアウト
- 会議室一覧の参照
- 指定日のスケジュール確認
- 予約作成
- 自分の予約一覧 / 予約キャンセル
- 管理者向け会議室作成 / 更新

## 起動方法

最初に FastAPI バックエンドを起動し、その後 Streamlit を別途起動してください。

```bash
cd frontend_streamlit
pip install -r requirements.txt
streamlit run app.py
```

デフォルトのバックエンド URL は以下です。

```text
http://localhost:8000/api/v1
```

バックエンドの URL が異なる場合は、画面左側のサイドバーから変更できます。
