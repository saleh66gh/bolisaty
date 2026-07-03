from datetime import datetime, timedelta
from App import crud


def get_merchant_id(payload: dict):
    return str(
        payload.get("merchant")
        or payload.get("merchant_id")
        or payload.get("data", {}).get("merchant")
        or payload.get("data", {}).get("merchant_id")
        or ""
    )


def handle_salla_event(db, payload: dict):
    event = payload.get("event")
    merchant_id = get_merchant_id(payload)

    if not event:
        return {"success": False, "message": "Missing event"}

    if not merchant_id:
        return {"success": False, "message": "Missing merchant id"}

    if event in ["app.installed", "app.store.authorize"]:
        return handle_store_connected(db, payload, merchant_id)

    if event == "app.uninstalled":
        return handle_store_uninstalled(db, merchant_id)

    if event == "app.trial.started":
        return handle_trial_started(db, payload, merchant_id)

    if event == "app.trial.expired":
        return handle_trial_expired(db, merchant_id)

    if event in ["app.subscription.started", "app.subscription.renewed"]:
        return handle_subscription_started(db, payload, merchant_id)

    if event == "app.subscription.canceled":
        return handle_subscription_canceled(db, merchant_id)

    return {"success": True, "message": f"Event ignored: {event}"}


def handle_store_connected(db, payload: dict, merchant_id: str):
    store = crud.get_store_by_salla_id(db, merchant_id)

    if not store:
        store = crud.create_salla_store(
            db=db,
            salla_store_id=merchant_id,
            store_name=f"متجر سلة {merchant_id}",
            owner_name="مالك المتجر",
        )

        crud.create_default_owner_for_store(db, store)
        crud.create_default_sender_for_store(db, store)

    data = payload.get("data", {})

    store.salla_connected = True
    store.is_active = True
    store.salla_access_token = data.get("access_token") or store.salla_access_token
    store.salla_refresh_token = data.get("refresh_token") or store.salla_refresh_token
    store.subscription_plan = store.subscription_plan or "trial"
    store.subscription_status = store.subscription_status or "active"

    if not store.subscription_start:
        store.subscription_start = datetime.utcnow()
    if not store.subscription_end:
        store.subscription_end = datetime.utcnow() + timedelta(days=30)

    db.commit()
    db.refresh(store)

    return {"success": True, "message": "Store connected", "store_id": store.id}


def handle_store_uninstalled(db, merchant_id: str):
    store = crud.get_store_by_salla_id(db, merchant_id)
    if store:
        store.salla_connected = False
        store.is_active = False
        store.subscription_status = "uninstalled"
        db.commit()

    return {"success": True, "message": "Store uninstalled"}


def handle_trial_started(db, payload: dict, merchant_id: str):
    store = crud.get_store_by_salla_id(db, merchant_id)
    if not store:
        return {"success": False, "message": "Store not found"}

    data = payload.get("data", {})

    store.subscription_plan = data.get("plan_name") or "trial"
    store.subscription_status = "trial"
    store.subscription_start = parse_date(data.get("start_date")) or datetime.utcnow()
    store.subscription_end = parse_date(data.get("end_date")) or datetime.utcnow() + timedelta(days=30)

    db.commit()
    return {"success": True, "message": "Trial started"}


def handle_trial_expired(db, merchant_id: str):
    store = crud.get_store_by_salla_id(db, merchant_id)
    if store:
        store.subscription_status = "trial_expired"
        db.commit()

    return {"success": True, "message": "Trial expired"}


def handle_subscription_started(db, payload: dict, merchant_id: str):
    store = crud.get_store_by_salla_id(db, merchant_id)
    if not store:
        return {"success": False, "message": "Store not found"}

    data = payload.get("data", {})

    store.subscription_plan = data.get("plan_type") or data.get("plan_name") or "paid"
    store.subscription_status = "active"
    store.subscription_start = parse_date(data.get("start_date")) or datetime.utcnow()
    store.subscription_end = parse_date(data.get("end_date"))

    db.commit()
    return {"success": True, "message": "Subscription active"}


def handle_subscription_canceled(db, merchant_id: str):
    store = crud.get_store_by_salla_id(db, merchant_id)
    if store:
        store.subscription_status = "canceled"
        db.commit()

    return {"success": True, "message": "Subscription canceled"}


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None