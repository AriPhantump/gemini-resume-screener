# 本地简历筛选系统 (基于Gemini 2.5 Pro)

一个基于Google Gemini 2.5 Pro的智能简历筛选系统，专门用于筛选本地的PDF和DOCX格式简历文件。

## ✨ 功能特性

### 🎯 核心功能
- **本地文件处理**: 支持PDF和DOCX格式简历文件
- **智能文档解析**: 自动提取简历中的结构化信息
- **自然语言查询**: 支持自然语言描述的招聘需求
- **三层筛选算法**: 语义检索 → 硬性过滤 → 多维评分
- **智能分析**: 为每个候选人生成详细的匹配分析

### 🧠 AI能力
- **Gemini 2.5 Pro**: 使用最新的Gemini模型进行文本理解和生成
- **语义向量搜索**: 基于ChromaDB的高效语义检索
- **多维度评分**: 技能、经验、学历、薪资、地点等维度综合评估
- **智能缓存**: 避免重复处理，提升性能

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd resume_screening

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，设置Gemini API密钥
export GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. 准备简历文件

```bash
# 创建简历文件夹
mkdir resumes

# 将PDF或DOCX格式的简历文件放入该文件夹
# 支持子文件夹嵌套
```

### 4. 使用方法

#### 方法一：命令行界面 (推荐)

```bash
# 扫描简历文件
python cli.py scan ./resumes

# 解析查询条件
python cli.py query "需要5年以上Python经验的后端工程师"

# 执行完整筛选
python cli.py screen ./resumes "Python后端工程师，3年以上经验，本科学历" --top-k 5
```

#### 方法二：Python API

```python
from app.core.local_resume_screener import LocalResumeScreener

# 初始化筛选器
screener = LocalResumeScreener(
    resume_directories=["./resumes"],
    gemini_api_key="your_api_key"
)

# 扫描和处理简历
stats = screener.scan_and_process_resumes()
print(f"处理了 {stats['processed']} 份简历")

# 执行筛选
results = screener.screen_resumes(
    "需要Python后端工程师，5年经验", 
    top_k=10
)

# 查看结果
for candidate in results['candidates']:
    print(f"{candidate['name']} - 得分: {candidate['overall_score']:.2f}")
```

#### 方法三：交互式演示

```bash
# 运行演示脚本
python demo_local.py
```

## 📁 项目结构

```
resume_screening/
├── app/
│   ├── core/                          # 核心业务逻辑
│   │   ├── gemini_client.py           # Gemini客户端
│   │   ├── enhanced_document_parser.py # 文档解析器
│   │   ├── gemini_extractor.py        # 元数据提取
│   │   ├── gemini_query_parser.py     # 查询解析
│   │   ├── local_file_manager.py      # 文件管理
│   │   ├── local_resume_screener.py   # 主筛选器
│   │   └── ...                        # 其他核心模块
│   ├── models/                        # 数据模型
│   └── ...
├── resumes/                           # 简历文件夹
├── cache/                             # 缓存目录
├── vector_db/                         # 向量数据库
├── cli.py                             # 命令行接口
├── demo_local.py                      # 演示脚本
├── requirements.txt                   # 依赖包
└── .env.example                       # 环境变量模板
```

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `GEMINI_API_KEY` | Gemini API密钥 | `your_api_key_here` |
| `RESUME_DIRECTORIES` | 简历文件夹路径 | `/path/to/resumes` |
| `CACHE_DIRECTORY` | 缓存目录 | `./cache` |
| `VECTOR_DB_DIRECTORY` | 向量数据库目录 | `./vector_db` |

### 支持的文件格式

- **PDF**: `.pdf`
- **DOCX**: `.docx`
- **DOC**: `.doc` (有限支持)

## 🎯 使用示例

### 1. 基本筛选

```bash
python cli.py screen ./resumes "Python开发工程师，3年经验" --top-k 5
```

### 2. 复杂查询

```bash
python cli.py screen ./resumes \
  "需要高级Java后端工程师，5年以上经验，熟悉Spring框架，本科以上学历，期望薪资20-30K，工作地点北京或上海" \
  --top-k 10
```

### 3. 批量处理

```bash
# 扫描多个文件夹
python cli.py scan ./resumes ./more_resumes ./archived_resumes

# 导出结果
python cli.py screen ./resumes "数据科学家" --export results.json
```

## 📊 筛选算法

### 三层筛选流程

1. **语义检索**: 使用向量相似度进行初步筛选
2. **硬性过滤**: 根据经验年限、学历等硬性条件过滤
3. **多维评分**: 综合评估并排序

### 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 技能匹配 | 30% | 必需技能与优先技能的匹配度 |
| 行业经验 | 20% | 相关行业工作经验 |
| 地理位置 | 20% | 工作地点偏好匹配 |
| 学历要求 | 10% | 教育背景匹配 |
| 薪资匹配 | 10% | 期望薪资与预算匹配 |
| 关键标签 | 10% | 其他关键特征匹配 |

## 🔍 高级功能

### 1. 缓存机制

系统会自动缓存以下内容：
- 文档解析结果
- 元数据提取结果
- 向量化结果

### 2. 文件监控

可以监控文件夹变化，自动处理新增的简历文件：

```python
# 启用文件监控 (开发中)
screener.start_file_monitoring()
```

### 3. 批量导出

支持多种格式的结果导出：

```bash
# JSON格式
python cli.py screen ./resumes "查询条件" --export results.json

# 文本格式
python cli.py screen ./resumes "查询条件" --export results.txt
```

## 🐛 故障排除

### 常见问题

1. **API密钥错误**
   ```
   解决: 检查GEMINI_API_KEY环境变量是否正确设置
   ```

2. **文件解析失败**
   ```
   解决: 确保文件格式为PDF或DOCX，且文件未损坏
   ```

3. **没有找到简历**
   ```
   解决: 检查文件路径是否正确，确保文件有读取权限
   ```

4. **内存不足**
   ```
   解决: 减少批处理文件数量，或增加系统内存
   ```

### 调试模式

```bash
# 启用详细日志
python cli.py --log-level DEBUG screen ./resumes "查询条件"
```

## 📈 性能优化

### 建议配置

- **内存**: 建议8GB以上
- **存储**: SSD硬盘，提升文件读取速度
- **网络**: 稳定的网络连接（API调用）

### 优化技巧

1. **使用缓存**: 避免重复处理相同文件
2. **批量处理**: 一次性处理多个文件
3. **合理设置top_k**: 避免处理过多候选人

## 🤝 贡献指南

欢迎提交Issues和Pull Requests！

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black app/
```

## 📄 许可证

MIT License

## 🙏 致谢

- Google Gemini API
- ChromaDB
- FastAPI
- 所有开源贡献者

---

**注意**: 请确保遵守相关法律法规，在处理简历数据时保护个人隐私。