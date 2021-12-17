#!/usr/bin/python3
import enum
import ubus
import time
import re
from icmplib import ping
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
    status = -1
    protocol = protocol_type.empty
    parameters = {}

class rule:
    name = ''
    description = ''
    state = False
    status = -1
    expression = ''
    event_true = event_type.empty
    event_false = event_type.empty
    parameters = {}

module_name = "Pingers"
confName = "pingerconf"
pingers = []
rules = []
threads_pingers = []

protocol_type_map = { 'NONE' : protocol_type.empty,
                        'ICMP' : protocol_type.ICMP }

event_type_map = { 'NONE' : event_type.empty }

pingerMutex = Lock()
ruleMutex = Lock()
pollMainThread = None
pollRulesThread = None

pinger_default = pinger()
rule_default = rule()


def do_event(event):
    if event != event_type.empty:
        #TODO
        pass

def thread_poll(thread_id, pinger):
    while thread_id in threads_pingers:
        if not pinger.state:
            #time.sleep(1)
            continue

        #print("thread_poll loop... " + pinger.parameters['address'])

        try:
            result = ping(address=pinger.parameters['address'], count=pinger.parameters['tries'], payload_size=pinger.parameters['size'], timeout=(pinger.parameters['timeout'] / 1000))

            try:
                if pinger.parameters['nofails']:
                    if result.packet_loss == 0 and result.is_alive:
                        pinger.status = 1
                    else:
                        pinger.status = 0
                else:
                    if result.is_alive:
                        pinger.status = 1
                    else:
                        pinger.status = 0
            except:
                pinger.status = -2
        except Exception as ex:
            #bad ping
            print("thread_poll exception: " + str(ex))

        #time.sleep(1)

def expression_convert(expression):
    result = re.findall(r'%_(\S+)_%', expression)
    result = set(result)

    for r in result:
        expression = expression.replace("%_" + r + "_%", "data['" + r + "']")

    logic_operands = [ 'AND', 'OR', 'NOT' ]

    for l in logic_operands:
        expression = expression.replace(l, l.lower())

    expression = expression.replace("=", "==")

    return expression

def applyConf():
    def get_pinger_state_callback(event, data):
        ret_val = { 'state' : '-1',
                    'status' : '-2' }

        pingerMutex.acquire()

        for p in pingers:
            if data['name'] == p.name:
                ret_val['state'] = str(int(p.state))
                ret_val['status'] = str(p.status)
                break

        pingerMutex.release()

        event.reply(ret_val)

    def get_rule_state_callback(event, data):
        ret_val = { 'state' : '-1',
                    'status' : '-2' }

        ruleMutex.acquire()

        for r in rules:
            if data['name'] == r.name:
                ret_val['state'] = str(int(r.state))
                ret_val['status'] = str(r.status)
                break

        ruleMutex.release()

        event.reply(ret_val)

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
                rule_default.expression = confdict['expression']
            except:
                pass

        #new pinger
        if confdict['.type'] == 'pinger' and confdict['.name'] != 'pinger_prototype':
            p = pinger()
            try:
                p.name = confdict['name']
            except:
                p.name = pinger_default.name

            try:
                p.description = confdict['description']
            except:
                p.description = pinger_default.description

            try:
                p.state = bool(int(confdict['state']))
            except:
                p.state = pinger_default.state

            try:
                p.protocol = protocol_type_map[confdict['protocol']]
            except:
                p.protocol = pinger_default.protocol

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
            r = rule()

            try:
                r.name = confdict['name']
            except:
                r.name = rule_default.name

            try:
                r.description = confdict['description']
            except:
                r.description = rule_default.description

            try:
                r.state = bool(int(confdict['state']))
            except:
                r.state = rule_default.state

            try:
                r.event_true = event_type_map[confdict['event_true']]
            except:
                r.event_true = rule_default.event_true

            try:
                r.event_false = event_type_map[confdict['event_false']]
            except:
                r.event_false = rule_default.event_false

            try:
                r.expression = confdict['expression']
            except:
                r.expression = rule_default.expression

            ruleMutex.acquire()
            rules.append(r)
            ruleMutex.release()

    pingerMutex.acquire()

    for p in pingers:
        thr_id = len(threads_pingers) + 1

        threads_pingers.append(thr_id)

        thr = Thread(target=thread_poll, args=(thr_id, p))
        thr.start()

    pingerMutex.release()

    ubus.add(
            'owrt_pingers', {
                'get_pinger_state': {
                    'method': get_pinger_state_callback,
                    'signature': {
                        'name': ubus.BLOBMSG_TYPE_STRING
                    }
                },
                'get_rule_state': {
                    'method': get_rule_state_callback,
                    'signature': {
                        'name': ubus.BLOBMSG_TYPE_STRING
                    }
                }
            }
        )

def reconfigure(event, data):
    if data['config'] == confName:
        del pingers[:]
        del rules[:]
        del threads_pingers[:]

        applyConf()

def pollMain():
    ubus.listen(("commit", reconfigure))
    ubus.loop()

def pollRules():
    while True:
        data = {}

        pingerMutex.acquire()

        #build data from pingers
        for p in pingers:
            if p.status == 1:
                data[p.name] = True
            else:
                data[p.name] = False

        pingerMutex.release()

        ruleMutex.acquire()

        for r in rules:
            if not r.state:
                continue

            expr = expression_convert(r.expression)
            expr_res = eval(expr)

            if not expr_res:
                r.status = 0
                print("rule " + r.name + " is false")
                do_event(r.event_false)
            else:
                r.status = 1
                print("rule " + r.name + " is true")
                do_event(r.event_true)

        ruleMutex.release()

        time.sleep(1)

def main():
    try:
        ubus.connect()

        applyConf()

        print("Pingers: " + str(pingers))

        pollRulesThread = Thread(target=pollRules, args=())
        pollRulesThread.start()

        pollMainThread = Thread(target=pollMain, args=())
        pollMainThread.start()
    except KeyboardInterrupt:
        del threads_pingers[:]
        ubus.disconnect()

if __name__ == "__main__":
    main()
