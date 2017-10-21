# coding=utf-8
# chmod +x bot.py
# while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import time

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name= "WUDUJIAO"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = True

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index = 0
prod_exchange_hostname = "production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)


def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    return json.loads(exchange.readline())

sym = {}
trade_turn = 0
trade_record = []
record = []
# symbol 到 buy 和 sell 的字典
book_record = {}


def dumps():
    with open('data') as f:
        pass


def hello():
    return {"type": "hello", "team": team_name.upper()}


def buy(id, sym, price, size):
    return {"type": "add", "order_id": id, "symbol": "SYM", "dir": "BUY", "price": price, "size": size}


def sell(id, sym, price, size):
    return {"type": "add", "order_id": id, "symbol": "SYM", "dir": "SELL", "price": price, "size": size}


def add_trade(sym, price, size):
    global record
    try:
        record[sym].append((price, size))
    except Exception as e:
        record = []
        record[sym].append((price, size))


def process(info):
    if info["type"] == "hello":
        print("The exchange replied:", info, file=sys.stderr)
    elif info["type"] == "open":
        for i in info["symbols"]:
            sym[i] = 1
    elif info["type"] == "close":
        for i in info["symbols"]:
            sym[i] = 0
    elif info["type"] == "error":
        print(info["error"])
    elif info["type"] == "book":
        buy = info['buy']
        sell = info['sell']
        best_buy = buy[0]
        for abuy in buy:
            if abuy[0] > best_buy[0]:
                best_buy = abuy

        best_buy = sell[0]
        for asell in sell:
            if asell[0] < best_sell[0]:
                best_sell = asell

        book_record[info['symbol']] = {'buy': buy, 'sell': sell, 'best_sell': best_sell, 'best_buy': best_buy}
        print('book_record: ', book_record)
    elif info["type"] == "trade":
        add_trade(info["symbol"], info["price"], info["size"])
    elif info["type"] == "ack":
        pass
    elif info["type"] == "reject":
        pass
    elif info["type"] == "fill":
        pass
    else:
        pass


def processInfo(exchange):
    info = read_from_exchange(exchange)
    process(info)
    return info

# ~~~~~============== MAIN LOOP ==============~~~~~



def main():
    exchange = connect()
    id = 1
    write_to_exchange(exchange, hello())
    process(read_from_exchange(exchange))
    i = 0
    while i < 10:
        i = i + 1
        try:
            info = read_from_exchange(exchange)
            print('info: ', info)
            process(info)
            print('putting buy order')
            write_to_exchange(exchange, buy(id, "USD", 79980, 1))
            process(read_from_exchange(exchange))
            print('putting sell order')
            write_to_exchange(exchange, sell(id, "USD", 80020, 1))
            process(read_from_exchange(exchange))

            id += 1
            time.sleep(5)
        except:
            continue
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
        

def cancel_all():
    index = 0
    exchange = connect()
    write_to_exchange(exchange, hello())
    info = read_from_exchange(exchange)
    process(info)
    while index < 100:
        time.sleep(0.05)
        index = index + 1
        text = {
            'type': 'cancel', 'order_id': index,
        }
        write_to_exchange(exchange, text)
        server_msg = read_from_exchange(exchange)
        if server_msg['type'] == 'error':
            print('after cancel all, return message: ', server_msg['error'])
            return None
        elif server_msg['type'] == 'out':
            print('canceling all: order_id=', server_msg['order_id'])
        elif server_msg['type'] == 'reject':
            print('order rejected, order_id=',  server_msg['order_id'],', return message=', server_msg['error'])
        else:
            print('something unexpected in cancel_all(), msg_type=', server_msg['type'])



cancel_all()

if __name__ == "__main__":
    main()

