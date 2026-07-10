FROM python:3.13-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/exports

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "data_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
