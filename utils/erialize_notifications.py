from datetime import datetime

def serialize_notifications(notifications):
    serialized = []
    for notif in notifications:
        notif = dict(notif)  # copia para no mutar el original
        for key, value in notif.items():
            if isinstance(value, datetime):
                notif[key] = value.isoformat()
        serialized.append(notif)
    return serialized
