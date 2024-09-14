import json
import requests

INVESTORS = 'investors.json'
SELL_OFFERS = 'sell_offers.json'

USERNAME_CACHE = {'ids': {}, 'usernames': {}}

def get(fname):
    f = open(fname, 'r')
    file = json.loads(f.read())
    f.close()

    return file

def write(fname, data):
    f = open(fname, 'w')
    f.write(json.dumps(data))
    f.close()

def tio_id(username):
    if username in USERNAME_CACHE['ids']:
        return USERNAME_CACHE['ids'][username]

    t_id = requests.get(f"https://ch.tetr.io/api/users/{username}").json()['data']['_id']
    USERNAME_CACHE['ids'][username] = t_id
    USERNAME_CACHE['usernames'][t_id] = username

    return t_id

def tio_username(t_id):
    if t_id in USERNAME_CACHE['usernames']:
        return USERNAME_CACHE['usernames'][t_id]

    username = requests.get(f"https://ch.tetr.io/api/users/{t_id}").json()['data']['username']
    USERNAME_CACHE['ids'][username] = t_id
    USERNAME_CACHE['usernames'][t_id] = username

    return username

def tio_standing(username):
    return requests.get(f"https://ch.tetr.io/api/users/{username}/summaries/league").json()['data']['standing']

def update_cache():
    ids = {}
    usernames = {}

    entries = requests.get('https://ch.tetr.io/api/users/by/league?limit=100').json()['data']['entries']
    for entry in entries:
        usernames[entry['_id']] = entry['username']
        ids[entry['username']] = entry['_id']

    USERNAME_CACHE = {'ids': ids, 'usernames': usernames}

def get_investor(investor):
    investor = str(investor)

    investors = get(INVESTORS)

    if investor not in investors:
        investors[investor] = {'balance': 10000, 'portfolio': {}}

    portfolio = investors[investor]['portfolio']
    portfolio = {tio_username(stock):portfolio[stock] for stock in portfolio}
    investors[investor]['portfolio'] = portfolio
    return investors[investor]

def get_leaderboard():
    investors = get(INVESTORS)
    return sorted([{'id': player, 'balance': investors[player]['balance']} for player in investors if player != 'bank'], key=lambda a:-a['balance'])[:20]

def get_offers():
    unformatted = get(SELL_OFFERS)
    offers = []
    for stock in unformatted:
        name = tio_username(stock)
        for offer in unformatted[stock]['offers']:
            offers.append({
                'stock': name,
                'seller': offer['seller'],
                'price': offer['price'],
                'quantity': offer['maximum'] / offer['price']
            })

    return offers

def pay_dividends():
    entries = requests.get('https://ch.tetr.io/api/users/by/league?limit=100').json()['data']['entries']
    baseline = requests.get(f'https://ch.tetr.io/api/users/by/league?limit=1&after={entries[-1]["league"]["tr"] - 0.00000001}:0:1e-10').json()['data']['entries'][0]['league']['tr']

    payouts = {entry['_id']: entry['league']['tr'] - baseline for entry in entries}

    investors = get(INVESTORS)
    for investor_id in investors:
        investor = investors[investor_id]
        for stock in investor['portfolio']:
            if stock in payouts:
                investor['balance'] += investor['portfolio'][stock] * payouts[stock] * 0.01
    write(INVESTORS, investors)

def make_sell_offer(seller, stock, price, maximum):
    standing = tio_standing(stock)
    if standing > 100:
        return

    stock = tio_id(stock)

    investors = get(INVESTORS)
    if stock not in investors[seller]['portfolio'] or maximum / price > investors[seller]['portfolio'][stock]:
        return

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
    stock = tio_id(stock)

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

    stock = tio_id(stock)

    if buyer not in investors:
        investors[buyer] = {'balance': 10000, 'portfolio': {}}

    if value > investors[buyer]['balance'] or value <= 0 or stock not in sell_offers or value > sell_offers[stock]['total']:
        write(INVESTORS, investors)
        return

    if stock not in investors[buyer]['portfolio']:
        investors[buyer]['portfolio'][stock] = 0

    sell_offers[stock]['total'] -= value
    investors[buyer]['balance'] -= value
    while value > 0:
        curr = sell_offers[stock]['offers'][-1]
        if value > curr['maximum']:
            investors[buyer]['portfolio'][stock] += curr['maximum'] / curr['price']
            investors[curr['seller']]['portfolio'][stock] -= curr['maximum'] / curr['price']

            investors[curr['seller']]['balance'] -= curr['maximum']

            del sell_offers[stock]['offers'][-1]

            value -= curr['maximum']

        else:
            investors[curr['seller']]['balance'] += value
            investors[curr['seller']]['portfolio'][stock] -= value / curr['price']

            curr['maximum'] -= value

            investors[buyer]['portfolio'][stock] += value / curr['price']

            value = 0

    write(INVESTORS, investors)
    write(SELL_OFFERS, sell_offers)

