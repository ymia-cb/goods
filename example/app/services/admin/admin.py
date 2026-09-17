from example.app.respositories.admin.admin import AdminMetricsRepository


class AdminMetricsService:
    def __init__(self, repository: AdminMetricsRepository):
        self.repository = repository

    async def get_metrics(self) ->dict[str, int]:
        return await self.repository.get_metrics()
