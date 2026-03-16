# 会議室予約システム V2（エンタープライズ向け改良版）

这是基于你当前 V1 CRUD 项目升级后的后端骨架，重点补上了企业项目里最常见的能力：

- 用户注册 / 登录 / JWT 鉴权
- Access Token + Refresh Token
- 密码哈希（Argon2）
- Redis 缓存（会议室列表、每日排期）
- Redis Token 管理（refresh token 存储、access token 黑名单）
- 预约冲突校验
- 并发预约保护（Redis 分布式锁 + 数据库行锁）
- 管理员创建/维护会议室
- `/health` 和 `/ready` 探针接口
- 分层目录结构（api / core / db / models / schemas / services）

## 1. 为什么不能继续沿用你 V1 的结构

你 V1 的问题不是“能不能加功能”，而是**继续在原结构上补功能，后面会越来越难维护**：

- `main.py` 直接堆路由，后期很难拆分
- `crud.py` 把简单查询和业务规则混在一起
- `schemas.py` / `models.py` 还停留在最基础 CRUD
- 没有密码哈希，没有鉴权，也没有角色控制
- 预约虽然做了冲突判断，但没有考虑并发下的竞态条件
- 没有缓存层，也没有 token 生命周期管理

所以 V2 直接升级为更符合企业项目的目录结构。

## 2. 运行方式

```bash
cp .env.example .env
docker compose up
```

启动后访问：

- Swagger: `http://localhost:8000/docs`
- OpenAPI: `http://localhost:8000/openapi.json`

## 3. 推荐调用顺序

1. `POST /api/v1/auth/register` 注册
2. `POST /api/v1/auth/login` 登录
3. 使用返回的 `access_token` 调用受保护接口
4. `POST /api/v1/auth/refresh` 刷新 token
5. 管理员调用 `POST /api/v1/rooms` 创建会议室
6. 普通用户调用 `POST /api/v1/bookings` 创建预约

## 4. 当前并发保护策略

V2 已经用了两层保护：

1. **Redis 锁**：同一会议室的并发预约先串行化，避免瞬间多个请求同时通过应用层判断。  
2. **数据库行锁**：在创建预约时对会议室行加锁，再做一次 overlap 检查，降低竞态风险。

这已经比 V1 的“先查再插入”强很多。

## 5. 真正生产环境的下一步建议

你下一阶段可以继续补这些能力：

- Alembic 数据库迁移
- Nginx + Gunicorn/Uvicorn 多实例部署
- PostgreSQL Exclusion Constraint（从数据库层彻底兜住时间重叠）
- pytest 自动化测试
- RBAC 更细粒度权限
- 操作审计日志
- 限流、防刷、幂等键
- CI/CD（GitHub Actions）

## 6. 和你 V1 的关系

这份 V2 不是简单“在旧文件上打补丁”，而是**按企业后端方式重构**。你后面在 GitHub 展示项目时，也会比 V1 更像真实工程项目。


## 7. Streamlit フロントエンド

このプロジェクトには、FastAPI バックエンドと連携する `frontend_streamlit/` も追加しています。

### 主な機能

- ユーザー登録 / ログイン
- Access Token / Refresh Token の更新
- 会議室一覧表示
- 日別スケジュール確認
- 予約作成 / 自分の予約一覧 / 予約キャンセル
- 管理者向け会議室作成・更新

### 起動方法

```bash
cd frontend_streamlit
pip install -r requirements.txt
streamlit run app.py
```

デフォルトの接続先 API は以下です。

```text
http://localhost:8000/api/v1
```

必要に応じて、画面左側のサイドバーから接続先を変更できます。
