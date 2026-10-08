import requests
import json
from dataclasses import dataclass

@dataclass
class Card:
    s: str    # Name/Set (e.g., "Modern Horizons 3 Commander")
    q: str    # Quantity (e.g., "0")
    l: str    # Level/Line (e.g., "1")
    sid: str  # Unique ID (e.g., "2995201b-22c7...")
    f: str    # Foil status or flag (e.g., "0")

    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        return cls(
            s=data.get('s', ''),
            q=data.get('q', ''),
            l=data.get('l', ''),
            sid=data.get('sid', ''),
            f=data.get('f', '')
        )


def FetchCardId(cardName):
    url = "https://mtg.afk.games/AFKMTG.asmx/cardNameSearch"

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json; charset=UTF-8",
        "priority": "u=1, i",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "referer": "https://mtg.afk.games/"
    }

    payload = {
        "search": cardName
    }

    response = requests.post(url, headers=headers, json=payload)
    jsonResponse = response.json()
    searchResults = json.loads(json.dumps(jsonResponse))
    resultList = searchResults["d"]
    # clean_string = resultList.rsplit('},', 1)[0] + '}]'
    # print(clean_string)

    bestList = json.loads(resultList)
    return bestList[0]["cid"]

def findInStock(cid):
    url = "https://mtg.afk.games/AFKMTG.asmx/cardsbycid"
    
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json; charset=UTF-8",
        "priority": "u=1, i",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "referer": "https://mtg.afk.games/"
    }

    payload = {
        "cid": cid
    }
    
    response = requests.post(url, headers=headers, json=payload)
    jsonResponse = response.json()
    searchResults = json.loads(json.dumps(jsonResponse))
    resultList = searchResults["d"]
    bestList = json.loads(resultList)
    printingsInStock = []
    for i in range(len(bestList)):
        if int(bestList[i]["q"]) > 0:
            printing = Card(**bestList[i])
            printingsInStock.append(printing)

    if len(printingsInStock) > 0:
        print(str(len(printingsInStock)) + " printings in stock")
        for i in range(len(printingsInStock)):
            isFoil = False
            if printingsInStock[i].f == 1:
                isFoil = True
            print(printingsInStock[i].s + ": " + printingsInStock[i].q + " in stock! | Foil: " + str(isFoil))
    else:
        print("Out of stock!")




cardId = FetchCardId("Brightglass Gearhulk")

if (cardId is not None):
    findInStock(cardId)
