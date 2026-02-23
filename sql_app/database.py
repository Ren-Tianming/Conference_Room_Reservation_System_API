import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.sql.functions import now
from sqlalchemy.orm import Mapped, mapped_column

load_dotenv()
ASYNC_DATABASE_URL = os.getenv("DATABASE_URL")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  
    pool_size=10, 
    max_overflow=20
)

class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=now(), 
        comment="作成時間"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=now(),
        onupdate=now(),
        comment="更新時間"
    )

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def create_table():
    # print("--- テープルを作成中 ---")
    # print(f"DEBUG　作成中のテープル: {Base.metadata.tables.keys()}")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # print("--- テープル作成完了 ---")

