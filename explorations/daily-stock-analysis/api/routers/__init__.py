"""__init__ for routers package."""
from api.routers.analysis import router as analysis_router  # noqa: F401
from api.routers.stocks import router as stocks_router  # noqa: F401
from api.routers.agent import router as agent_router  # noqa: F401
from api.routers.portfolio import router as portfolio_router  # noqa: F401
from api.routers.alerts import router as alerts_router  # noqa: F401
from api.routers.decision_signals import router as decision_signals_router  # noqa: F401
from api.routers.system_config import router as system_config_router  # noqa: F401
from api.routers.usage import router as usage_router  # noqa: F401
from api.routers.history import router as history_router  # noqa: F401
