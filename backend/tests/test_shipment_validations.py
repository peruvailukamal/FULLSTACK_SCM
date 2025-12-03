import pytest
from datetime import datetime
from fastapi import HTTPException
from backend.routes.shipments import create_shipment
from backend.models.shipment import ShipmentSchema


class Dummy:
    async def find_one(self, q):
        return None

    async def insert_one(self, doc):
        return None


@pytest.mark.asyncio
async def test_invalid_shipment_number_format():
    shipment = ShipmentSchema(
        Shipment_Number="shp#1",
        Route_Details="A->B",
        Device="dev",
        Po_Number="PO1",
        NDC_Number="NDC1",
        Serial_Number_of_Goods="SN1",
        Container_number="C1",
        Goods_Type="Type",
        Expected_Delivery_Date=datetime.utcnow()
    )

    # Should raise HTTPException for invalid format
    with pytest.raises(HTTPException):
        await create_shipment(shipment)


@pytest.mark.asyncio
async def test_duplicate_shipment_number(monkeypatch):
    # monkeypatch the shipment_collection to return an existing doc
    class Found:
        async def find_one(self, q):
            return {"Shipment_Number": "SHP-1001"}
    monkeypatch.setattr('backend.routes.shipments.shipment_collection', Found())

    shipment = ShipmentSchema(
        Shipment_Number="SHP-1001",
        Route_Details="A->B",
        Device="dev",
        Po_Number="PO1",
        NDC_Number="NDC1",
        Serial_Number_of_Goods="SN1",
        Container_number="C1",
        Goods_Type="Type",
        Expected_Delivery_Date=datetime.utcnow()
    )

    with pytest.raises(HTTPException):
        await create_shipment(shipment)


@pytest.mark.asyncio
async def test_create_shipment_success(monkeypatch):
    class Empty:
        async def find_one(self, q):
            return None
        async def insert_one(self, doc):
            return None
    monkeypatch.setattr('backend.routes.shipments.shipment_collection', Empty())

    shipment = ShipmentSchema(
        Shipment_Number="SHP1002",
        Route_Details="A->B",
        Device="dev",
        Po_Number="PO1",
        NDC_Number="NDC1",
        Serial_Number_of_Goods="SN1",
        Container_number="C1",
        Goods_Type="Type",
        Expected_Delivery_Date=datetime.utcnow()
    )

    resp = await create_shipment(shipment)
    assert resp == {"message": "Shipment created successfully"}
