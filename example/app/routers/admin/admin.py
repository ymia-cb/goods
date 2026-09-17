from fastapi import APIRouter

from example.app.dependencies import get_auth_service, AdminMetricsServiceDep
from example.app.schemas.admin.admin import AdminMetricsResponse

router = APIRouter(tags=["管理员路由"], prefix="/api/v1/admin")

@router.get("/metrics", response_model=AdminMetricsResponse)
async def get_admin_metrics(metrics_service: AdminMetricsServiceDep, authrization: str):
    get_auth_service().get_authorized_user(authrization, "admin")
    return await metrics_service.get_metrics()