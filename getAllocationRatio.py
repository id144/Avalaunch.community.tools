import re
import sys
import unicodedata
import json
import requests
import time
from web3 import Web3

_AvalaunchAPIURL = "http://avalaunch-kyc.herokuapp.com/api/v1"

def getAPISalesInfo():
    _infoAllSalesURL = _AvalaunchAPIURL + "/projects"
    try:
        r = apiSession.get(url=_infoAllSalesURL, timeout=10)
        _APIinfo = r.json()["projects"]
        _APIinfo.sort(key=id)
        return _APIinfo
    except Exception as e:
        print(e)
        quit()

def getTXJSON(
    _contract="0x41Ed99efeab7f5e82Cc2ba69FA1b81F7aBB7b064",
    _start=1,
    _end=99999999,
    _sort="asc",
):
    _contractTXURL = (
        "https://api.snowtrace.io/api?module=account&action=txlist&address="
        + _contract
        + "&startblock="
        + str(int(_start))
        + "&endblock="
        + str(int(_end))
        + "&sort="
        + _sort
        + "&apikey=YourApiKeyToken"
    )
    for j in range(3):
        try:
            r = apiSession.get(url=_contractTXURL, timeout=10)
            _tx = r.json()["result"]
            break
        except Exception as e:
            print(e)
    return _tx

def getAccountInfo(_address, _id):
    regInfoURL = _AvalaunchAPIURL + "/projects/" + str(int(_id)) +"/register"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json; charset=utf-8",
        "x-wallet-address": _address,
    }
    try:
        r = apiSession.get(url=regInfoURL, headers=headers, timeout=10)
    except Exception as e:
        return []
    _info = r.json()
    return _info

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")

apiSession = requests.Session()

def main(_projectArg=""):
    _arg = ""
    salesInfoAPI = getAPISalesInfo()

    if len(_projectArg) == 0:
        for _project in salesInfoAPI:
            print(f'{_project["id"]:02}' + " : " + _project["title"]  + " : " + _project["contract_address"])
        quit()

    projectContract = ""
    selectedProject = None
    for _project in salesInfoAPI:
        if _projectArg.lower() in _project["title"].lower():
            selectedProject = _project
            break

        if  len(_projectArg)>10 and _projectArg.lower() in (_project["contract_address"].lower()):
            selectedProject = _project
            break

        if int(_projectArg) == int(_project["id"]):
            selectedProject = _project
            break        

    if selectedProject is None:
        print('Project ' + str(_projectArg) + ' not found')
        quit()

    print("Selected project:")
    print(f'{selectedProject["id"]:02}' + " : " + selectedProject["title"]  + " : " + selectedProject["contract_address"])
    # find contract for the selected sale

    # get range and count
    _txRangeStart = getTXJSON(_contract=selectedProject["contract_address"])
    _txRangeEnd = getTXJSON(_contract=selectedProject["contract_address"], _sort="desc")
    _txRange = _txRangeStart

    _txRange.extend(_txRangeEnd)

    first = _txRange[0]["blockNumber"]
    last = _txRange[len(_txRange) - 1]["blockNumber"]

    _txs = []
    for i in range(int(first), int(last), 5000):
        _txs.extend(
            getTXJSON(
                _contract=selectedProject["contract_address"], _start=i, _end=i + 4999
            )
        )
    statsFileName = slugify(selectedProject["title"]) + "_avalaunch_participations.csv"
    statsFileName_b = slugify(selectedProject["title"]) + "_avalaunch_participations_b.csv"
    fl = open(statsFileName, "w")
    fl_banned = open(statsFileName_b, "w")

    # checksum all addresses
    for i, _tx in enumerate(_txs):
        _txs[i]["from"] = Web3.toChecksumAddress(_tx["from"])

    # populate all sale info from transactions
    _sales = []
    j = 0
    for i, _tx in enumerate(_txs):
        # only first 500 transactions, let's not overload api

        # populate only the contract function registerForSale(bytes signature, uint256 roundId)
        if ("0xe9d8479e") not in _tx["input"]:
            continue
        try:
            if j > 50:
                break
            _sales.append(getAccountInfo(_tx["from"], selectedProject["id"]))
            j = j+1
            time.sleep(0.5)
        except Exception as e:
            print(e)


    for i, _accInfo in enumerate(_sales):
        if "registered_for" not in _accInfo:
            continue
        if _accInfo["is_banned"]:
            _accInfo["allocation"] = 0
        if _accInfo["user_country_code"] is None:
            _accInfo["user_country_code"] = "N/A"
        if _accInfo["registered_for"] == "Staking":
            _saleInfo = (
                "{:.2f}".format(float(_accInfo["amount_staking"]))
                + "; "
                + "{:.2f}".format(float(_accInfo["allocation"]))
                + ";"
                + _accInfo["user_country_code"]
                + ";"
                + str(float(_accInfo["allocation_percent"]))
            )
            if not _accInfo["is_banned"]:
                fl.write(_saleInfo + "\n")
            else:
                fl_banned.write(_saleInfo + "; " + _address + "\n")

    fl.close()
    fl_banned.close()


if __name__ == "__main__":
    print("---Avalaunch comunity tool - Sale stats---")

    print("")
    if len(sys.argv) > 1:
        main( re.sub(r'\W+', '', sys.argv[1].lower()) )
    else:
        print("Specify project:")
        
        print("add name, contract address or index number to the command line")
        print("ie. ")
        print( "python3 " + os.path.basename(__file__) + " 49" )
        print( "python3 " + os.path.basename(__file__) + " kalao")
        print( "python3 " + os.path.basename(__file__) + " 0x16Bc59978851012aDA4843E49Df2A314EA38665a")        
        print("")

        main()
