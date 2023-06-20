# app/main.py

import json
import requests
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import database, Reality

SUB_CB_TO_TEXT = {
    2: '1+kk',
    3: '1+1',
    4: '2+kk',
    5: '2+1',
    6: '3+kk',
    7: '3+1',
    8: '4+kk',
    9: '4+1',
    10: '5+kk',
    11: '5+1',
    12: '6-a-vice',
    16: 'atypicky'
}

SREALITY_API = 'https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&page={}'
IMAGE_URL = 'https://www.sreality.cz/detail/prodej/byt/{}/{}/{}#img=0'
MAX_SCRAPED_DATA = 500
PAGE_SIZE = 20

def collect_data(page_no: int):
    '''
    Function collect_data collect data from one source page
    Input: page number
    Output: list of sets
    '''

    data = None
    try:
        response = requests.get(SREALITY_API.format(page_no))
    except Exception:
        print('Error: read from api fails')
    else:
        data = json.loads(response.text)
    
    items = None
    if data:
        items = data['_embedded']['estates']

    scraped_data = []
    if items:
        for item in items:
            title_name = item['name']
            sub_cb = item['seo']['category_sub_cb']
            sub_locality = item['seo']['locality']
            hash_id = item['hash_id']
            image_link = IMAGE_URL.format(SUB_CB_TO_TEXT[sub_cb], sub_locality, hash_id)

            data_set = (title_name, image_link)
            scraped_data.append(data_set)

    return scraped_data


app = FastAPI(title="web scrape app")
templates = Jinja2Templates(directory="app/template")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    db_data = await Reality.objects.all()
    result_blok = []
    for reality_item in db_data:
        adv_item = dict(reality_item)
        result_blok.append('\t{}\t\t{}'.format(adv_item['adv_name'], adv_item['adv_img_link']))

    return templates.TemplateResponse("index.html", {"request": request, "data":result_blok})


@app.get("/items/")
async def read_items():
    return await Reality.objects.all()


@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()

    db_data = await Reality.objects.all()
    data_count_in_DB = len(db_data)

    # populate DB 500 record, one page 20 records, add one extra page
    complete_data = 0
    for page_index in range(0, (MAX_SCRAPED_DATA // PAGE_SIZE) + 1):
        if complete_data >= (MAX_SCRAPED_DATA - data_count_in_DB):
            break

        data = collect_data(page_index)
        reality_data = []
        for data_set in data:
            title_name, image_link = data_set
            reality_data.append(Reality(adv_name=title_name, adv_img_link=image_link))

        await Reality.objects.bulk_create(reality_data)

        complete_data += len(reality_data)


@app.on_event("shutdown")
async def shutdown():
    if database.is_connected:
        await database.disconnect()

