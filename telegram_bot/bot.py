from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
import json
import requests

json_content = None
with open("statics.json") as f:
    json_content = json.load(f)
if not json_content:
    print("Could not load statics.json file")
    exit(1)

def is_user_valid(user) -> bool:
    return user is not None and user.id in json_content["whitelist"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_user_valid(update.effective_user):
        await update.message.reply_text(json_content["welcome"])
    else:
        await update.message.reply_text(json_content["go_away"])

async def imei_sent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_user_valid(update.effective_user):
        imei = update.effective_message.text
        if len(imei) == 16 or (len(imei) == 15 and luhn(imei)):
            data = {
                "token": json_content["token_flask"],
                "imei": imei
            }
            response = requests.post("http://localhost:5000/api/check-imei", data=data)
            response = json.loads(response.content)
            if "failure" in response:
                await update.message.reply_text(response["failure"])
            else:
                await update.message.reply_text("Device name: {dev_name}\nBrand: {brand}\nManufacturer: {manufacturer}".format(dev_name=response["deviceName"], brand=response["brand"], manufacturer=response["manufacturer"]))
        else:
            await update.message.reply_text("IMEI provided is incorrect")
    else:
        await update.message.reply_text(json_content["go_away"])

def luhn(s) -> bool:
    sum = 0
    for i, ch in enumerate(s):
        ich = int(ch)
        if i % 2 == 0:
            sum += ich
        else:
            sum += ich * 2 if ich * 2 < 10 else ich * 2 - 9
    return sum % 10 == 0

app = ApplicationBuilder().token(json_content["token_bot"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(None, imei_sent))

app.run_polling()
