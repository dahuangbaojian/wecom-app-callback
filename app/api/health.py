from fastapi import APIRouter

router = APIRouter(tags=["根路径"])


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "企业微信消息接收服务"}
