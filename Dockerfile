FROM python:3.11-slim

LABEL org.opencontainers.image.title="Data Analysis Agent"
LABEL org.opencontainers.image.version="2.0.0"
LABEL org.opencontainers.image.description="企业级 LLM 驱动的智能数据分析代理"

# 系统依赖：build-essential 用于编译少量无 wheel 的依赖；中文字体用于 matplotlib 图表
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfreetype6-dev \
    libfontconfig1-dev \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制代码再安装（可编辑安装，让 daa 包从 /app 导入；只装运行时依赖，不带 dev）
COPY . .
RUN pip install --no-cache-dir -e .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# 运行时数据目录（实际由挂载卷提供）
RUN mkdir -p /app/outputs /app/uploads /app/chroma_data

EXPOSE 8000

# 默认启动 API 服务（worker 通过 docker-compose 的 command 覆盖）
CMD ["uvicorn", "daa.main:app", "--host", "0.0.0.0", "--port", "8000"]
