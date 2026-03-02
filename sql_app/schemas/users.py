from pydantic import BaseModel, Field
from typing import Optional


# =========================
# 共通字段
# =========================
class UserBase(BaseModel):
    user_name: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="ユーザー名"
    )


# =========================
# 创建用户
# =========================
class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="パスワード"
    )


# =========================
# 更新用户
# =========================
class UserUpdate(BaseModel):
    user_name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=64
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128
    )


# =========================
# 登录
# =========================
class UserLogin(BaseModel):
    user_name: str
    password: str


# =========================
# 返回给前端的用户信息
# =========================
class UserResponse(UserBase):
    user_id: int

    class Config:
        from_attributes = True