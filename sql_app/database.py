# SQLAlchemy のエンジン生成用関数をインポート
from sqlalchemy import create_engine

# ORM関連（セッション生成、モデル基底クラス）
from sqlalchemy.orm import sessionmaker, declarative_base


# ===============================
# データベース接続URLの定義
# ===============================

# SQLiteデータベースを使用
# ./sql_app.db はプロジェクト直下に作成される
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"


# ===============================
# データベースエンジンの生成
# ===============================

# create_engine でDB接続エンジンを作成
# SQLiteはマルチスレッド制限があるため
# check_same_thread=False を指定する
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# ===============================
# セッションファクトリの作成
# ===============================

# DB操作を行うためのセッション生成クラス
# autocommit=False → 手動でcommitが必要
# autoflush=False → 自動flushを無効化
# bind=engine → 上で作成したengineを使用
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ===============================
# ORMモデル用の基底クラス
# ===============================

# models.pyで継承して使用する
Base = declarative_base()
