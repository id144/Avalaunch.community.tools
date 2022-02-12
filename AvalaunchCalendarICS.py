import json
import os
import re
import sys
import requests
from ics import Calendar, Event
from datetime import datetime
from web3 import Web3


apiSession = requests.Session()

airdropsURL = 'https://avalaunch-kyc.herokuapp.com/api/v1/airdrops'
projectsURL = 'https://avalaunch-kyc.herokuapp.com/api/v1/projects'


def getAirdropsInfo():    
    try:
        r = apiSession.get(url=airdropsURL, timeout=10)
        _APIinfo = r.json()     
        return _APIinfo
    except Exception as e:
        print(e)
        return []

def getProjectsInfo():    
    try:
        r = apiSession.get(url=projectsURL, timeout=10)
        _APIinfo = r.json()     
        return _APIinfo
    except Exception as e:
        print(e)
        return []

def getAccountInfo(_address):    
    try:
        profileURL = 'https://avalaunch-kyc.herokuapp.com/api/v1/wallet/' + _address +  '+?allocations=true&transactions=false'
        r = apiSession.get(url=profileURL, timeout=10)
        _APIinfo = r.json()     
        return _APIinfo
    except Exception as e:
        print(e)
        return []      

def newEvent(_title, _description, datebegin, dateend):
    _e = Event()
    _e.name = _title
    _e.description = _description
    _e.begin = (datetime.utcfromtimestamp(datebegin).strftime('%Y-%m-%d %H:%M:%S')) 
    _e.end = (datetime.utcfromtimestamp(dateend).strftime('%Y-%m-%d %H:%M:%S')) 
    return _e

def nameFromID(id, projects):
    for _project in projects['projects']:
        if int(_project['id']) == int(id):

            return _project['title']
    return 'unknown project'

def main(_address):    
    c = Calendar()
    #Timezone sample
    #https://github.com/ics-py/ics-py/blob/main/tests/normalization.py
    #tzUTC  = Timezone.from_tzid("Etc/GMT")


    _airDrops =  getAirdropsInfo()
    _projects =  getProjectsInfo()
    _account = getAccountInfo(_address)

    avalaunchEvents = []

    for _airDrop in _airDrops['airdrops']:
        for _portion in _airDrop['portions']:
            e = Event()
            e.name = _airDrop['title'] + ' - Airdrop #'   + str(_portion['id'])
            e.description = _portion['description'] + ' Contract:' + (_portion['contract_address'])+ ' Token:' + (_airDrop['token_address'])
            e.begin = (datetime.utcfromtimestamp(_portion['start_time']).strftime('%Y-%m-%d %H:%M:%S'))        
            avalaunchEvents.append(e)


    for _project in _projects['projects']:
            
            _event = newEvent( 
                _project['title'] + ' - Registration',
                _project['heading_text'], 
                _project['timeline']['registration_opens'], 
                _project['timeline']['registration_closes']
                )
            avalaunchEvents.append(_event)

            
            _event = newEvent( 
                _project['title'] + ' - Sale' ,
                _project['heading_text'], 
                _project['timeline']['seed_round'],
                _project['timeline']['sale_ends']
                )
            avalaunchEvents.append(_event)




    for _allocation in _account['allocations']:
        for _portion in _allocation['vesting']:

            e = Event()
            _claimStatus =  '(Claimed)' if _portion['is_withdrawn'] else '(Unclaimed)'
            _name = nameFromID( str(_allocation['project_id']), _projects) + ' - Vesting'   + str(_portion['percent']) + '% ' + _claimStatus
            e.name = _name
            e.begin = (datetime.utcfromtimestamp(_portion['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))    
            avalaunchEvents.append(e)

    for _event in avalaunchEvents:
        c.events.add(_event)
    # [<Event 'My cool event' begin:2014-01-01 00:00:00 end:2014-01-01 00:00:01>]
    with open('avalaunch.ics', 'w') as my_file:
        my_file.writelines(c)
    # and it's done !

if __name__ == "__main__":
    print("---Avalaunch comunity tool - ICS export---")

    print("")
    if len(sys.argv) > 1:
        address =  Web3.toChecksumAddress(re.sub(r'\W+', '', sys.argv[1].lower()))                
        if not Web3.isAddress(address):
            print('Not an ethereum address')        
        main(address)

    else:
        print("Add your wallet address as a command parameter")    
        print("ie. ")
        print( "python3 " + os.path.basename(__file__) + " 0x16Bc59978851012aDA4843E49Df2A314EA38665a")        
        print("")
        quit()    