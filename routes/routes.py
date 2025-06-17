from fastapi import APIRouter
from routes import account_routes, user_route, loan_routes, route_auth

api_router = APIRouter()

# Auth routes
api_router.include_router(route_auth.route_auth, prefix="/api/auth", tags=["Auth"])
# User routes
api_router.include_router(user_route.user_router, prefix="/api/user", tags=["User"])
# loans routes
api_router.include_router(loan_routes.loans_router, prefix="/api/loan", tags=["Loan"])
# account routes
api_router.include_router(account_routes.accounts_router, prefix="/api/account", tags=["Account"])
