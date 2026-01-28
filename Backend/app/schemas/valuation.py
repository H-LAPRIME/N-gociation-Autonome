from pydantic import BaseModel

class MaintenanceHistory(BaseModel):
    service_book: str
    accident: str
    owners: int

class CarInput(BaseModel):
    brand_model: str
    year: int
    mileage_km: int
    condition: str
    maintenance_history: MaintenanceHistory

class PriceRange(BaseModel):
    min: int
    max: int

class ValuationOutput(BaseModel):
    state: int
    price_range: PriceRange
