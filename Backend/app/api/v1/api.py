from fastapi import APIRouter, Query

from app.tools import sql_inventory
from app.api.v1.endpoints import market

router = APIRouter()

# Include the market router
router.include_router(market.router)




