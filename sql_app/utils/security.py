from passlib.context import CryptContext

# パスワードの暗号化に使用するコンテキストを作成
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワードをハッシュ化する関数
def hash_password(password: str):
    return pwd_context.hash(password)