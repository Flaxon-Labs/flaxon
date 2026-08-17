from flaxon import Flaxon
from flaxon.validation import Schema, fields

app = Flaxon("android-backend")


class DeviceRegistration(Schema):
    device_id = fields.StrField(required=True, min_length=8)
    platform = fields.ChoiceField(["android"], required=True)
    notification_token = fields.StrField(required=True, min_length=16)


@app.post("/api/v1/devices")
async def register_device(data: DeviceRegistration):
    return {
        "success": True,
        "device": data.to_dict(),
    }
