import json
import requests

INVESTORS = 'investors.json'
SELL_OFFERS = 'sell_offers.json'

def get(fname):
    f = open(fname, 'r')
    investors = json.loads(f.read())
    f.close()

    return investors

def write(fname, data):
    f = open(fname, 'w')
    f.write(json.dumps(data))
    f.close()

def show_investors():
    return get(INVESTORS)

def show_offers():
    return get(SELL_OFFERS)

def pay_dividends():
    entries = requests.get('https://ch.tetr.io/api/users/by/league?limit=100').json()['data']['entries']
    baseline = requests.get(f'https://ch.tetr.io/api/users/by/league?limit=1&after={entries[-1]["league"]["tr"] - 0.00000001}:0:1e-10').json()['data']['entries'][0]['league']['tr']

    payouts = {entry['_id']: entry['league']['tr'] - baseline for entry in entries}

    investors = get(INVESTORS)
    for investor in investors:
        for stock in investor['portfolio']:
            if stock in payouts:
                investor['balance'] += investor['portfolio']['stock'] * payouts * 0.01
    write(INVESTORS, investors)

def make_sell_offer(seller, stock, price, maximum):
    sell_offers = get(SELL_OFFERS)
    if stock not in sell_offers:
        sell_offers[stock] = {'total': 0, 'offers': []}

    for offer in sell_offers[stock]['offers']:
        if offer['seller'] == seller:
            write(SELL_OFFERS, sell_offers)
            return

    sell_offers[stock]['offers'].append({'seller': seller, 'stock': stock, 'price': price, 'maximum': maximum})
    sell_offers[stock]['total'] += maximum 

    sell_offers[stock]['offers'].sort(key=lambda a: -a['price'])
    write(SELL_OFFERS, sell_offers)

def retract_sell_offer(seller, stock):
    sell_offers = get(SELL_OFFERS)
    if stock not in sell_offers:
        return

    for i, offer in enumerate(sell_offers[stock]['offers']):
        if offer['seller'] == seller:
            sell_offers[stock]['total'] -= offer['maximum']
            del sell_offers[stock]['offers'][i]
            break
    write(SELL_OFFERS, sell_offers)

def buy_stocks(buyer, stock, value):
    investors = get(INVESTORS)
    sell_offers = get(SELL_OFFERS)

    if buyer not in investors:
        investors[buyer] = {'balance': 10000, 'portfolio': {}}

    if value >= investors[buyer]['balance'] or value <= 0 or stock not in sell_offers or value > sell_offers[stock]['total']:
        write(INVESTORS, investors)
        return

    if stock not in investors[buyer]['portfolio']:
        investors[buyer]['portfolio'][stock] = 0

    while value > 0:
        curr = sell_offers[stock]['offers'][-1]
        if value > curr['maximum']:
            value -= curr['maximum']

            investors[buyer]['portfolio'][stock] += curr['maximum'] / curr['price']

            del sell_offers[stock]['offers'][-1]

        else:
            curr['maximum'] -= value
            investors[buyer]['portfolio'][stock] += value / curr['price']
            investors[buyer]['balance'] -= value

            value = 0
    write(INVESTORS, investors)
    write(SELL_OFFERS, sell_offers)

