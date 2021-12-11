#!/usr/bin/python3
import enum
import ubus
from threading import Thread
from threading import Lock
from journal import journal




class protocol_type(enum.Enum):
    empty = 0,
    ICMP = 1

class event_type(enum.Enum):
    empty = 0

class pinger:
    name = ''
    description = ''
    state = False
    protocol = protocol_type.empty

class rule:
    name = ''
    description = ''
    state = False
    status = 0
    expression = None
    event_true = event_type.empty
    event_false = event_type.empty

module_name = "Pingers"
confName = "pingerconf"
pingers = []
rules = []

protocol_type_map = { 'NONE' : protocol_type.empty,
                        'ICMP' : protocol_type.ICMP }

event_type_map = { 'NONE' : event_type.empty }

mutex = Lock()
pollMainThread = None
pollPingersThread = None
pollRulesThread = None

def applyConf():
    #TODO
    pass

def reconfigure(event, data):
    if data['config'] == confName:
        del pingers[:]
        del rules[:]

        applyConf()

def pollMain():
    ubus.listen(("commit", reconfigure))
    ubus.loop()

def pollPingers():
    while True:
        for p in pingers:
            #TODO
            mutex.acquire()
            e = p
            mutex.release()

def pollRules():
    while True:
        for r in rules:
            #TODO
            mutex.acquire()
            e = r
            mutex.release()

def main():
    try:
        ubus.connect()

        applyConf()

        pollPingersThread = Thread(target=pollPingers, args=())
        pollPingersThread.start()

        pollRulesThread = Thread(target=pollRules, args=())
        pollRulesThread.start()

        pollMain()
    except KeyboardInterrupt:
        ubus.disconnect()

if __name__ == "__main__":
    main()
