import time
import requests
import json

EPOCH_TIMESTAMP = 1612942165

stats = {}
risk_score = 10


mappings = {
  'sushi': {
    'address': '0xe94B5EEC1fA96CEecbD33EF5Baa8d00E4493F4f3',
    'tokenAddr': '0x6b3595068778dd592e39a122f4f5a5cf09c90fe2'
  }
}

def get_treasury_balance(address, tokenAddr):
  r = requests.get('https://api.ethplorer.io/getAddressInfo/' + address + '?apiKey=freekey&token=' + tokenAddr)
  res = r.json()
  balance = (res['tokens'][0]['balance'] / 10 ** 18)
  price = res['tokens'][0]['tokenInfo']['price']['rate']
  total = balance * price
  print("Total balalnce in USD = " + str(total))
  return total


def get_stats():
  r = requests.post('https://api.thegraph.com/subgraphs/name/zippoxer/sushiswap-subgraph-fork', json={
    "operationName": "uniswapDayDatas",
    "query": """query uniswapDayDatas($startTime: Int!, $skip: Int!) {
      uniswapDayDatas(first: 1000, skip: $skip, where: {date_gt: $startTime}, orderBy: date, orderDirection: asc) {
        id
        date
        totalVolumeUSD
        dailyVolumeUSD
        dailyVolumeETH
        totalLiquidityUSD
        totalLiquidityETH
        __typename
      }
      }
    """,
    "variables": {"startTime": EPOCH_TIMESTAMP, "skip": 0},
    "skip": 0,
    "startTime": EPOCH_TIMESTAMP
  })
  res = r.json()
  stats = res

  treasury_balance = get_treasury_balance(mappings['sushi']['address'], mappings['sushi']['tokenAddr'])
  print('treasury balance is ' + str(treasury_balance))

  print("Assuming loan amount = $1 million")
  for record in res['data']['uniswapDayDatas']:
    debt = 1000000
    equity = treasury_balance
    cashflow = float(record['dailyVolumeUSD']) * 0.003
    debt_equity_ratio = debt / equity
    debt_cashflow_ratio = debt / cashflow
    de_sensitivity_occ = 0.1
    dcf_sensitivity_occ = 0.3

    risk_score = (debt_equity_ratio * 0.25) + (debt_cashflow_ratio * 0.25) + (de_sensitivity_occ * 0.25) + (dcf_sensitivity_occ * 0.25)
    print("equity = %.2f, cashflow revenue = %.2f, risk score = %.2f" % (equity, cashflow, risk_score))


  data = {'name': 'sushi', 'score': risk_score}

  with open('../stats.json', 'w') as outfile:
    json.dump(data, outfile)
    # calculate & set risk score here
    # risk_score = 10


def post_stats_to_oracle():
  print('')

get_stats()
post_stats_to_oracle()

#import sys
#sys.exit()

#get_stats()
#post_stats_to_oracle()

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
from tornado.ioloop import PeriodicCallback
import tornado.web

class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.callback = PeriodicCallback(self.send_hello, 2000)
        self.callback.start()

    def send_hello(self):
        self.write_message(json.dumps([{"name": "sushi", "score": risk_score}]))

    def on_message(self, message):
        pass

    def on_close(self):
        self.callback.stop()

application = tornado.web.Application([
    (r'/websocket', WSHandler),
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8081)
    tornado.ioloop.IOLoop.instance().start()