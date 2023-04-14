# A very simple Flask Hello World app for you to get started with...
import logging

from dateutil.parser import isoparse
from flask import Flask, render_template
from flask_caching import Cache

from notion_client import Client

logger = logging.getLogger(__name__)

notion = Client(auth='secret_keRIQHcf5dSHm79AtTaIlvMxZ7E7LkXTQ98rfdex2V2')

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

app = Flask(__name__)
cache.init_app(app)


# Notion database https://www.notion.so/ea0b3a5be95542369660df5ee0a563a9?v=5c3d911f01ec4d3887ead0263a3e85d0&pvs=4

@cache.cached(timeout=50)
def get_data():
    blog_db = notion.databases.query(database_id='ea0b3a5be95542369660df5ee0a563a9')
    page_ids = [result['id'] for result in blog_db['results']]

    blogs = []

    for page_id in page_ids:
        page = notion.pages.retrieve(page_id=page_id)
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

    return blogs


# @cache.cached(timeout=50)
@app.route('/')
def hello_world():
    blogs = get_data()
    return render_template('template.html', blogs=blogs)
