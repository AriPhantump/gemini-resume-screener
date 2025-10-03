# 本地简历筛选系统 (基于Gemini 2.5 Pro)

🎯 **一个基于Google Gemini 2.5 Pro的智能简历筛选系统，专门用于筛选本地的PDF和DOCX格式简历文件。**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Pro-green.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 功能特性

### 🎯 核心功能
- **📁 本地文件处理**: 支持PDF和DOCX格式简历文件
- **🧠 智能文档解析**: 自动提取简历中的结构化信息
- **💬 自然语言查询**: 支持自然语言描述的招聘需求
- **🔍 三层筛选算法**: 语义检索 → 硬性过滤 → 多维评分
- **📊 智能分析**: 为每个候选人生成详细的匹配分析

### 🧠 AI能力
- **🤖 Gemini 2.5 Pro**: 使用最新的Gemini模型进行文本理解和生成
- **🔎 语义向量搜索**: 基于ChromaDB的高效语义检索
- **📈 多维度评分**: 技能、经验、学历、薪资、地点等维度综合评估
- **⚡ 智能缓存**: 避免重复处理，提升性能

## 项目结构

```
resume_screening/
├── app/                  # 主应用代码
│   ├── api/              # API路由和接口定义
│   ├── core/             # 核心业务逻辑 (如解析、检索、评分)
│   ├── models/           # 数据模型 (Pydantic/SQL)
│   ├── utils/            # 工具函数和辅助类
│   └── main.py           # 应用入口点
├── data/                 # 数据文件 (如简历样本、模型缓存)
├── cache/                # 缓存文件
├── chroma_db/            # 向量数据库
├── config/               # 配置文件 (如环境变量、系统设置)
├── notebooks/            # 探索性数据分析和原型开发 Jupyter Notebook
├── tests/                # 单元测试和集成测试
├── requirements.txt      # Python 依赖包列表
├── Dockerfile           # Docker配置文件
├── .env.example         # 环境变量示例文件
└── README.md            # 项目说明文件 (即本文件)
```

## 快速开始

### 环境准备

1.  **克隆项目代码** (如果适用)
2.  **创建虚拟环境**:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    # source venv/bin/activate
    ```
3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

### 配置环境变量

复制 `.env.example` 文件并重命名为 `.env`，然后填写相应的配置信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写你的OpenAI API密钥和其他配置：

```
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_openai_api_key
```

### 运行应用

```bash
# 开发模式运行
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式运行
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_core_modules.py -v
```

## 使用Docker部署

### 构建Docker镜像

```bash
docker build -t resume-screening .
```

### 运行Docker容器

```bash
docker run -d \
  --name resume-screening \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/chroma_db:/app/chroma_db \
  --env-file .env \
  resume-screening
```

## API接口

### 健康检查

```
GET /api/v1/health
```

检查系统是否正常运行。

**响应示例：**
```json
{
  "status": "ok"
}
```

### 上传简历

```
POST /api/v1/resumes
```

上传一份简历文件（PDF格式）进行处理和索引。

**请求参数：**
- `file` (form-data): 简历文件，支持PDF格式

**响应示例：**
```json
{
  "resume_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
  "message": "简历 'zhangsan_resume.pdf' 上传成功"
}
```

### 提交筛选查询

```
POST /api/v1/queries
```

提交自然语言形式的筛选查询。

**请求体：**
```json
{
  "query_text": "寻找3年以上经验的Python后端工程师，熟悉Django框架，有互联网公司工作经验，期望薪资20K以上"
}
```

**响应示例：**
```json
{
  "query_id": "q1w2e3r4-t5y6-7890-u1i2-o3p4q5r6s7t8",
  "message": "查询提交成功"
}
```

### 获取筛选结果

```
GET /api/v1/results/{query_id}
```

根据查询ID获取筛选结果。

**路径参数：**
- `query_id` (string): 查询ID

**响应示例：**
```json
{
  "query_id": "q1w2e3r4-t5y6-7890-u1i2-o3p4q5r6s7t8",
  "query_text": "寻找3年以上经验的Python后端工程师，熟悉Django框架，有互联网公司工作经验，期望薪资20K以上",
  "total_candidates": 1,
  "candidates": [
    {
      "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
      "rank": 1,
      "name": "张三",
      "email": "zhangsan@example.com",
      "phone": "13800138000",
      "overall_score": 0.95,
      "skill_scores": [
        {
          "name": "Python",
          "score": 0.9
        }
      ],
      "work_experience": [
        {
          "company": "互联网公司",
          "title": "软件工程师",
          "start_date": "2020-01",
          "end_date": "2023-12",
          "description": "负责后端开发工作"
        }
      ],
      "education": [
        {
          "institution": "清华大学",
          "major": "计算机科学与技术",
          "degree": "本科",
          "start_date": "2016-09",
          "end_date": "2020-06"
        }
      ],
      "skills": ["Python", "Django", "MySQL"],
      "expected_salary": "20K-30K",
      "preferred_locations": ["北京"],
      "analysis": "这是一位经验丰富的Python开发者..."
    }
  ],
  "created_at": "2025-08-11T10:30:00"
}
```

### 获取简历详情

```
GET /api/v1/resumes/{resume_id}
```

根据简历ID获取简历详细信息。

**路径参数：**
- `resume_id` (string): 简历ID

**响应示例：**
```json
{
  "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
  "filename": "zhangsan_resume.pdf",
  "text": "张三的简历内容...",
  "metadata": {
    "name": "张三",
    "email": "zhangsan@example.com",
    "skills": ["Python", "Django"]
  },
  "created_at": "2025-08-11T10:30:00"
}
```

## 配置

系统配置项应定义在 `config/` 目录下。通常包括：
- LLM API 密钥
- 向量数据库连接信息
- 文件存储路径
- 日志级别

## 开发指南

### 添加新的核心模块

1. 在 `app/core/` 目录下创建新的模块文件
2. 实现模块功能
3. 添加相应的测试文件到 `tests/` 目录
4. 更新API路由以集成新模块

### 扩展API接口

1. 在 `app/api/models.py` 中添加新的数据模型
2. 在 `app/api/routes.py` 中添加新的路由
3. 添加相应的测试

### 遵循的开发规范

- 遵循 [PEP 8](https://pep8.org/) Python 代码风格指南。
- 为新功能编写单元测试。
- 使用类型提示 (Type Hints)。
- 通过 Pull Request 进行代码贡献。

## 许可证

MIT License