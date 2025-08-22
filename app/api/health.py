from fastapi import APIRouter

router = APIRouter(tags=["根路径"])


@router.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "企业微信消息接收服务",
        "version": "1.0.0",
        "description": "专门用于接收企业微信自定义应用推送消息",
        "endpoints": {
            "wechat_callback": "/wechat/callback",
            "health": "/health"
        }
    }


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "企业微信消息接收服务"}
