#!/usr/bin/python3
import enum
import ubus
import icmplib
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
    parameters = {}

class rule:
    name = ''
    description = ''
    state = False
    status = 0
    expression = None
    event_true = event_type.empty
    event_false = event_type.empty
    parameters = {}

module_name = "Pingers"
confName = "pingerconf"
pingers = []
rules = []

protocol_type_map = { 'NONE' : protocol_type.empty,
                        'ICMP' : protocol_type.ICMP }

event_type_map = { 'NONE' : event_type.empty }

pingerMutex = Lock()
ruleMutex = Lock()
pollMainThread = None
pollPingersThread = None
pollRulesThread = None

pinger_default = pinger()
rule_default = rule()

def applyConf():
    confvalues = ubus.call("uci", "get", {"config": confName})
    for confdict in list(confvalues[0]['values'].values()):
        if confdict['.type'] == 'pinger' and confdict['.name'] == 'pinger_prototype':
            try:
                pinger_default.name = confdict['name']
            except:
                pass

            try:
                pinger_default.description = confdict['description']
            except:
                pass

            try:
                pinger_default.state = bool(int(confdict['state']))
            except:
                pass

            try:
                pinger_default.protocol = protocol_type_map[confdict['protocol']]
            except:
                pass

        if confdict['.type'] == 'rule' and confdict['.name'] == 'rule_prototype':
            try:
                rule_default.name = confdict['name']
            except:
                pass

            try:
                rule_default.description = confdict['description']
            except:
                pass

            try:
                rule_default.state = bool(int(confdict['state']))
            except:
                pass

            try:
                rule_default.event_true = event_type_map[confdict['event_true']]
            except:
                pass

            try:
                rule_default.event_false = event_type_map[confdict['event_false']]
            except:
                pass

            try:
                rule_default.status = int(confdict['status'])
            except:
                pass

            try:
                rule_default.expression = confdict['expression']
            except:
                pass

        #new pinger
        if confdict['.type'] == 'pinger' and confdict['.name'] != 'pinger_prototype':
            p = pinger_default
            try:
                p.name = confdict['name']
            except:
                pass

            try:
                p.description = confdict['description']
            except:
                pass

            try:
                p.state = bool(int(confdict['state']))
            except:
                pass

            try:
                p.protocol = protocol_type_map[confdict['protocol']]
            except:
                pass

            try:
                p.parameters['address'] = confdict['address']
            except:
                pass

            try:
                p.parameters['size'] = int(confdict['size'])
            except:
                pass

            try:
                p.parameters['timeout'] = int(confdict['timeout'])
            except:
                pass

            try:
                p.parameters['tries'] = int(confdict['tries'])
            except:
                pass

            try:
                p.parameters['nofails'] = bool(int(confdict['nofails']))
            except:
                pass

            pingerMutex.acquire()
            pingers.append(p)
            pingerMutex.release()

        #new rule
        if confdict['.type'] == 'rule' and confdict['.name'] != 'rule_prototype':
            r = rule_default

            try:
                r.name = confdict['name']
            except:
                pass

            try:
                r.description = confdict['description']
            except:
                pass

            try:
                r.state = bool(int(confdict['state']))
            except:
                pass

            try:
                r.event_true = event_type_map[confdict['event_true']]
            except:
                pass

            try:
                r.event_false = event_type_map[confdict['event_false']]
            except:
                pass

            try:
                r.status = int(confdict['status'])
            except:
                pass

            try:
                r.expression = confdict['expression']
            except:
                pass

            ruleMutex.acquire()
            rules.append(r)
            ruleMutex.release()

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
            pingerMutex.acquire()
            e = p
            pingerMutex.release()

            print("pollPingers loop...")

            print("pollPingers e.name " + e.name)
            if e.state:
                try:
                    result = icmplib.ping(address=e.parameters['address'], count=e.parameters['tries'], payload_size=e.parameters['size'], timeout=e.parameters['timeout'])
                    print(result)
                except Exception as ex:
                    #bad ping
                    print("pollPingers exception: " + str(ex))

def pollRules():
    while True:
        for r in rules:
            #TODO
            ruleMutex.acquire()
            e = r
            ruleMutex.release()

def main():
    try:
        ubus.connect()

        applyConf()

        print("Pingers: " + str(pingers))

        pollPingersThread = Thread(target=pollPingers, args=())
        pollPingersThread.start()

        pollRulesThread = Thread(target=pollRules, args=())
        pollRulesThread.start()

        pollMainThread = Thread(target=pollMain, args=())
        pollMainThread.start()
    except KeyboardInterrupt:
        ubus.disconnect()

if __name__ == "__main__":
    main()
