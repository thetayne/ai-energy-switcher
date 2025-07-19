import logging
logging.basicConfig(level=logging.INFO)

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.prompts import PromptTemplate
import os
import re
from .verivox_scraper import scrape_verivox_offers
from langchain.tools import Tool as LC_Tool

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Simple tool example (can be extended)
def energy_check_tool(input_text: str) -> str:
    energy_keywords = [
        'energy', 'strom', 'electricity', 'provider', 'tariff', 'switch', 'wechsel', 'energie', 'gas', 'contract', 'vertrag', 'power', 'renewable', 'green', 'kwh', 'kilowatt', 'verbrauch', 'rechnung', 'bill', 'anbieter', 'tarif', 'preis', 'cost', 'savings', 'discount', 'bonus', 'grundversorgung', 'sondertarif', 'öko', 'ökostrom'
    ]
    if any(word in input_text.lower() for word in energy_keywords):
        return "energy"
    return "not_energy"

energy_check = Tool(
    name="EnergyCheck",
    func=energy_check_tool,
    description="Checks if the inquiry is about energy or energy provider switching."
)

def extract_location(text):
    # Map number words to digits
    number_words = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }
    # Replace number words with digits
    for word, digit in number_words.items():
        text = re.sub(rf'\b{word}\b', digit, text, flags=re.IGNORECASE)
    # Accept 5 digits together, or separated by spaces/dashes
    digits = re.sub(r'[^0-9]', '', text)
    logging.info(f"Extracted digits for location: {digits}")
    if len(digits) == 5:
        return str(digits)
    return None

def extract_consumption(text, state=None):
    # Try to match with unit first (up to 5 digits)
    match = re.search(r'(\d{1,3}(?:,\d{3})*|\d{3,5})[^\d]{0,10}(kwh|kilowattstunden|kilowatt[- ]?hours?)', text, re.IGNORECASE)
    if match:
        num = match.group(1).replace(',', '')
        return num
    # Accept any 3-5 digit number (up to 50000) if asking for consumption
    if state and state.get('step') == 'ask_consumption':
        match = re.search(r'(\d{3,5})(?:[.,])?', text)
        if match:
            val = int(match.group(1))
            if 100 <= val <= 50000:
                return str(val)
    return None

def extract_cost(text, state=None):
    # Try to match with unit first (up to 4 digits)
    match = re.search(r'(\d{1,3}(?:,\d{3})*|\d{2,4})[^\d]{0,10}(euro|eur|€)', text, re.IGNORECASE)
    if match:
        num = match.group(1).replace(',', '')
        return num
    # Accept any 2-4 digit number (up to 5000) if asking for cost
    if state and state.get('step') == 'ask_cost':
        match = re.search(r'(\d{2,4})', text)
        if match:
            val = int(match.group(1))
            if 10 <= val <= 5000:
                return str(val)
    return None

def extract_preferences(text):
    prefs = []
    if 'green' in text.lower() or 'öko' in text.lower():
        prefs.append('green')
    if 'cost' in text.lower() or 'preis' in text.lower() or 'cheap' in text.lower():
        prefs.append('cost')
    if 'service' in text.lower() or 'support' in text.lower():
        prefs.append('service')
    if 'local' in text.lower() or 'stadtwerk' in text.lower():
        prefs.append('local')
    if 'tech' in text.lower():
        prefs.append('tech')
    return ', '.join(prefs) if prefs else None

def extract_household_size(text):
    # Only accept household size 1-5
    match = re.search(r'\b([1-5])\b', text)
    if match:
        return int(match.group(1))
    match = re.search(r'([1-5])\s*(person|people|haushalt|family)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5
    }
    for word, num in number_words.items():
        if re.search(rf'\b{word}\b', text, re.IGNORECASE):
            return num
    return None

def select_top_offers(offers, preferences):
    # Simple scoring: +2 for matching main pref, +1 for others
    scored = []
    prefs = preferences.lower().split(',') if preferences else []
    for offer in offers:
        score = 0
        if 'green' in prefs and offer['green']:
            score += 2
        if 'cost' in prefs:
            # Lower price is better
            price_num = int(''.join(filter(str.isdigit, offer['price']))) if offer['price'] else 0
            score += max(0, 10000 - price_num) // 1000
        if 'service' in prefs and offer['service']:
            score += 1
        if 'local' in prefs and offer['local']:
            score += 1
        if 'tech' in prefs and offer['tech']:
            score += 1
        scored.append((score, offer))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [x[1] for x in scored[:3]]

verivox_tool = LC_Tool(
    name="VerivoxProviderSearch",
    func=lambda zip_code, kwh, household: scrape_verivox_offers(zip_code, int(kwh), int(household)),
    description="Searches Verivox for electricity providers given zip code, kWh/year, and household size."
)

def run_agent(user_input: str, state: dict = None) -> dict:
    if state is None:
        state = {"active": False, "location": None, "household_size": None, "consumption": None, "cost": None, "preferences": None, "step": "ask_location"}
    # Reset logic (optional): if user says 'start over' or 'reset', clear state
    if 'start over' in user_input.lower() or 'reset' in user_input.lower():
        state = {"active": False, "location": None, "household_size": None, "consumption": None, "cost": None, "preferences": None, "step": "ask_location"}
        return {"agent_response": "Let's start over. Please ask an energy-related question to begin.", "state": state, "done": False}
    # Only check for energy intent if not active
    if not state.get("active", False):
        check_result = energy_check_tool(user_input)
        if check_result != "energy":
            return {
                "agent_response": "I'm here to help you switch your energy provider. Please ask an energy-related question!",
                "state": state,
                "done": False
            }
        # If energy-related, activate state
        state["active"] = True
    # Always try to extract info and update state
    if not state["location"]:
        loc = extract_location(user_input)
        if loc:
            state["location"] = loc

    if not state["location"] or not (isinstance(state["location"], str) and re.fullmatch(r'\d{5}', state["location"])):
        state["location"] = None
        state["step"] = "ask_location"
        logging.info(f"Current state after asking for location: {state}")
        return {"agent_response": "What is your 5-digit postal code (PLZ)?", "state": state, "done": False}
    if not state["household_size"]:
        hh = extract_household_size(user_input)
        if hh:
            state["household_size"] = hh
    if not state["consumption"]:
        cons = extract_consumption(user_input, state)
        if cons:
            state["consumption"] = cons
    if not state["cost"]:
        cost = extract_cost(user_input, state)
        if cost:
            state["cost"] = cost
    if not state["preferences"]:
        prefs = extract_preferences(user_input)
        if prefs:
            state["preferences"] = prefs
    # Ask for missing info
    if not state["location"] or not (isinstance(state["location"], str) and re.fullmatch(r'\d{5}', state["location"])):
        state["location"] = None
        state["step"] = "ask_location"
        logging.info(f"Current state after asking for location: {state}")
        return {"agent_response": "What is your 5-digit postal code (PLZ)?", "state": state, "done": False}
    if not state["household_size"]:
        state["step"] = "ask_household_size"
        logging.info(f"Current state after asking for household size: {state}")
        return {"agent_response": "How many people are in your household? (1-5)", "state": state, "done": False}
    if not state["consumption"]:
        state["step"] = "ask_consumption"
        logging.info(f"Current state after asking for consumption: {state}")
        return {"agent_response": "How much energy do you use per year? For example, how many kilowatt-hours (kWh) did you use last year?", "state": state, "done": False}
    if not state["cost"]:
        state["step"] = "ask_cost"
        logging.info(f"Current state after asking for cost: {state}")
        return {"agent_response": "How much are you currently paying per month or year?", "state": state, "done": False}
    if not state["preferences"]:
        state["step"] = "ask_preferences"
        logging.info(f"Current state after asking for preferences: {state}")
        return {"agent_response": "What do you value most in an energy provider? (green energy, low cost, customer service, local utility, tech support)", "state": state, "done": False}
    # All info collected
    logging.info(f"Current state before provider search: {state}")
    if state["location"] and state["household_size"] and state["consumption"] and state["cost"] and state["preferences"]:
        offers = scrape_verivox_offers(state["location"], state["consumption"], state["household_size"])
        top3 = select_top_offers(offers, state["preferences"])
        state["offers"] = top3
        response = "Here are the top 3 energy providers for you:\n"
        for idx, offer in enumerate(top3, 1):
            response += f"{idx}. {offer['provider']} - {offer['tariff']} - {offer['price']}"
            if offer['green']:
                response += " (Green)"
            if offer['local']:
                response += " (Local)"
            if offer['tech']:
                response += " (Tech)"
            response += "\n"
        return {
            "agent_response": response,
            "state": state,
            "done": True
        }
    return {
        "agent_response": "Thank you! I have all the information I need to find the best energy provider for you.",
        "state": state,
        "done": True
    } 