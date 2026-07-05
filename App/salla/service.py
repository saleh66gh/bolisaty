from datetime import datetime, timedelta
from App import crud
from App.salla.sync import sync_store_info
def parse_date(value):
    if not value:
        return None

    try:
        if isinstance(value, dict):
            value = value.get("date") or value.get("datetime") or ""

        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).replace(tzinfo=None)

    except Exception:
        return None


def get_merchant_id(payload: dict) -> str:
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
        return update_subscription_status(db, merchant_id, "trial_expired")

    if event in ["app.subscription.started", "app.subscription.renewed"]:
        return handle_subscription_active(db, payload, merchant_id)

    if event == "app.subscription.canceled":
        return update_subscription_status(db, merchant_id, "canceled")

    return {"success": True, "message": f"Event ignored: {event}"}


def handle_store_connected(db, payload: dict, merchant_id: str):
    data = payload.get("data", {}) or {}

    store = crud.get_store_by_salla_id(db, merchant_id)

    if not store:
        store = crud.create_salla_store(
            db=db,
            salla_store_id=merchant_id,
            store_name=data.get("store_name") or data.get("name") or f"متجر سلة {merchant_id}",
            owner_name=data.get("owner_name") or data.get("merchant_name") or "مالك المتجر",
        )

        crud.create_default_owner_for_store(db, store)

    store.salla_store_id = merchant_id
    store.salla_connected = True
    store.is_active = True

    store.salla_access_token = data.get("access_token") or store.salla_access_token
    store.salla_refresh_token = data.get("refresh_token") or store.salla_refresh_token

    crud.update_store_subscription(
        db=db,
        store=store,
        plan=data.get("plan_name") or "trial",
        status="trial",
        start=parse_date(data.get("start_date")) or datetime.utcnow(),
        end=parse_date(data.get("end_date")) or datetime.utcnow() + timedelta(days=30),
    )
    db.commit()
    db.refresh(store)
    sync_store_info(db, store)

    return {
        "success": True,
        "message": "Store connected",
        "store_id": store.id,
        "salla_store_id": store.salla_store_id
    }


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

    data = payload.get("data", {}) or {}
    crud.update_store_subscription(
        db=db,
        store=store,
        plan=data.get("plan_name") or "trial",
        status="trial",
        start=parse_date(data.get("start_date")) or datetime.utcnow(),
        end=parse_date(data.get("end_date")) or datetime.utcnow() + timedelta(days=30),
    )
    db.commit()

    return {"success": True, "message": "Trial started"}


def handle_subscription_active(db, payload: dict, merchant_id: str):
    store = crud.get_store_by_salla_id(db, merchant_id)

    if not store:
        return {"success": False, "message": "Store not found"}

    data = payload.get("data", {}) or {}

    crud.update_store_subscription(
        db=db,
        store=store,
        plan=data.get("plan_type") or data.get("plan_name") or "paid",
        status="active",
        start=parse_date(data.get("start_date")) or store.subscription_start,
        end=parse_date(data.get("end_date")),
    )
    db.commit()

    return {"success": True, "message": "Subscription active"}


def update_subscription_status(db, merchant_id: str, status: str):
    store = crud.get_store_by_salla_id(db, merchant_id)

    if store:
        crud.update_store_subscription(
            db=db,
            store=store,
            status=status,
        )
        db.commit()

    return {"success": True, "message": f"Subscription status: {status}"}