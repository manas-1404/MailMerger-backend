import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, HTTPException, Depends
from google.auth.transport.requests import AuthorizedSession
from sqlalchemy.orm import Session

from app.routes.constant_routes import GOOGLE_CLIENT_SECRETS_FILE, SCOPES, REDIRECT_URI

from app.auth.dependency_auth import create_jwt_token, create_jwt_refresh_token
from app.utils.utils import credentials_to_dict
from app.db.dbConnection import SessionLocal, get_db_session
from app.models.user_models import User
from app.models.user_token_models import UserToken

oauth_router = APIRouter(
    prefix="/api/oauth",
    tags=["OAuth"]
)

# this method is used when the frontend requests for sign-in using google or when the user wants to give access to google
# this method will only create the google oauth consent url, include all the information about the client (app), redirects etc
# this method will return the google consent url to the frontend, which will redirect the user to the google consent page
# it will also include state parameter as cookie to verify the response from google later
@oauth_router.get("/gmail-authorize")
async def gmail_authorize(request: Request):
    """
    Endpoint to initiate Gmail OAuth authorization.
    This will redirect the user to the Google authorization page.
    """
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = str(request.base_url) + "api/oauth/oauth2callback"

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true'
    )

    # Store the state so the callback can verify the auth server response.
    response = RedirectResponse(url=authorization_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False,  # Set to True in production
    )

    return response


@oauth_router.get('/oauth2callback', name='oauth2callback')
def oauth2callback(request: Request, db_connection: Session = Depends(get_db_session)):
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    returned_state = request.query_params.get('state')
    stored_state = request.cookies.get('oauth_state')


    if returned_state != stored_state:
        raise HTTPException(status_code=400, detail="State mismatch. Possible CSRF attack.")


    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE, scopes=SCOPES, state=returned_state)

    flow.redirect_uri = str(request.base_url) + "api/oauth/oauth2callback"

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = str(request.url)

    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials

    print(dir(credentials))

    credentials_dict = credentials_to_dict(credentials)
    print(credentials_dict)


    authed_session = AuthorizedSession(credentials)
    userinfo = authed_session.get("https://www.googleapis.com/oauth2/v2/userinfo").json()


    new_user = User(name=userinfo['name'], email=userinfo['email'], password="oauth_google", resume=None, cover_letter=None)

    db_connection.add(new_user)

    db_connection.flush()

    jwt_refresh_token = create_jwt_refresh_token(data=new_user.uid)

    db_connection.query(User).filter(User.uid == new_user.uid).update({User.refresh_token: jwt_refresh_token})


    #store the user tokens in the db
    new_user_token = UserToken(access_token=credentials_dict['token'],
                                   refresh_token=credentials_dict['refresh_token'],
                                   token_type='Google',
                                   expires_at=credentials_dict['expiry'],
                                   uid=new_user.uid)

    db_connection.add(new_user_token)

    db_connection.commit()


    redirected_response = RedirectResponse(
        url="http://localhost:5173/dashboard",
        status_code=302
    )

    redirected_response.set_cookie(
        key="refresh_token",
        value=jwt_refresh_token,
        httponly=True,
        secure=False,  # Set to True in production
        samesite="Strict",
        max_age=60 * 60 * 24 * 7  # 7 days
    )


    return redirected_response
