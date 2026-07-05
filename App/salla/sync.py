from datetime import datetime

from App import crud
from App.salla.client import get_store_info, SallaApiError


def sync_store_info(db, store):
    try:
        store_info = get_store_info(store, db)
    except SallaApiError:
        return store

    return crud.update_store_from_salla(
        db=db,
        store=store,
        data=store_info
    )


def mark_store_synced(db, store):
    store.last_platform_sync = datetime.utcnow()
    store.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(store)
    return store