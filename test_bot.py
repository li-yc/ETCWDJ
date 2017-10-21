# coding=utf-8
# chmod +x bot.py
# while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import time

# ~~~~~============== CONFIGURATION  ==============~~~~~


def put(msg, msg2=' '):
    print(msg, msg2)

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
    with open('data.txt') as f:
        pass


def hello():
    return {"type": "hello", "team": team_name.upper()}


def buy(index, symbol, price, size):
    return {"type": "add", "order_id": index, "symbol": symbol, "dir": "BUY", "price": price, "size": size}


def sell(index, symbol, price, size):
    return {"type": "add", "order_id": index, "symbol": symbol, "dir": "SELL", "price": price, "size": size}


def add_trade(symbol, price, size):
    global record
    try:
        record[symbol].append((price, size))
    except NameError or TypeError:
        record = []
        record[symbol].append((price, size))


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

        best_sell = sell[0]
        for asell in sell:
            if asell[0] < best_sell[0]:
                best_sell = asell

        book_record[info['symbol']] = {'buy': buy, 'sell': sell, 'best_sell': best_sell, 'best_buy': best_buy}
        print('book_record: ', book_record)
    elif info["type"] == "trade":
        add_trade(info["symbol"], info["price"], info["size"])
    elif info["type"] == "ack":
        put('order placed, order_id=', info['order_id'])
    elif info["type"] == "reject":
        put('rejected, error message: ', info['error'])
    elif info["type"] == "fill":
        put('order traded, symbol=' + info['symbol'] + ', dir=' + info['dir'] + ', price=' + info['price'])
    else:
        pass


def process_info(exchange, times, interval=0.05):
    t = 0
    while t < times:
        t += interval
        time.sleep(interval)
        info = read_from_exchange(exchange)
        process(info)

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
            put('putting buy order')
            buy_order = {

            }
            write_to_exchange(exchange, buy(id, "USDHKD", 79996, 10))
            process_info(exchange, 2, interval=0.2)
            put('putting sell order')
            id += 1
            write_to_exchange(exchange, sell(id, "USDHKD", 80004, 10))
            process_info(exchange, 2, interval=0.2)
            print('i:', i)
            id += 1
        except Exception as e:
            print('ERROR in main():', e)
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
            print('order rejected, order_id=',  server_msg['order_id'], ', return message=', server_msg['error'])
        else:
            print('something unexpected in cancel_all(), msg_type=', server_msg['type'])


if __name__ == "__main__":
    main()

