from fastapi import APIRouter, Depends, Query, HTTPException
from sql_app.crud.crud import news
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_config import get_db