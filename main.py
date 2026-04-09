import time

from database.db import DbConnection
from domain.dtos import Task, status
from web_driver.wd import WebDriver

db_conn = DbConnection()
market = db_conn.get_market()
url = market.marketplace_info.link

webdriver = WebDriver(market, db_conn)

webdriver.load_url(url)

time_start = time.time()
campaigns = webdriver.bidder_info()

tasks = []


for campaign in campaigns:
    campaign.items.sort(key=lambda x: x.bid, reverse=True)

for campaign in campaigns:
    if campaign.status != status.get('running'):
        continue

    cat = {}
    for item in campaign.items:
        if not item.quantity:
            continue
        cat.setdefault(item.category_id, 0)
        cat[item.category_id] += 1
        tasks.append(Task(
            campaign_id=campaign.campaign_id,
            sku=item.sku,
            category_id=item.category_id,
            region=campaign.regions,
            keywords=item.keywords,
            bid=item.bid,
            limit=4000.0 if any([key in item.category.lower() for key in ('кофе', 'пылесос', 'грили')]) else 2000.0,
            position=cat[item.category_id]
        ))

webdriver.bidder(tasks)
time_end = time.time()
print(f'Затрачено {time_end - time_start}')
# webdriver.quit()
