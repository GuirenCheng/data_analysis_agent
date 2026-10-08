# 用 Docker 部署到云服务器

本教程面向第一次接触 Docker 的读者，把本项目逐步部署到一台 Linux 云服务器，并在浏览器里使用。

## 一、整体架构

项目由 5 个容器组成，由 `docker-compose.yml` 统一编排：

| 容器 | 作用 | 对外端口 |
|------|------|----------|
| `frontend` | Nginx：托管前端静态页面 + 把 `/api` 反向代理到后端 | **8080** |
| `api` | FastAPI 后端（登录、会话、上传、SSE 进度推送等） | 8000（仅调试） |
| `worker` | ARQ 后台任务，真正执行 LLM 数据分析工作流 | 无 |
| `mysql` | MySQL 8.0（用户、会话、步骤等业务数据） | 无（仅内网） |
| `redis` | Redis 7（任务队列 + 缓存 + 进度） | 无（仅内网） |

只有 `frontend` 对外提供服务；MySQL / Redis / worker / api 都在 Docker 内网里互相访问，更安全。

## 二、前提

- 一台 Linux 云服务器（Ubuntu 20.04 / 22.04 / 24.04 均可，本教程以 Ubuntu 为例）
- 已安装 Docker 与 Docker Compose 插件

安装 Docker（Ubuntu 一行命令）：

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # 让当前用户免 sudo 使用 docker（需重新登录生效）
newgrp docker
docker --version && docker compose version
```

## 三、上传项目

```bash
# 方式一：git clone（如果代码已推到 GitHub/Gitee）
git clone <你的仓库地址> data_analysis_agent
cd data_analysis_agent

# 方式二：从本地 Windows 用 scp 上传
# 在本地 PowerShell 执行：
#   scp -r C:\Users\你\Desktop\data_analysis_agent 用户名@服务器IP:~
# 然后在服务器上 cd data_analysis_agent
```

## 四、配置环境变量（密钥）

```bash
cp .env.example .env
nano .env    # 或 vim .env
```

需要填写/修改的项：

| 变量 | 说明 |
|------|------|
| `LLM_API_KEY` | DeepSeek（或其它 OpenAI 兼容服务）的 API Key |
| `EMBEDDING_API_KEY` | 独立的 Embedding 服务 API Key（**必填**，见下方说明） |
| `EMBEDDING_BASE_URL` | Embedding 服务的 base_url（如硅基流动 `https://api.siliconflow.cn/v1`） |
| `EMBEDDING_MODEL` | Embedding 模型名（如 `BAAI/bge-m3`） |
| `SECRET_KEY` / `JWT_SECRET_KEY` | 任意随机字符串，务必改掉默认值 |
| `MYSQL_PASSWORD` | 应用数据库账号（`daa`）的密码 |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 |

> **为什么需要单独的 Embedding 服务？** 本项目的 RAG 检索要把历史分析内容转成向量。DeepSeek 没有 embedding 接口，所以必须单独配一个 OpenAI 兼容的 embedding 服务（硅基流动 / 智谱 / OpenAI 等）。不配也不影响主分析流程（代码里已做降级：检索失败会静默跳过），但历史分析参考（RAG）就失效了。

> 注意：`.env` 含密钥，已被 `.dockerignore` 排除、不会打进镜像；但**不要把它提交到 git**（`.gitignore` 已忽略 `.env`）。

## 五、构建并启动

```bash
docker compose up -d --build
```

- `--build`：先构建镜像（首次较慢，因为要下载并安装 Python / Node 依赖）
- `-d`：后台运行（detach）

查看状态：

```bash
docker compose ps                 # 应全部 running，mysql/redis 显示 healthy
docker compose logs -f api worker # 跟踪后端/worker 日志（Ctrl+C 退出）
```

> 首次启动 MySQL 会自动执行 `scripts/init.sql` 建表，一般几十秒内完成；若 `api` 启动时报连不上数据库，等 MySQL `healthy` 后 `docker compose restart api worker` 即可。

## 六、访问

浏览器打开 `http://服务器IP:8080`，注册一个账号，上传 CSV 文件、输入分析需求即可。

如果打不开，先确认云厂商「安全组/防火墙」放行了 **8080** 端口：

```bash
# Ubuntu 用 ufw 的话
sudo ufw allow 8080/tcp
```

## 七、常用命令

```bash
docker compose logs -f <服务名>    # 看某个服务的日志（api/worker/frontend/mysql/redis）
docker compose restart api         # 重启后端
docker compose down                # 停止并删除容器（保留数据卷）
docker compose down -v             # 停止并删除容器 + 数据卷（清空 MySQL/Redis 数据，慎用）
docker compose up -d               # 再次启动（不重新构建）
```

## 八、数据与文件

- `outputs/`、`uploads/`、`chroma_data/` 以「绑定挂载」方式对应宿主机同名目录：生成的报告、上传的数据、向量库都直接落在项目目录里，方便查看和备份。
- MySQL 数据在命名卷 `mysql_data`、Redis 在 `redis_data`（用 `docker volume ls` 查看）。

## 九、升级 HTTPS / 绑定域名（可选）

先按上面的方式跑通。之后若买了域名、想要 HTTPS，可以在最前面加一层带 SSL 证书的 Nginx（或 Caddy）反代到本机的 `8080` 端口，这一步不影响现有架构。
