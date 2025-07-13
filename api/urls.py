from ninja import NinjaAPI

from .routers.anime import router as anime_router
from .routers.auth import router as auth_router
from .routers.category import router as categories_router
from .routers.comment import router as comment_router
from .routers.gal import router as gal_router
from .routers.guest import router as guest_router
from .routers.health import router as health_router
from .routers.mail import router as mail_router
from .routers.page import router as page_router
from .routers.post import router as posts_router
from .routers.root import router as root_router

api = NinjaAPI()

api.add_router("/anime", anime_router)
api.add_router("/auth", auth_router)
api.add_router("/category", categories_router)
api.add_router("/comment", comment_router)
api.add_router("/gal", gal_router)
api.add_router("/guest", guest_router)
api.add_router("/health", health_router)
api.add_router("/mail", mail_router)
api.add_router("/page", page_router)
api.add_router("/post", posts_router)
api.add_router("/", root_router)
