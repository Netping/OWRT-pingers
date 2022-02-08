#!/usr/bin/python3
import ubus
import os
import time

# config info
config = "pingerconf"
config_path = "/etc/config/"

# ubus methods info
test_ubus_objects = [
    {
        'uobj': 'owrt_pingers',
        'umethods': [
            {
                'umethod': 'get_pinger_state',
                'inparams': {"name":"google_ping"},
                'outparams': {
                    'state': ["__contains__", [str(x) for x in range(0,2)]],
                    'status': ["__contains__", [str(x) for x in range(-2,2)]]
                }
            },
            {
                'umethod': 'get_rule_state',
                'inparams': {"name":"Google good"},
                'outparams': {
                    'state': ["__contains__", [str(x) for x in range(0,2)]],
                    'status': ["__contains__", [str(x) for x in range(-2,2)]]
                }
            },
        ]
    },
]

try:
    ubus.connect()
except:
    print("Can't connect to ubus")

def test_conf_existance():
    ret = False

    try:
        ret = os.path.isfile(f"{config_path}{config}")
    except:
        assert ret

    assert ret

def test_conf_valid():
    ret = False

    try:
        # ubus.connect()
        confvalues = ubus.call("uci", "get", {"config": config})
        for confdict in list(confvalues[0]['values'].values()):
            #check globals
            if confdict['.type'] == 'globals' and confdict['.name'] == 'globals':
                assert confdict['protocol'] == ['NONE.нет', 'ICMP.пинг']
                assert confdict['event'] == ['NONE.нет', 'statechanged.Состояние изменено']
                assert confdict['maxpingers'] == '32'
            #check pinger_prototype
            if confdict['.type'] == 'pinger' and confdict['.name'] == 'pinger_prototype':
                assert confdict['name'] == 'Pinger'
                assert confdict['description'] == '0'
                assert confdict['protocol'] == 'NONE'
                assert confdict['state'] == '0'
            #check rule_prototype
            if confdict['.type'] == 'rule' and confdict['.name'] == 'rule_prototype':
                assert confdict['name'] == 'Rule'
                assert confdict['description'] == '0'
                assert confdict['state'] == '0'
                assert confdict['expression'] == '0'
                assert confdict['event_true'] == 'NONE'
                assert confdict['event_false'] == 'NONE'
    except:
        assert ret

def test_ubus_methods_existance():
    ret = False

    try:
        test_uobj_list = [x['uobj'] for x in test_ubus_objects]
        test_uobj_list.sort()
        uobj_list = []
        for l in list(ubus.objects().keys()):
            if l in test_uobj_list:
                uobj_list.append(l)
        uobj_list.sort()
        assert test_uobj_list == uobj_list
    except:
        assert ret

def test_ubus_api():
    ret = False

    try:
        test_uobjs = [x for x in test_ubus_objects]
        for uobj in test_uobjs:
            test_uobj_methods = [x for x in uobj['umethods']]
            for method in test_uobj_methods:
                res = ubus.call(uobj['uobj'], method['umethod'], method['inparams'])
                assert type(method['outparams']) == type(res[0])
                if isinstance(method['outparams'], dict):
                    for key in method['outparams']:
                        assert key in res[0]
                        if key in res[0]:
                            assert getattr(method['outparams'][key][1], method['outparams'][key][0])(res[0][key])
    except:
        assert ret
