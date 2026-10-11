import requests
import json
from dataclasses import dataclass
import sys
import gzip

@dataclass
class Card:
    s: str    # Name/Set 
    q: str    # Quantity 
    l: str    # Level/Line 
    sid: str  # Unique ID 
    f: str    # Foil status

    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        return cls(
            s=data.get('s', ''),
            q=data.get('q', ''),
            l=data.get('l', ''),
            sid=data.get('sid', ''),
            f=data.get('f', '')
        )


def FetchCardValue(sid):
    file_path = "LocalData/default-cards-20261009210547.jsonl.gz"

    with gzip.open(file_path, "rt", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            card_data = json.loads(line)

            if card_data.get("id") == sid:
                return card_data["prices"]["usd"]

    return None
    # try:
    #    print(card_prices["data"][sid])
    # except KeyError:
    #    print("Printing not found")

    # url = f"https://api.scryfall.com/cards/{sid}"
    #
    # headers = {
    #     "accept": "application/json, text/javascript, */*; q=0.01",
    #     "accept-language": "en-US,en;q=0.9",
    #     "content-type": "application/json; charset=UTF-8",
    #     "User-Agent": "BulkCardSearch/1.0 (your@email.com)",
    # }
    #
    # response = requests.get(url, headers=headers)
    #
    # if response.status_code == 200:
    #     card_data = response.json()
    #
    #     # Extract card name and price dictionary
    #     card_name = card_data.get("name")
    #     prices = card_data.get("prices", {})
    #
    #     print(f"Card: {card_name}")
    #     print(f"USD (Normal): ${prices.get('usd')}")
    #     print(f"USD (Foil):   ${prices.get('usd_foil')}")
    #     print(f"EUR (Normal): €{prices.get('eur')}")
    #     print(f"TIX (MTGO):   {prices.get('tix')} tix")
    #
    #     return prices
    # elif response.status_code == 404:
    #     print(f"Error: Card with ID {sid} not found.")
    # else:
    #     print(f"Error: HTTP {response.status_code}")

def FetchCardByName(cardName):
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

    bestList = json.loads(resultList)
    cid = bestList[0]["cid"]

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
    cardList = json.loads(resultList)
    cards = []
    for i in range(len(cardList)):
        card = Card(**cardList[i])
        cards.append(card)
    return cards

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
        #print(str(len(printingsInStock)) + " printings in stock")
        for i in range(len(printingsInStock)):
            isFoil = False
            if printingsInStock[i].f == 1:
                isFoil = True
            #print(printingsInStock[i].s + ": " + printingsInStock[i].q + " in stock! | Foil: " + str(isFoil))
            return True
    else:
        #print("Out of stock!")
        return False


def parse_card_list(file_path):
    card_list = []
    
    ignored_titles = {"Commander", "Deck", ""}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            cleaned_line = line.strip()
            
            if not cleaned_line or cleaned_line.upper() in ignored_titles:
                continue
            
            parts = cleaned_line.split(' ', 1)
            
            if parts[0].isdigit() and len(parts) > 1:
                card_name = parts[1]
                card_list.append(card_name)
            else:
                card_list.append(cleaned_line)
                
    return card_list

def print_progress_bar(iteration, total, length=40):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = "█" * filled_length + "-" * (length - filled_length)
    print(f"\rProgress: |{bar}| {percent}% Complete", end="", flush=True)

cards = parse_card_list('MTG.txt')
cardsInStock = []
total_steps = len(cards)
for i in range(len(cards)):

    cardId = FetchCardId(cards[i])

    if (cardId is not None):
        isInStock = findInStock(cardId)
        if isInStock:
            cardsInStock.append(cards[i])
    print_progress_bar(i, total_steps - 1)

print()
#
# if len(cardsInStock) > 0:
#     print("Cards in stock: ")
#     for i in range(len(cardsInStock)):
#         print(cardsInStock[i])
#
# if len(cardsInStock) < len(cards):
#     print()
#     print("Cards not at AFK: ")
#     missingCards = list(set(cards) - set(cardsInStock))
#     for i in range(len(missingCards)):
#             print(missingCards[i])
# print()
# print("AFK has " + str(len(cardsInStock)) + " of the " + str(len(cards)) + " needed.")

# cardToPriceSearch = FetchCardByName("Sol Ring")
# print(cardToPriceSearch[0].sid)
# FetchCardValue(cardToPriceSearch[0].sid)

# for i in range(0, len(cardToPriceSearch)):
#     print(cardToPriceSearch[i].sid)
#     FetchCardValue(cardToPriceSearch[i].sid)


