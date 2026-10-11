import time
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from dataclasses import dataclass
import gzip

CARD_PRICES_PATH = (
    Path(__file__).resolve().parents[2]
    / "LocalData"
    / "default-cards-20261009210547.jsonl.gz"
)
cardPrices: dict[str, str] = {}
MAX_CONCURRENT_CARD_SEARCHES = 4
AFK_REQUEST_TIMEOUT = (5, 20)


@dataclass
class Card:
    s: str    # Name/Set
    q: str    # Quantity
    l: str    # Level/Line
    sid: str  # Unique ID
    f: str    # Foil status
    price: str | None = None # Price
    image_url: str = "" # Image URL

    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        return cls(
            s=data.get('s', ''),
            q=data.get('q', ''),
            l=data.get('l', ''),
            sid=data.get('sid', ''),
            f=data.get('f', '')
        )


def load_card_prices() -> dict[str, str]:
    prices_by_id = {}
    with gzip.open(CARD_PRICES_PATH, "rt", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            card_data = json.loads(line)
            card_id = card_data.get("id")
            usd_price = card_data.get("prices", {}).get("usd")
            usd_foil_price = card_data.get("prices", {}).get("usd_foil")
            if card_id and usd_price is not None or usd_foil_price is not None:
                prices_by_id[card_id] = {"usd": usd_price, "usd_foil": usd_foil_price}
    return prices_by_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cardPrices
    cardPrices = load_card_prices()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    text: str
    printImages: bool = True
    ShowOnlyCheapest: bool = False


@app.get("/api/data")
def get_data():
    return {"status": "loaded", "card_count": len(cardPrices)}


@app.post("/search")
async def search(request: SearchRequest):
    start_time = time.perf_counter()
    cards = parse_card_list([request.text])
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CARD_SEARCHES)

    async def fetch_card(card_name):
        async with semaphore:
            return await asyncio.to_thread(
                FetchAllPrintings,
                card_name,
                printImages=request.printImages,
                showCheapestOnly=request.ShowOnlyCheapest,
            )

    card_printings = await asyncio.gather(*(fetch_card(card) for card in cards))
    cardsInStock = [
        {card_name: printings}
        for card_name, printings in zip(cards, card_printings)
        if printings
    ]

    end_time = time.perf_counter()
    print(f"\nSearch completed in {end_time - start_time:.2f} seconds.")

    return {"status": "received", "data": cardsInStock}

def print_progress_bar(iteration, total, length=40):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = "█" * filled_length + "-" * (length - filled_length)
    print(f"\rProgress: |{bar}| {percent}% Complete", end="", flush=True)

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

    response = requests.post(
        url, headers=headers, json=payload, timeout=AFK_REQUEST_TIMEOUT
    )
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

    response = requests.post(
        url, headers=headers, json=payload, timeout=AFK_REQUEST_TIMEOUT
    )
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
        # print(str(len(printingsInStock)) + " printings in stock")
        for i in range(len(printingsInStock)):
            isFoil = False
            if printingsInStock[i].f == 1:
                isFoil = True
            # print(printingsInStock[i].s + ": " + printingsInStock[i].q + " in stock! | Foil: " + str(isFoil))
            return True
    else:
        # print("Out of stock!")
        return False

def parse_card_list(raw_input_list):
    card_list = []

    if len(raw_input_list) == 1 and "\n" in raw_input_list[0]:
        lines_to_process = raw_input_list[0].split('\n')
    else:
        lines_to_process = raw_input_list

    ignored_titles = {"COMMANDER", "DECK", ""}

    for line in lines_to_process:
        cleaned_line = line.strip()

        if not cleaned_line or cleaned_line.upper() in ignored_titles:
            continue

        parts = cleaned_line.split(' ', 1)

        if parts[0].isdigit() and len(parts) > 1:
            card_name = parts[1]
            card_list.append(card_name)
        else:
            card_list.append(cleaned_line)

    card_list = list(dict.fromkeys(card_list))
    return card_list

def FetchAllPrintings(cardName, printImages=True, showCheapestOnly=False):
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


    response = requests.post(
        url, headers=headers, json=payload, timeout=AFK_REQUEST_TIMEOUT
    )
    jsonResponse = response.json()
    searchResults = json.loads(json.dumps(jsonResponse))
    resultList = searchResults["d"]

    bestList = json.loads(resultList)
    if bestList == []:
        return []
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
    response = requests.post(
        url, headers=headers, json=payload, timeout=AFK_REQUEST_TIMEOUT
    )
    jsonResponse = response.json()
    searchResults = json.loads(json.dumps(jsonResponse))
    resultList = searchResults["d"]
    cardList = json.loads(resultList)
    printingsInStock = []

    cheapestPrinting = None
    if showCheapestOnly:
        for i in range(len(cardList)):
            if int(cardList[i]["q"]) > 0:
                printing = Card(**cardList[i])
                if (printing.f == "1" and cardPrices.get(printing.sid) is not None):
                    printing.price = cardPrices[printing.sid]["usd_foil"]
                elif (printing.f == "0" and cardPrices.get(printing.sid) is not None):
                    printing.price = cardPrices[printing.sid]["usd"]
                if cheapestPrinting is None or (
                    printing.price is not None
                    and (
                        cheapestPrinting.price is None
                        or float(printing.price) < float(cheapestPrinting.price)
                    )
                ):
                    cheapestPrinting = printing
        if printImages and cheapestPrinting is not None:
            time.sleep(0.5)
            cheapestPrinting.image_url = GetScryfallImage(cheapestPrinting.sid)
    else:
        for i in range(len(cardList)):
            if int(cardList[i]["q"]) > 0:
                printing = Card(**cardList[i])
                if (printing.f == "1" and cardPrices.get(printing.sid) is not None):
                    printing.price = cardPrices[printing.sid]["usd_foil"]
                elif (printing.f == "0" and cardPrices.get(printing.sid) is not None):
                    printing.price = cardPrices[printing.sid]["usd"]
                if printImages:
                    time.sleep(0.5)
                    printing.image_url = GetScryfallImage(printing.sid)
                printingsInStock.append(printing)

    cards = [cheapestPrinting] if cheapestPrinting else []
    for i in range(len(printingsInStock)):
        cards.append(printingsInStock[i])
    return cards

def FetchCardValue(sid):
    return cardPrices.get(sid)

def GetScryfallImage(sid):
    headers = {
        "User-Agent": "BulkSearcher/1.0 ",
        "Accept": "application/json",
    }

    url = f"https://api.scryfall.com/cards/{sid}"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    card_data = response.json()

    if "image_uris" in card_data:
        return card_data["image_uris"].get("normal")

    for face in card_data.get("card_faces", []):
        image_url = face.get("image_uris", {}).get("normal")
        if image_url:
            return image_url

    return None

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)