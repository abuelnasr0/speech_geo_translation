from fastapi import FastAPI, UploadFile, File, Form
import os
import uuid

# from utils.dummy_transcriper import DummyTranscriper
from .utils.transcriper import Transcriper, Language

# from .utils.spelling_corrector import SpellingCorrector
from .utils.spelling_cprrecter_new import SpellingCorrectorNew
from .utils.location_classifier import LocationClassifier
from .utils.address_translator import AddressTranslator
from .database.database_api import DatabaseAPI

transcriber = Transcriper()
address_corrector = SpellingCorrectorNew()
address_translator = AddressTranslator(
    api_key="AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
)
location_classifier = LocationClassifier()
db_api = DatabaseAPI()


app = FastAPI()

# Create a directory to save uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def geocode(filename, lang):
    print("lang", lang)

    address = transcriber.transcribe(filename, lang)
    print(address)
    corrected_address = address
    # if lang != "English":
    #     corrected_address = address_corrector(address)
    #     print(corrected_address)
    location = address_translator(corrected_address)
    print(location)
    if location == None:
        raise RuntimeError("Can't found this address")
    location_class = location_classifier((location["latitude"], location["longitude"]))
    location.update({"service_area_id": location_class["ssec_id"]})
    db_api.add_complaint(**location)

    if lang != "English":
        return address, location, location_class
    else:
        return address, location, location_class


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), lang: str = Form(...)):
    # Save the file
    print("lang", lang)
    uuid3 = str(uuid.uuid3(uuid.NAMESPACE_DNS, file.filename))
    print(uuid3)

    with open(os.path.join(UPLOAD_DIR, uuid3 + ".wav"), "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        address, location, location_class = geocode(
            os.path.join(UPLOAD_DIR, uuid3 + ".wav"), lang
        )
    except Exception as e:
        return {
            "message": "Not Found",
            "error_message": e,
        }

    os.remove(os.path.join(UPLOAD_DIR, uuid3 + ".wav"))

    return {
        "message": "Found succefully",
        "address": address,
        "location": location,
        "location_class": location_class,
    }
