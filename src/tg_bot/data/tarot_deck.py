from enum import Enum
from pathlib import Path
from typing import Dict, NamedTuple
from logger import bot_logger
import random 
from config import get_taro_image_path 

class Suit(Enum):
    CUPS = "cups" 
    PENTACLES = "pents"
    WANDS = "wands"
    SWORDS = "swords"

class CardInfo(NamedTuple):
    name: str
    image_filename: str
    suit: Suit # Масти

TAROT_DECK: Dict[str, CardInfo] = {
    "The Fool": CardInfo(name="The Fool", image_filename="00_shut.jpg", suit=None),
    "The Magician": CardInfo(name="The Magician", image_filename="01_mag.jpg", suit=None),
    "The High Priestes": CardInfo(name="The High Priestes", image_filename="02_zhrica.jpg", suit=None),
    "The Empress": CardInfo(name="The Empress", image_filename="03_impress.jpg", suit=None),
    "The Emperor": CardInfo(name="The Emperor", image_filename="04_imperor.jpg", suit=None),
    "The Hierophant": CardInfo(name="The Hierophant", image_filename="05_hierofant.jpg", suit=None),
    "The Lovers": CardInfo(name="The Lovers", image_filename="06_lovers.jpg", suit=None),
    "The Chariot": CardInfo(name="The Chariot", image_filename="07_chariot.jpg", suit=None),
    "The Strength": CardInfo(name="The Strength", image_filename="08_Strenghch.jpg", suit=None),
    "The Hermit": CardInfo(name="The Hermit", image_filename="09_hermit.jpg", suit=None),
    "The Wheel of Fortune": CardInfo(name="The Wheel of Fortune", image_filename="10_fortune.jpg", suit=None),
    "The Justice": CardInfo(name="The Justice", image_filename="11_justice.jpg", suit=None),
    "The Hanged Man": CardInfo(name="The Hanged Man", image_filename="12_hanged_men.jpg", suit=None),
    "The Death": CardInfo(name="The Death", image_filename="13_death.jpg", suit=None),
    "The Temperance": CardInfo(name="The Temperance", image_filename="14_temperam.jpg", suit=None),
    "The Devil": CardInfo(name="The Devil", image_filename="15_devil.jpg", suit=None),
    "The Tower": CardInfo(name="The Tower", image_filename="16_tower.jpg", suit=None),
    "The Star": CardInfo(name="The Star", image_filename="17_stare.jpg", suit=None),
    "The Moon": CardInfo(name="The Moon", image_filename="18_moon.jpg", suit=None),
    "The Sun": CardInfo(name="The Sun", image_filename="19_sun.jpg", suit=None),
    "The Judgement": CardInfo(name="The Judgement", image_filename="20_sud.jpg", suit=None),
    "The World": CardInfo(name="The World", image_filename="21_world.jpg", suit=None),

    "Ace of Swords": CardInfo(name="Ace of Swords", image_filename="22_swordS01.jpg", suit=Suit.SWORDS),
    "Two of Swords": CardInfo(name="Two of Swords", image_filename="23_swords02.jpg", suit=Suit.SWORDS),
    "Three of Swords": CardInfo(name="Three of Swords", image_filename="24_swords03.jpg", suit=Suit.SWORDS),
    "Four of Swords": CardInfo(name="Four of Swords", image_filename="24_swords04.jpg", suit=Suit.SWORDS),
    "Five of Swords": CardInfo(name="Five of Swords", image_filename="25_swords05.jpg", suit=Suit.SWORDS),
    "Six of Swords": CardInfo(name="Six of Swords", image_filename="26_swords06.jpg", suit=Suit.SWORDS),
    "Seven of Swords": CardInfo(name="Seven of Swords", image_filename="27_swords07.jpg", suit=Suit.SWORDS),
    "Eight of Swords": CardInfo(name="Eight of Swords", image_filename="28_swords08.jpg", suit=Suit.SWORDS),
    "Nine of Swords": CardInfo(name="Nine of Swords", image_filename="29_swords09.jpg", suit=Suit.SWORDS),
    "Ten of Swords": CardInfo(name="Ten of Swords", image_filename="30_swords10.jpg", suit=Suit.SWORDS),
    "Page of Swords": CardInfo(name="Page of Swords", image_filename="31_swords11.jpg", suit=Suit.SWORDS),
    "Knight of Swords": CardInfo(name="Knight of Swords", image_filename="32_swords12.jpg", suit=Suit.SWORDS),
    "Queen of Swords": CardInfo(name="Queen of Swords", image_filename="33_swords13.jpg", suit=Suit.SWORDS),
    "King of Swords": CardInfo(name="King of Swords", image_filename="34_sword14s.jpg", suit=Suit.SWORDS),
    
    "Ace of Wands": CardInfo(name="Ace of Wands", image_filename="35_wands01.jpg", suit=Suit.WANDS),
    "Two of Wands": CardInfo(name="Two of Wands", image_filename="36_wands02.jpg", suit=Suit.WANDS),
    "Three of Wands": CardInfo(name="Three of Wands", image_filename="37_wands03.jpg", suit=Suit.WANDS),
    "Four of Wands": CardInfo(name="Four of Wands", image_filename="38_wands04.jpg", suit=Suit.WANDS),
    "Five of Wands": CardInfo(name="Five of Wands", image_filename="39_wands05.jpg", suit=Suit.WANDS),
    "Six of Wands": CardInfo(name="Six of Wands", image_filename="40_wands06.jpg", suit=Suit.WANDS),
    "Seven of Wands": CardInfo(name="Seven of Wands", image_filename="41_wands07.jpg", suit=Suit.WANDS),
    "Eight of Wands": CardInfo(name="Eight of Wands", image_filename="42_wands08.jpg", suit=Suit.WANDS),
    "Nine of Wands": CardInfo(name="Nine of Wands", image_filename="43_wands09.jpg", suit=Suit.WANDS),
    "Ten of Wands": CardInfo(name="Ten of Wands", image_filename="44_wands10.jpg", suit=Suit.WANDS),
    "Page of Wands": CardInfo(name="Page of Wands", image_filename="45_wands11.jpg", suit=Suit.WANDS),
    "Knight of Wands": CardInfo(name="Knight of Wands", image_filename="46_wands12.jpg", suit=Suit.WANDS),
    "Queen of Wands": CardInfo(name="Queen of Wands", image_filename="47_wands13.jpg", suit=Suit.WANDS),
    "King of Wands": CardInfo(name="King of Wands", image_filename="48_wands14.jpg", suit=Suit.WANDS),
    
    "Ace of Pentacles": CardInfo(name="Ace of Pentacles", image_filename="49_pents01.jpg", suit=Suit.PENTACLES),
    "Two of Pentacles": CardInfo(name="Two of Pentacles", image_filename="50_pents02.jpg", suit=Suit.PENTACLES),
    "Three of Pentacles": CardInfo(name="Three of Pentacles", image_filename="51_pents03.jpg", suit=Suit.PENTACLES),
    "Four of Pentacles": CardInfo(name="Four of Pentacles", image_filename="52_pents04.jpg", suit=Suit.PENTACLES),
    "Five of Pentacles": CardInfo(name="Five of Pentacles", image_filename="53_pents05.jpg", suit=Suit.PENTACLES),
    "Six of Pentacles": CardInfo(name="Six of Pentacles", image_filename="54_pents06.jpg", suit=Suit.PENTACLES),
    "Seven of Pentacles": CardInfo(name="Seven of Pentacles", image_filename="55_pents07.jpg", suit=Suit.PENTACLES),
    "Eight of Pentacles": CardInfo(name="Eight of Pentacles", image_filename="56_pents08.jpg", suit=Suit.PENTACLES),
    "Nine of Pentacles": CardInfo(name="Nine of Pentacles", image_filename="57_pents09.jpg", suit=Suit.PENTACLES),
    "Ten of Pentacles": CardInfo(name="Ten of Pentacles", image_filename="58_pents10.jpg", suit=Suit.PENTACLES),
    "Page of Pentacles": CardInfo(name="Page of Pentacles", image_filename="59_pents11.jpg", suit=Suit.PENTACLES),
    "Knight of Pentacles": CardInfo(name="Knight of Pentacles", image_filename="60_pents12.jpg", suit=Suit.PENTACLES),
    "Queen of Pentacles": CardInfo(name="Queen of Pentacles", image_filename="61_pents13.jpg", suit=Suit.PENTACLES),
    "King of Pentacles": CardInfo(name="King of Pentacles", image_filename="62_pents14.jpg", suit=Suit.PENTACLES),
    
    "Ace of Cups": CardInfo(name="Ace of Cups", image_filename="63_cups01.jpg", suit=Suit.CUPS),
    "Two of Cups": CardInfo(name="Two of Cups", image_filename="64_cups02.jpg", suit=Suit.CUPS),
    "Three of Cups": CardInfo(name="Three of Cups", image_filename="65_cups03.jpg", suit=Suit.CUPS),
    "Four of Cups": CardInfo(name="Four of Cups", image_filename="66_cups04.jpg", suit=Suit.CUPS),
    "Five of Cups": CardInfo(name="Five of Cups", image_filename="67_cups05.jpg", suit=Suit.CUPS),
    "Six of Cups": CardInfo(name="Six of Cups", image_filename="68_cups06.jpg", suit=Suit.CUPS),
    "Seven of Cups": CardInfo(name="Seven of Cups", image_filename="69_cups07.jpg", suit=Suit.CUPS),
    "Eight of Cups": CardInfo(name="Eight of Cups", image_filename="70_cups08.jpg", suit=Suit.CUPS),
    "Nine of Cups": CardInfo(name="Nine of Cups", image_filename="71_cups09.jpg", suit=Suit.CUPS),
    "Ten of Cups": CardInfo(name="Ten of Cups", image_filename="72_cups10.jpg", suit=Suit.CUPS),
    "Page of Cups": CardInfo(name="Page of Cups", image_filename="73_cups11.jpg", suit=Suit.CUPS),
    "Knight of Cups": CardInfo(name="Knight of Cups", image_filename="74_cups12.jpg", suit=Suit.CUPS),
    "Queen of Cups": CardInfo(name="Queen of Cups", image_filename="75_cups13.jpg", suit=Suit.CUPS),
    "King of Cups": CardInfo(name="King of Cups", image_filename="76_cups14.jpg", suit=Suit.CUPS),   
}

def get_card_info(card_name: str) -> CardInfo:
    card_info = TAROT_DECK.get(card_name)
    if not card_info:
        raise ValueError(f"Card '{card_name}' not found in the deck")
    return card_info

def get_card_image_path(card_name: str) -> Path:
    bot_logger.debug(f"[TarotDeck] get_card_image_path called for card: '{card_name}'")
    
    card_info = get_card_info(card_name)
    image_path = get_taro_image_path(card_info.image_filename)
    
    bot_logger.debug(f"[Tarot] Image path for card '{card_name}': {image_path}")
    return image_path

def draw_random_cards(count: int = 1) -> list[str]:
    all_card_names = list(TAROT_DECK.keys())
    return random.sample(all_card_names, k=min(count, len(all_card_names)))

