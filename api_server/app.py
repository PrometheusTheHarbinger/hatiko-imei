from flask import Flask, request
import requests
import json
from hashlib import sha256

json_content = None
with open("statics.json") as f: # Concealing tokens and correct auth hashes
    json_content = json.load(f)
if not json_content:
    print("Could not load statics.json file")
    exit(1)
service_to_ask = None

app = Flask(__name__)

def is_service_found() -> bool:
    global service_to_ask
    if service_to_ask is None:
        response = requests.get("https://api.imeicheck.net/v1/services", headers={"Authorization": "Bearer " + json_content["token_imeicheck"]})
        for service in json.loads(response.content):
            if service["title"] == "Model + Brand + Manufacturer (by IMEI)": # Let's pick the simplest one, because other services require awareness about device manufacturer
                service_to_ask = service["id"]
        if service_to_ask is None:
            return False
    return True


@app.post("/api/check-imei")
def check():
    if sha256(request.values["token"].encode()).hexdigest() == json_content["auth_hash"]:
        if not is_service_found():
            return json.dumps({"failure": "Can not connect to database, please try again later"})
        response = requests.post("https://api.imeicheck.net/v1/checks", headers={"Authorization": "Bearer " + json_content["token_imeicheck"]}, data={"deviceId": request.values["imei"], "serviceId": service_to_ask})
        if response.status_code != 201:
            return json.dumps({"failure": "Error while fetching data from database, please try again later"})
        response = json.loads(response.content)
        if response["status"] == "successful":
            return json.dumps(response["properties"])
        else:
            return json.dumps({"failure": "IMEI was not found in the database"})
    else:
        return json.dumps({"failure": "Unauthorized"})
