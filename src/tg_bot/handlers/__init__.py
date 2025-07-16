from .basic import basic_router
from .register import register_router
from .profile import profile_router
from .general import general_router
from .subscription import subscription_router
from .horoscope import horoscope_router
from .events import event_router

from middleware.cancelation import DeclineMiddleware

all_routers = (
    basic_router, profile_router, register_router,
    subscription_router, horoscope_router, event_router,
    general_router
)

# register middleware
for router in all_routers:
    router.message.middleware.register(DeclineMiddleware())
    router.callback_query.middleware.register(DeclineMiddleware())