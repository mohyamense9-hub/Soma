from telethon import TelegramClient, events
import requests

api_id = 38460443        # حط هنا api_id
api_hash = "5ee35420f38f9fe6915f3606fb353fb9"  # حط هنا api_hash
source_group = -1003808609180  # ID الجروب الخاص

client = TelegramClient("otp", api_id, api_hash)

@client.on(events.NewMessage(chats=source_group))
async def handler(event):
    text = event.message.message  # الرسالة النصية
    if text:
        try:
            requests.post(
                "http://127.0.0.1:5000/otp",
                json={"msg": text}
            )
        except Exception as e:
            print("Error sending OTP:", e)

client.start()
client.run_until_disconnected()
