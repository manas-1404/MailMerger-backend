from fastapi import FastAPI, APIRouter
from sqlalchemy import text
import logging

from app.routes.email_routes import email_router
from app.routes.login_routes import login_router
from app.routes.oauth_routes import oauth_router
from app.routes.auth_routes import auth_router
from app.pydantic_schemas.response_pydantic import ResponseSchema

from app.db.dbConnection import engine, SessionLocal
from app.models.base_model import Base
import app.models
from app.routes.template_routes import template_router
from app.routes.user_routes import user_router

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.include_router(oauth_router)
app.include_router(auth_router)
app.include_router(login_router)
app.include_router(user_router)
app.include_router(template_router)
app.include_router(email_router)

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}
#
# @app.get("/health")
# async def health_check():
#     return ResponseSchema(
#         status_code=200,
#         message="Service is running",
#         data={"status": "healthy"}
#     )
#
# @app.get("/hello/{name}")
# async def say_hello(name: str):
#     return {"message": f"Hello {name}"}
#
@app.on_event("startup")
async def db_create_tables():
    Base.metadata.create_all(bind=engine)

    try:
        db_session = SessionLocal()
        db_session.execute(text('SELECT 1'))
        logger.info("Database connection is successful.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    finally:
        db_session.close()

# INFO:     127.0.0.1:61889 - "GET /api/oauth/gmail-authorize?purpose=signup HTTP/1.1" 307 Temporary Redirect
# ['__abstractmethods__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_abc_impl', '_account', '_apply', '_blocking_refresh', '_client_id', '_client_secret', '_cred_file_path', '_default_scopes', '_enable_reauth_refresh', '_granted_scopes', '_id_token', '_make_copy', '_metric_header_for_usage', '_non_blocking_refresh', '_quota_project_id', '_rapt_token', '_refresh_handler', '_refresh_token', '_refresh_worker', '_scopes', '_token_uri', '_trust_boundary', '_universe_domain', '_use_non_blocking_refresh', 'account', 'apply', 'before_request', 'client_id', 'client_secret', 'default_scopes', 'expired', 'expiry', 'from_authorized_user_file', 'from_authorized_user_info', 'get_cred_info', 'granted_scopes', 'has_scopes', 'id_token', 'quota_project_id', 'rapt_token', 'refresh', 'refresh_handler', 'refresh_token', 'requires_scopes', 'scopes', 'to_json', 'token', 'token_state', 'token_uri', 'universe_domain', 'valid', 'with_account', 'with_non_blocking_refresh', 'with_quota_project', 'with_quota_project_from_environment', 'with_token_uri', 'with_universe_domain']
# {'token': 'ya29.a0AS3H6Nx920Fd9fZ8dmt7Efe2U7JW9aHN-oPyKVqJjZTeijMJMNrpk_W68d5yQwCMxIbbnidFeiRXWbpCaKJ3zQtr748a-_SmnUrfqntGGHJYKFrf96i2s9Sr7l37Z_lUl9EqLcLZ0Gm7Lt-W_P5WPRCDhjsRmtleYuSrwMAJaCgYKAUUSARcSFQHGX2MiZq343KG4yJqFEKaSwNwPDg0175', 'refresh_token': '1//03TI_3Gth-Mt7CgYIARAAGAMSNwF-L9IrrgKGF5hQXUvhJAbgbvds64pHgrWCwLDrJhda-Cy6jOONvgUbpwAi4oprmsnIaNuIaUQ', 'token_uri': 'https://oauth2.googleapis.com/token', 'client_id': '94652135329-nq3cttrqlk9qlq6003kmfn7biluq9g2t.apps.googleusercontent.com', 'client_secret': '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', 'granted_scopes': ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/gmail.send'], 'expiry': '2025-07-06 23:03:39.910377'}
