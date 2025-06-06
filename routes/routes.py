from fastapi import APIRouter
from routes import user_route, loan_routes, route_auth

api_router = APIRouter()

# Auth routes
api_router.include_router(route_auth.route_auth, prefix="/api/auth", tags=["Auth"])
# User routes
api_router.include_router(user_route.user_router, prefix="/api/user", tags=["User"])
# loans routes
api_router.include_router(loan_routes.loans_router, prefix="/api/loan", tags=["Loan"])
