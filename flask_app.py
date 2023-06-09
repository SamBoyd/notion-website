# A very simple Flask Hello World app for you to get started with...
import logging

from dateutil.parser import isoparse
from datetime import datetime
from flask import Flask, render_template
from flask_caching import Cache

from notion_client import Client
from notion_client.errors import APIResponseError

NOTION_SECRET = 'XXXXXXXXX'
NOTION_DATABASE_ID = 'XXXXXXXXX'

logger = logging.getLogger(__name__)

notion = Client(auth=NOTION_SECRET)

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

app = Flask(__name__)
cache.init_app(app)


# Notion database https://www.notion.so/ea0b3a5be95542369660df5ee0a563a9?v=5c3d911f01ec4d3887ead0263a3e85d0&pvs=4

@cache.cached(timeout=50)
def get_data():
    try:
        blog_db = notion.databases.query(database_id=NOTION_DATABASE_ID)
    except APIResponseError as e:
        if 'API token is invalid.' in str(e):
            logging.info('API token is invalid')
        elif 'path failed validation: path.database_id should be a valid uuid' in str(e):
            logging.info('Database id is invalid')

        return []

    page_ids = [result['id'] for result in blog_db['results']]

    blogs = []

    for page_id in page_ids:
        page = notion.pages.retrieve(page_id=page_id)

        if page['properties']['Published']['checkbox'] is False:
            continue

        page_title = page['properties']['Title']['title'][0]['plain_text']
        child_blocks = notion.blocks.children.list(page_id)
        text_blocks = []

        for child in child_blocks['results']:
            for text_block in child['paragraph']['rich_text']:
                text_blocks.append(text_block['plain_text'])

        dt = isoparse(page['created_time'])
        created_at = dt.strftime('%d %B %y')

        href = f"{page_title.replace(' ', '-').lower()}"

        blogs.append(
            dict(
                title=page_title,
                created_at=created_at,
                content=text_blocks,
                href=href
            )
        )

    return sorted(blogs, key=lambda page: datetime.strptime(page['created_at'], '%d %B %y'))


# @cache.cached(timeout=50)
@app.route('/')
def hello_world():
    blogs = get_data()
    return render_template('template.html', blogs=blogs)
