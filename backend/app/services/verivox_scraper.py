import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import logging

VERIVOX_URL = "https://www.verivox.de/strom/"

HOUSEHOLD_SIZE_TO_PERSONS = {
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
}

def scrape_verivox_offers(zip_code: str, kwh_per_year: int, household_size: int) -> List[Dict]:
    params = {
        "plz": zip_code,
        "verbrauch": kwh_per_year,
        "personen": HOUSEHOLD_SIZE_TO_PERSONS.get(household_size, 1),
        "onlyEco": 0,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    logging.info(f"Verivox request params: {params}")
    response = requests.get(VERIVOX_URL, params=params, headers=headers, timeout=20)
    logging.info(f"Verivox response status: {response.status_code}")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    offers = []
    offer_cards = soup.select('.tariff-list__item')
    logging.info(f"Found {len(offer_cards)} offer cards on Verivox")
    for card in offer_cards[:25]:
        provider = card.select_one('.tariff-list__provider-logo')
        provider_name = provider["alt"] if provider and provider.has_attr("alt") else "Unknown"
        price_el = card.select_one('.tariff-list__price')
        price = price_el.get_text(strip=True) if price_el else ""
        tariff_el = card.select_one('.tariff-list__tariff-name')
        tariff = tariff_el.get_text(strip=True) if tariff_el else ""
        green = bool(card.select_one('.tariff-list__eco-label'))
        # Service/local/tech: try to infer from text or icons
        service = 'service' in card.get_text().lower()
        local = 'stadtwerk' in card.get_text().lower() or 'regional' in card.get_text().lower()
        tech = 'app' in card.get_text().lower() or 'smart' in card.get_text().lower()
        offers.append({
            "provider": provider_name,
            "price": price,
            "tariff": tariff,
            "green": green,
            "service": service,
            "local": local,
            "tech": tech
        })
    return offers 