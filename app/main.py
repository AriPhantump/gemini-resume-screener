"""
应用入口点
"""
from fastapi import FastAPI
from app.api import routes

app = FastAPI(title="Resume Screener API", description="基于LLM的智能简历筛选系统 API")

# 包含API路由
app.include_router(routes.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Resume Screener API"}