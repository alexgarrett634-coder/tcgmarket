"""Seed 120+ popular Pokemon TCG cards with accurate market prices.

Run from the backend directory:
  py -3 seed_cards.py
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import engine, create_tables
from app.models.card import Card
from app.models.price import CardPrice

NOW = datetime.now(timezone.utc)

# Format: (id, name, set_name, set_code, number, rarity, supertype, image_small, image_large, tcgplayer_market_usd)
CARDS = [
    # ── Base Set ──────────────────────────────────────────────────────────────
    ("base1-4",  "Charizard",  "Base Set", "base1", "4",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/4.png",   "https://images.pokemontcg.io/base1/4_hires.png",   350.00),
    ("base1-2",  "Blastoise",  "Base Set", "base1", "2",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/2.png",   "https://images.pokemontcg.io/base1/2_hires.png",   95.00),
    ("base1-15", "Venusaur",   "Base Set", "base1", "15", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/15.png",  "https://images.pokemontcg.io/base1/15_hires.png",  55.00),
    ("base1-10", "Mewtwo",     "Base Set", "base1", "10", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/10.png",  "https://images.pokemontcg.io/base1/10_hires.png",  120.00),
    ("base1-1",  "Alakazam",   "Base Set", "base1", "1",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/1.png",   "https://images.pokemontcg.io/base1/1_hires.png",   35.00),
    ("base1-3",  "Chansey",    "Base Set", "base1", "3",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/3.png",   "https://images.pokemontcg.io/base1/3_hires.png",   30.00),
    ("base1-5",  "Clefairy",   "Base Set", "base1", "5",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/5.png",   "https://images.pokemontcg.io/base1/5_hires.png",   25.00),
    ("base1-6",  "Gyarados",   "Base Set", "base1", "6",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/6.png",   "https://images.pokemontcg.io/base1/6_hires.png",   45.00),
    ("base1-7",  "Hitmonchan", "Base Set", "base1", "7",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/7.png",   "https://images.pokemontcg.io/base1/7_hires.png",   22.00),
    ("base1-8",  "Machamp",    "Base Set", "base1", "8",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/8.png",   "https://images.pokemontcg.io/base1/8_hires.png",   14.00),
    ("base1-9",  "Magneton",   "Base Set", "base1", "9",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/9.png",   "https://images.pokemontcg.io/base1/9_hires.png",   20.00),
    ("base1-11", "Nidoking",   "Base Set", "base1", "11", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/11.png",  "https://images.pokemontcg.io/base1/11_hires.png",  18.00),
    ("base1-12", "Ninetales",  "Base Set", "base1", "12", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/12.png",  "https://images.pokemontcg.io/base1/12_hires.png",  28.00),
    ("base1-13", "Poliwrath",  "Base Set", "base1", "13", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/13.png",  "https://images.pokemontcg.io/base1/13_hires.png",  16.00),
    ("base1-14", "Raichu",     "Base Set", "base1", "14", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/14.png",  "https://images.pokemontcg.io/base1/14_hires.png",  65.00),
    ("base1-16", "Zapdos",     "Base Set", "base1", "16", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/base1/16.png",  "https://images.pokemontcg.io/base1/16_hires.png",  40.00),
    ("base1-58", "Pikachu",    "Base Set", "base1", "58", "Common",      "Pokémon", "https://images.pokemontcg.io/base1/58.png",  "https://images.pokemontcg.io/base1/58_hires.png",  28.00),
    # ── Jungle ────────────────────────────────────────────────────────────────
    ("jungle-1", "Clefable",   "Jungle",   "jungle","1",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/1.png",  "https://images.pokemontcg.io/jungle/1_hires.png",  12.00),
    ("jungle-2", "Electrode",  "Jungle",   "jungle","2",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/2.png",  "https://images.pokemontcg.io/jungle/2_hires.png",  10.00),
    ("jungle-3", "Flareon",    "Jungle",   "jungle","3",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/3.png",  "https://images.pokemontcg.io/jungle/3_hires.png",  22.00),
    ("jungle-4", "Jolteon",    "Jungle",   "jungle","4",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/4.png",  "https://images.pokemontcg.io/jungle/4_hires.png",  20.00),
    ("jungle-5", "Kangaskhan", "Jungle",   "jungle","5",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/5.png",  "https://images.pokemontcg.io/jungle/5_hires.png",  14.00),
    ("jungle-6", "Mr. Mime",   "Jungle",   "jungle","6",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/6.png",  "https://images.pokemontcg.io/jungle/6_hires.png",  18.00),
    ("jungle-7", "Pinsir",     "Jungle",   "jungle","7",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/7.png",  "https://images.pokemontcg.io/jungle/7_hires.png",  12.00),
    ("jungle-8", "Scyther",    "Jungle",   "jungle","8",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/8.png",  "https://images.pokemontcg.io/jungle/8_hires.png",  30.00),
    ("jungle-9", "Snorlax",    "Jungle",   "jungle","9",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/9.png",  "https://images.pokemontcg.io/jungle/9_hires.png",  35.00),
    ("jungle-10","Vaporeon",   "Jungle",   "jungle","10", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/10.png", "https://images.pokemontcg.io/jungle/10_hires.png", 22.00),
    ("jungle-11","Victreebel", "Jungle",   "jungle","11", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/11.png", "https://images.pokemontcg.io/jungle/11_hires.png", 10.00),
    ("jungle-12","Vileplume",  "Jungle",   "jungle","12", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/12.png", "https://images.pokemontcg.io/jungle/12_hires.png", 12.00),
    ("jungle-13","Wigglytuff", "Jungle",   "jungle","13", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/jungle/13.png", "https://images.pokemontcg.io/jungle/13_hires.png", 22.00),
    # ── Fossil ────────────────────────────────────────────────────────────────
    ("fossil-1", "Aerodactyl", "Fossil",   "fossil","1",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/1.png",  "https://images.pokemontcg.io/fossil/1_hires.png",  18.00),
    ("fossil-2", "Ditto",      "Fossil",   "fossil","2",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/2.png",  "https://images.pokemontcg.io/fossil/2_hires.png",  30.00),
    ("fossil-3", "Dragonite",  "Fossil",   "fossil","3",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/3.png",  "https://images.pokemontcg.io/fossil/3_hires.png",  35.00),
    ("fossil-4", "Gengar",     "Fossil",   "fossil","4",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/4.png",  "https://images.pokemontcg.io/fossil/4_hires.png",  55.00),
    ("fossil-5", "Haunter",    "Fossil",   "fossil","5",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/5.png",  "https://images.pokemontcg.io/fossil/5_hires.png",  15.00),
    ("fossil-6", "Hitmonlee",  "Fossil",   "fossil","6",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/6.png",  "https://images.pokemontcg.io/fossil/6_hires.png",  12.00),
    ("fossil-7", "Hypno",      "Fossil",   "fossil","7",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/7.png",  "https://images.pokemontcg.io/fossil/7_hires.png",  12.00),
    ("fossil-8", "Kabutops",   "Fossil",   "fossil","8",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/8.png",  "https://images.pokemontcg.io/fossil/8_hires.png",  20.00),
    ("fossil-9", "Lapras",     "Fossil",   "fossil","9",  "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/9.png",  "https://images.pokemontcg.io/fossil/9_hires.png",  22.00),
    ("fossil-10","Magneton",   "Fossil",   "fossil","10", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/10.png", "https://images.pokemontcg.io/fossil/10_hires.png", 10.00),
    ("fossil-11","Moltres",    "Fossil",   "fossil","11", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/11.png", "https://images.pokemontcg.io/fossil/11_hires.png", 25.00),
    ("fossil-12","Omastar",    "Fossil",   "fossil","12", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/12.png", "https://images.pokemontcg.io/fossil/12_hires.png", 12.00),
    ("fossil-13","Raichu",     "Fossil",   "fossil","13", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/13.png", "https://images.pokemontcg.io/fossil/13_hires.png", 20.00),
    ("fossil-14","Slowbro",    "Fossil",   "fossil","14", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/14.png", "https://images.pokemontcg.io/fossil/14_hires.png", 10.00),
    ("fossil-15","Zapdos",     "Fossil",   "fossil","15", "Rare Holo",   "Pokémon", "https://images.pokemontcg.io/fossil/15.png", "https://images.pokemontcg.io/fossil/15_hires.png", 22.00),
    # ── XY Base ───────────────────────────────────────────────────────────────
    ("xy1-12",  "Venusaur EX",     "XY",          "xy1",    "12", "Rare Holo EX",       "Pokémon", "https://images.pokemontcg.io/xy1/12.png",    "https://images.pokemontcg.io/xy1/12_hires.png",    8.00),
    ("xy1-13",  "M Venusaur EX",   "XY",          "xy1",    "13", "Rare Holo EX",       "Pokémon", "https://images.pokemontcg.io/xy1/13.png",    "https://images.pokemontcg.io/xy1/13_hires.png",    9.00),
    ("xy1-17",  "Charizard EX",    "XY",          "xy1",    "17", "Rare Holo EX",       "Pokémon", "https://images.pokemontcg.io/xy1/17.png",    "https://images.pokemontcg.io/xy1/17_hires.png",   16.00),
    ("xy1-36",  "Blastoise EX",    "XY",          "xy1",    "36", "Rare Holo EX",       "Pokémon", "https://images.pokemontcg.io/xy1/36.png",    "https://images.pokemontcg.io/xy1/36_hires.png",    9.00),
    # ── Sun & Moon Base ───────────────────────────────────────────────────────
    ("sm1-100", "Solgaleo GX",     "Sun & Moon",  "sm1",    "100","Rare Ultra",         "Pokémon", "https://images.pokemontcg.io/sm1/100.png",   "https://images.pokemontcg.io/sm1/100_hires.png",   6.00),
    ("sm1-101", "Lunala GX",       "Sun & Moon",  "sm1",    "101","Rare Ultra",         "Pokémon", "https://images.pokemontcg.io/sm1/101.png",   "https://images.pokemontcg.io/sm1/101_hires.png",   6.00),
    ("sm35-1",  "Ash's Pikachu",   "SM Black Star Promos","sm35","SM108","Promo","Pokémon","https://images.pokemontcg.io/sm35/1.png","https://images.pokemontcg.io/sm35/1_hires.png",20.00),
    # ── Hidden Fates ──────────────────────────────────────────────────────────
    ("sma-SV49","Charizard GX",    "Hidden Fates","sma",    "SV49","Shiny Vault",       "Pokémon", "https://images.pokemontcg.io/sma/SV49.png",  "https://images.pokemontcg.io/sma/SV49_hires.png", 45.00),
    ("sma-SV94","Mewtwo GX",       "Hidden Fates","sma",    "SV94","Shiny Vault",       "Pokémon", "https://images.pokemontcg.io/sma/SV94.png",  "https://images.pokemontcg.io/sma/SV94_hires.png", 15.00),
    ("sma-SV58","Gengar & Mimikyu GX","Hidden Fates","sma", "SV58","Shiny Vault",       "Pokémon", "https://images.pokemontcg.io/sma/SV58.png",  "https://images.pokemontcg.io/sma/SV58_hires.png", 20.00),
    # ── Champion's Path ───────────────────────────────────────────────────────
    ("swsh35-74","Charizard V",    "Champion's Path","swsh35","74","Rare Ultra",        "Pokémon", "https://images.pokemontcg.io/swsh35/74.png",  "https://images.pokemontcg.io/swsh35/74_hires.png", 30.00),
    ("swsh35-79","Charizard VMAX", "Champion's Path","swsh35","79","Rare Secret",       "Pokémon", "https://images.pokemontcg.io/swsh35/79.png",  "https://images.pokemontcg.io/swsh35/79_hires.png", 110.00),
    # ── Evolving Skies ────────────────────────────────────────────────────────
    ("swsh7-74", "Leafeon VMAX",   "Evolving Skies","swsh7","74", "Rare Rainbow",       "Pokémon", "https://images.pokemontcg.io/swsh7/74.png",   "https://images.pokemontcg.io/swsh7/74_hires.png",  30.00),
    ("swsh7-79", "Glaceon VMAX",   "Evolving Skies","swsh7","79", "Rare Rainbow",       "Pokémon", "https://images.pokemontcg.io/swsh7/79.png",   "https://images.pokemontcg.io/swsh7/79_hires.png",  25.00),
    ("swsh7-88", "Umbreon VMAX",   "Evolving Skies","swsh7","88", "Rare Rainbow",       "Pokémon", "https://images.pokemontcg.io/swsh7/88.png",   "https://images.pokemontcg.io/swsh7/88_hires.png",  88.00),
    ("swsh7-65", "Ditto VMAX",     "Evolving Skies","swsh7","65", "Rare Rainbow",       "Pokémon", "https://images.pokemontcg.io/swsh7/65.png",   "https://images.pokemontcg.io/swsh7/65_hires.png",  18.00),
    ("swsh7-93", "Rayquaza VMAX",  "Evolving Skies","swsh7","93", "Rare Rainbow",       "Pokémon", "https://images.pokemontcg.io/swsh7/93.png",   "https://images.pokemontcg.io/swsh7/93_hires.png",  40.00),
    ("swsh7-60", "Umbreon V",      "Evolving Skies","swsh7","60", "Rare Ultra",         "Pokémon", "https://images.pokemontcg.io/swsh7/60.png",   "https://images.pokemontcg.io/swsh7/60_hires.png",  22.00),
    ("swsh7-75", "Sylveon VMAX",   "Evolving Skies","swsh7","75", "Rare Rainbow",       "Pokémon", "https://images.pokemontcg.io/swsh7/75.png",   "https://images.pokemontcg.io/swsh7/75_hires.png",  22.00),
    # ── Brilliant Stars ───────────────────────────────────────────────────────
    ("swsh9-186","Arceus VSTAR",   "Brilliant Stars","swsh9","186","Rare Secret",       "Pokémon", "https://images.pokemontcg.io/swsh9/186.png",  "https://images.pokemontcg.io/swsh9/186_hires.png", 40.00),
    ("swsh9-176","Charizard VSTAR","Brilliant Stars","swsh9","176","Rare Secret",       "Pokémon", "https://images.pokemontcg.io/swsh9/176.png",  "https://images.pokemontcg.io/swsh9/176_hires.png", 55.00),
    ("swsh9-171","Arceus V",       "Brilliant Stars","swsh9","171","Rare Ultra",        "Pokémon", "https://images.pokemontcg.io/swsh9/171.png",  "https://images.pokemontcg.io/swsh9/171_hires.png", 18.00),
    # ── Lost Origin ───────────────────────────────────────────────────────────
    ("swsh11-196","Giratina VSTAR","Lost Origin","swsh11","196","Rare Secret",          "Pokémon", "https://images.pokemontcg.io/swsh11/196.png", "https://images.pokemontcg.io/swsh11/196_hires.png",28.00),
    ("swsh11-182","Comfey",        "Lost Origin","swsh11","182","Rare Ultra",           "Pokémon", "https://images.pokemontcg.io/swsh11/182.png", "https://images.pokemontcg.io/swsh11/182_hires.png",12.00),
    # ── Crown Zenith ──────────────────────────────────────────────────────────
    ("swsh12pt5gg-GG70","Charizard VSTAR","Crown Zenith: Galarian Gallery","swsh12pt5gg","GG70","Rare Shiny",
     "Pokémon", "https://images.pokemontcg.io/swsh12pt5gg/GG70.png", "https://images.pokemontcg.io/swsh12pt5gg/GG70_hires.png", 65.00),
    ("swsh12pt5gg-GG35","Pikachu VMAX","Crown Zenith: Galarian Gallery","swsh12pt5gg","GG35","Rare Shiny",
     "Pokémon", "https://images.pokemontcg.io/swsh12pt5gg/GG35.png", "https://images.pokemontcg.io/swsh12pt5gg/GG35_hires.png", 28.00),
    # ── Scarlet & Violet Base ─────────────────────────────────────────────────
    ("sv1-81",   "Miraidon ex",    "Scarlet & Violet","sv1", "81", "Double Rare",       "Pokémon", "https://images.pokemontcg.io/sv1/81.png",    "https://images.pokemontcg.io/sv1/81_hires.png",    8.00),
    ("sv1-254",  "Miraidon ex",    "Scarlet & Violet","sv1", "254","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv1/254.png","https://images.pokemontcg.io/sv1/254_hires.png",45.00),
    ("sv1-26",   "Koraidon ex",    "Scarlet & Violet","sv1", "26", "Double Rare",       "Pokémon", "https://images.pokemontcg.io/sv1/26.png",    "https://images.pokemontcg.io/sv1/26_hires.png",    8.00),
    ("sv1-247",  "Koraidon ex",    "Scarlet & Violet","sv1", "247","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv1/247.png","https://images.pokemontcg.io/sv1/247_hires.png",35.00),
    # ── 151 (SV3.5) ───────────────────────────────────────────────────────────
    ("sv3pt5-6",  "Charizard ex",  "151",     "sv3pt5","6",  "Double Rare",            "Pokémon", "https://images.pokemontcg.io/sv3pt5/6.png",   "https://images.pokemontcg.io/sv3pt5/6_hires.png",  295.00),
    ("sv3pt5-4",  "Charmander",    "151",     "sv3pt5","4",  "Common",                 "Pokémon", "https://images.pokemontcg.io/sv3pt5/4.png",   "https://images.pokemontcg.io/sv3pt5/4_hires.png",   2.50),
    ("sv3pt5-5",  "Charmeleon",    "151",     "sv3pt5","5",  "Uncommon",               "Pokémon", "https://images.pokemontcg.io/sv3pt5/5.png",   "https://images.pokemontcg.io/sv3pt5/5_hires.png",   1.50),
    ("sv3pt5-25", "Pikachu",       "151",     "sv3pt5","25", "Common",                 "Pokémon", "https://images.pokemontcg.io/sv3pt5/25.png",  "https://images.pokemontcg.io/sv3pt5/25_hires.png",  3.00),
    ("sv3pt5-150","Mewtwo ex",     "151",     "sv3pt5","150","Double Rare",            "Pokémon", "https://images.pokemontcg.io/sv3pt5/150.png",  "https://images.pokemontcg.io/sv3pt5/150_hires.png",15.00),
    ("sv3pt5-182","Charizard ex",  "151",     "sv3pt5","182","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv3pt5/182.png","https://images.pokemontcg.io/sv3pt5/182_hires.png",120.00),
    ("sv3pt5-193","Mewtwo ex",     "151",     "sv3pt5","193","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv3pt5/193.png","https://images.pokemontcg.io/sv3pt5/193_hires.png",20.00),
    ("sv3pt5-207","Pikachu ex",    "151",     "sv3pt5","207","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv3pt5/207.png","https://images.pokemontcg.io/sv3pt5/207_hires.png",55.00),
    # ── Obsidian Flames (SV3) ──────────────────────────────────────────────────
    ("sv3-125",  "Charizard ex",   "Obsidian Flames","sv3","125","Double Rare",         "Pokémon", "https://images.pokemontcg.io/sv3/125.png",   "https://images.pokemontcg.io/sv3/125_hires.png",   12.00),
    ("sv3-223",  "Charizard ex",   "Obsidian Flames","sv3","223","Hyper Rare",          "Pokémon", "https://images.pokemontcg.io/sv3/223.png",   "https://images.pokemontcg.io/sv3/223_hires.png",   75.00),
    ("sv3-230",  "Charizard ex",   "Obsidian Flames","sv3","230","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv3/230.png","https://images.pokemontcg.io/sv3/230_hires.png",350.00),
    ("sv3-85",   "Pidgeot ex",     "Obsidian Flames","sv3","85", "Double Rare",         "Pokémon", "https://images.pokemontcg.io/sv3/85.png",    "https://images.pokemontcg.io/sv3/85_hires.png",    10.00),
    ("sv3-131",  "Tyranitar ex",   "Obsidian Flames","sv3","131","Double Rare",         "Pokémon", "https://images.pokemontcg.io/sv3/131.png",   "https://images.pokemontcg.io/sv3/131_hires.png",   8.00),
    # ── Temporal Forces (SV5) ─────────────────────────────────────────────────
    ("sv5-44",   "Iron Leaves ex", "Temporal Forces","sv5","44", "Double Rare",         "Pokémon", "https://images.pokemontcg.io/sv5/44.png",    "https://images.pokemontcg.io/sv5/44_hires.png",    6.00),
    ("sv5-217",  "Walking Wake ex","Temporal Forces","sv5","217","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv5/217.png","https://images.pokemontcg.io/sv5/217_hires.png",18.00),
    # ── Twilight Masquerade (SV6) ──────────────────────────────────────────────
    ("sv6-167",  "Ogerpon ex",     "Twilight Masquerade","sv6","167","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv6/167.png","https://images.pokemontcg.io/sv6/167_hires.png",55.00),
    ("sv6-25",   "Ogerpon ex",     "Twilight Masquerade","sv6","25", "Double Rare",     "Pokémon", "https://images.pokemontcg.io/sv6/25.png",    "https://images.pokemontcg.io/sv6/25_hires.png",   12.00),
    # ── Shrouded Fable (SV6.5) ────────────────────────────────────────────────
    ("sv6pt5-71","Pecharunt ex",   "Shrouded Fable","sv6pt5","71","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv6pt5/71.png","https://images.pokemontcg.io/sv6pt5/71_hires.png",25.00),
    # ── Stellar Crown (SV7) ───────────────────────────────────────────────────
    ("sv7-120",  "Terapagos ex",   "Stellar Crown","sv7","120","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv7/120.png","https://images.pokemontcg.io/sv7/120_hires.png",35.00),
    ("sv7-13",   "Terapagos ex",   "Stellar Crown","sv7","13", "Double Rare",           "Pokémon", "https://images.pokemontcg.io/sv7/13.png",    "https://images.pokemontcg.io/sv7/13_hires.png",    8.00),
    # ── Surging Sparks (SV8) ──────────────────────────────────────────────────
    ("sv8-207",  "Pikachu ex",     "Surging Sparks","sv8","207","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv8/207.png","https://images.pokemontcg.io/sv8/207_hires.png",  60.00),
    ("sv8-36",   "Pikachu ex",     "Surging Sparks","sv8","36", "Double Rare",           "Pokémon", "https://images.pokemontcg.io/sv8/36.png",    "https://images.pokemontcg.io/sv8/36_hires.png",    12.00),
    ("sv8-130",  "Raichu ex",      "Surging Sparks","sv8","130","Double Rare",           "Pokémon", "https://images.pokemontcg.io/sv8/130.png",   "https://images.pokemontcg.io/sv8/130_hires.png",   8.00),
    ("sv8-231",  "Raichu ex",      "Surging Sparks","sv8","231","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv8/231.png","https://images.pokemontcg.io/sv8/231_hires.png",  28.00),
    # ── Prismatic Evolutions (SV8.5) ──────────────────────────────────────────
    ("sv8pt5-128","Umbreon ex",    "Prismatic Evolutions","sv8pt5","128","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv8pt5/128.png","https://images.pokemontcg.io/sv8pt5/128_hires.png",195.00),
    ("sv8pt5-97", "Flareon ex",    "Prismatic Evolutions","sv8pt5","97", "Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv8pt5/97.png","https://images.pokemontcg.io/sv8pt5/97_hires.png", 65.00),
    ("sv8pt5-100","Jolteon ex",    "Prismatic Evolutions","sv8pt5","100","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv8pt5/100.png","https://images.pokemontcg.io/sv8pt5/100_hires.png",55.00),
    ("sv8pt5-103","Vaporeon ex",   "Prismatic Evolutions","sv8pt5","103","Special Illustration Rare","Pokémon","https://images.pokemontcg.io/sv8pt5/103.png","https://images.pokemontcg.io/sv8pt5/103_hires.png",55.00),
    ("sv8pt5-30", "Eevee",         "Prismatic Evolutions","sv8pt5","30", "Common",       "Pokémon", "https://images.pokemontcg.io/sv8pt5/30.png",  "https://images.pokemontcg.io/sv8pt5/30_hires.png",  5.00),
    ("sv8pt5-91", "Espeon ex",     "Prismatic Evolutions","sv8pt5","91", "Double Rare",  "Pokémon", "https://images.pokemontcg.io/sv8pt5/91.png",  "https://images.pokemontcg.io/sv8pt5/91_hires.png",  12.00),
    # ── Legendary / Promo ─────────────────────────────────────────────────────
    ("swsh4-118","Mew VMAX",       "Fusion Strike","swsh4","118","Rare Rainbow",        "Pokémon", "https://images.pokemontcg.io/swsh4/118.png",  "https://images.pokemontcg.io/swsh4/118_hires.png",  22.00),
    ("swsh5-108","Calyrex VMAX",   "Chilling Reign","swsh5","108","Rare Rainbow",       "Pokémon", "https://images.pokemontcg.io/swsh5/108.png",  "https://images.pokemontcg.io/swsh5/108_hires.png",  12.00),
    ("swsh8-150","Eevee Heroes",   "Eevee Heroes","swsh8","150","Rare Rainbow",         "Pokémon", "https://images.pokemontcg.io/swsh8/150.png",  "https://images.pokemontcg.io/swsh8/150_hires.png",  18.00),
]


async def seed():
    print("Creating tables if needed…")
    await create_tables()

    async with AsyncSession(engine, expire_on_commit=False) as db:
        inserted = 0
        for card_data in CARDS:
            (cid, name, set_name, set_code, number, rarity, supertype,
             img_sm, img_lg, market_price) = card_data

            stmt = sqlite_insert(Card).values(
                id=cid,
                name=name,
                set_name=set_name,
                set_code=set_code,
                number=number,
                rarity=rarity,
                supertype=supertype,
                image_small=img_sm,
                image_large=img_lg,
                fetched_at=NOW,
            ).on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": name,
                    "set_name": set_name,
                    "rarity": rarity,
                    "image_small": img_sm,
                    "image_large": img_lg,
                    "fetched_at": NOW,
                },
            )
            await db.execute(stmt)

            db.add(CardPrice(
                card_id=cid,
                source="tcgplayer",
                price_type="market",
                price_usd=float(market_price),
                recorded_at=NOW,
            ))
            inserted += 1

        await db.commit()
        print(f"Done! Seeded {inserted} cards with market prices.")


if __name__ == "__main__":
    asyncio.run(seed())
