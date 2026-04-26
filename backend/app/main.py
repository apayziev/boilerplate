from .api import router
from .core.config import settings
from .core.setup import create_application, lifespan_factory

app = create_application(router=router, settings=settings, lifespan=lifespan_factory(settings))
