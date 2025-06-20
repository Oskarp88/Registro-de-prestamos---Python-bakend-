

from json import dumps
from fastapi.encoders import jsonable_encoder
from database.connection import get_db
from utils.constants import Constants
from utils.erialize_notifications import serialize_notifications
from websocket_manager.manager import manager
from datetime import datetime

from bson import ObjectId

async def notify_latest_notifications():
    print(f"🔔 Ejecutando notify_latest_notifications() {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    db = get_db()
    notifications_collection = db[Constants.NOTIFICATIONS]
    print(f"📡 Notificando a {len(manager.client_sockets)} sockets activos")
    for user_id, socket in manager.client_sockets.items():
        cursor = notifications_collection.find().sort("creation_date", -1).limit(100)
        notifications = await cursor.to_list(length=100)

       

        # Convertir ObjectId a string en cada notificación
        notifications_serializable = []
        for notif in notifications:
            notif['_id'] = str(notif['_id'])
            # Si tienes más campos ObjectId en notif, conviértelos también:
            if 'client_id' in notif and isinstance(notif['client_id'], ObjectId):
                notif['client_id'] = str(notif['client_id'])
            # También si tienes read_by con ObjectId, conviértelos igual (si aplica)
            notifications_serializable.append(notif)

        unread_count = sum(
            1 for notif in notifications_serializable if user_id not in notif.get("read_by", [])
        )

        notifications_serializable = serialize_notifications(notifications_serializable)

        payload = {
            "type": "notifications",
            "notifications": notifications_serializable,
            "unread_count": unread_count
        }

        await manager.send_personal_message(dumps(payload), socket)
