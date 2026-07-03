from fastapi import HTTPException

from App import crud
from App.db_models import LabelTemplate
from App.label_generator import generate_shipping_label
from App.salla.models import SallaShipmentPayloadData
from App.salla.mapper import map_salla_to_label_data
from App.logger import logger


def get_salla_merchant_id(payload: dict) -> str:
    return str(
        payload.get("merchant")
        or payload.get("merchant_id")
        or payload.get("data", {}).get("merchant")
        or payload.get("data", {}).get("merchant_id")
        or ""
    )


def handle_shipment_creating(db, payload: dict):
    merchant_id = get_salla_merchant_id(payload)

    if not merchant_id:
        raise HTTPException(status_code=400, detail="Missing merchant id")

    store = crud.get_store_by_salla_id(db, merchant_id)

    if not store:
        raise HTTPException(status_code=404, detail="Store not connected")

    if not store.is_active:
        raise HTTPException(status_code=403, detail="Store is inactive")

    raw_data = payload.get("data", payload)
    data = SallaShipmentPayloadData(**raw_data)

    shipment = data.shipments[0] if data.shipments else None
    ship_from = shipment.ship_from.model_dump() if shipment and shipment.ship_from else {}

    sender = crud.get_or_create_sender_from_salla(
        db=db,
        store=store,
        ship_from=ship_from,
    )

    template = None

    if store.default_template_id:
        template = crud.get_label_template_by_id(db, store.default_template_id)

    if not template:
        template = db.query(LabelTemplate).filter(
            LabelTemplate.is_active == True
        ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    label_data = map_salla_to_label_data(
        data=data,
        sender_id=sender.id,
        template_id=template.id,
    )

    generate_shipping_label(
        data=label_data,
        sender=sender,
        store=store,
        template_html=template.html_code,
    )

    tracking_number = label_data.order_number

    response = {
        "success": True,
        "data": {
            "tracking_number": tracking_number,
            "tracking_link": tracking_number,
            "label_url": f"https://api.bolisaty.me/download-label/{label_data.order_number}",
        }
    }

    print("===== SALLA RESPONSE =====")
    print(response)

    return response