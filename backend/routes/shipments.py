from fastapi import APIRouter, Body, Depends, HTTPException
from typing import List
from backend.models.shipment import ShipmentSchema
from backend.config.database import shipment_collection
from backend.middleware.security import JWTBearer
from fastapi import HTTPException
import re

router = APIRouter()

@router.post("/shipments", dependencies=[Depends(JWTBearer())])
async def create_shipment(shipment: ShipmentSchema = Body(...)):
    # Validate shipment number format and uniqueness
    shipment_number = shipment.Shipment_Number
    if not shipment_number or not re.match(r'^[A-Z0-9\-_]+$', shipment_number):
        raise HTTPException(status_code=400, detail="Invalid Shipment_Number format. Use alphanumerics, hyphens or underscores.")

    existing = await shipment_collection.find_one({"Shipment_Number": shipment_number})
    if existing:
        raise HTTPException(status_code=400, detail="Shipment_Number already exists")

    shipment_dict = shipment.dict()
    if shipment_dict.get("Expected_Delivery_Date"):
        shipment_dict["Expected_Delivery_Date"] = shipment_dict["Expected_Delivery_Date"].isoformat()
        
    await shipment_collection.insert_one(shipment_dict)
    return {"message": "Shipment created successfully"}

@router.get("/shipments", dependencies=[Depends(JWTBearer())])
async def get_shipments():
    shipments = []
    # Fetch all shipments
    async for shipment in shipment_collection.find():
        # IMPORTANT: Convert ObjectId to string to prevent JSON errors
        shipment["_id"] = str(shipment["_id"])
        shipments.append(shipment)
    return shipments

