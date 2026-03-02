"""Seed real Pokemon TCG sealed product catalog with listings.

Products: booster boxes, Elite Trainer Boxes, Ultra Premium Collections,
          booster bundles, tins, and collection boxes across all eras.

Usage:
  cd backend
  python seed_products.py
"""
import asyncio
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, create_tables
from app.models.product import SealedProduct
from app.models.price import ProductPrice
from app.models.listing import Listing, SellerProfile
from app.models.user import User

# ─── Sealed Product Catalog ─────────────────────────────────────────────────
# (name, set_name, product_type, ebay_search_term)
# product_type: booster_box | etb | upc | bundle | tin | pack | collection_box
PRODUCTS: list[tuple[str, str, str, str]] = [

    # ═══════════════════════════════════════════════════════════════════════
    # SCARLET & VIOLET ERA (2023–present)
    # ═══════════════════════════════════════════════════════════════════════

    # Scarlet & Violet Base
    ("Scarlet & Violet Booster Box", "Scarlet & Violet", "booster_box", "pokemon scarlet violet base set booster box"),
    ("Scarlet & Violet Elite Trainer Box Scarlet", "Scarlet & Violet", "etb", "pokemon scarlet violet scarlet etb"),
    ("Scarlet & Violet Elite Trainer Box Violet", "Scarlet & Violet", "etb", "pokemon scarlet violet violet etb"),
    ("Scarlet & Violet Booster Bundle", "Scarlet & Violet", "bundle", "pokemon scarlet violet booster bundle"),
    ("Koraidon ex Special Collection", "Scarlet & Violet", "collection_box", "pokemon koraidon ex special collection"),
    ("Miraidon ex Special Collection", "Scarlet & Violet", "collection_box", "pokemon miraidon ex special collection"),
    ("Pikachu ex Premium Collection", "Scarlet & Violet", "collection_box", "pokemon pikachu ex premium collection"),
    ("Scarlet & Violet Booster Pack", "Scarlet & Violet", "pack", "pokemon scarlet violet booster pack"),

    # Paldea Evolved
    ("Paldea Evolved Booster Box", "Paldea Evolved", "booster_box", "pokemon paldea evolved booster box"),
    ("Paldea Evolved Elite Trainer Box", "Paldea Evolved", "etb", "pokemon paldea evolved etb"),
    ("Paldea Evolved Booster Bundle", "Paldea Evolved", "bundle", "pokemon paldea evolved booster bundle"),
    ("Paldea Evolved Booster Pack", "Paldea Evolved", "pack", "pokemon paldea evolved booster pack"),

    # Obsidian Flames
    ("Obsidian Flames Booster Box", "Obsidian Flames", "booster_box", "pokemon obsidian flames booster box"),
    ("Obsidian Flames Elite Trainer Box", "Obsidian Flames", "etb", "pokemon obsidian flames etb"),
    ("Obsidian Flames Booster Bundle", "Obsidian Flames", "bundle", "pokemon obsidian flames booster bundle"),
    ("Charizard ex Premium Collection", "Obsidian Flames", "collection_box", "pokemon charizard ex premium collection obsidian flames"),
    ("Obsidian Flames Booster Pack", "Obsidian Flames", "pack", "pokemon obsidian flames booster pack"),

    # 151
    ("151 Booster Box", "151", "booster_box", "pokemon 151 booster box sv03.5"),
    ("151 Elite Trainer Box", "151", "etb", "pokemon 151 elite trainer box sv03.5"),
    ("151 Ultra Premium Collection", "151", "upc", "pokemon 151 ultra premium collection mew"),
    ("151 Booster Bundle", "151", "bundle", "pokemon 151 booster bundle sv03.5"),
    ("Mew ex Collection", "151", "collection_box", "pokemon mew ex collection 151"),
    ("151 Booster Pack", "151", "pack", "pokemon 151 booster pack"),

    # Paradox Rift
    ("Paradox Rift Booster Box", "Paradox Rift", "booster_box", "pokemon paradox rift booster box"),
    ("Paradox Rift Elite Trainer Box Iron Valiant", "Paradox Rift", "etb", "pokemon paradox rift iron valiant elite trainer box"),
    ("Paradox Rift Elite Trainer Box Roaring Moon", "Paradox Rift", "etb", "pokemon paradox rift roaring moon elite trainer box"),
    ("Paradox Rift Booster Bundle", "Paradox Rift", "bundle", "pokemon paradox rift booster bundle"),
    ("Paradox Rift Booster Pack", "Paradox Rift", "pack", "pokemon paradox rift booster pack"),

    # Paldean Fates
    ("Paldean Fates Elite Trainer Box", "Paldean Fates", "etb", "pokemon paldean fates elite trainer box"),
    ("Paldean Fates Booster Bundle", "Paldean Fates", "bundle", "pokemon paldean fates booster bundle"),
    ("Paldean Fates Great Tusk/Iron Treads Premium Collection", "Paldean Fates", "collection_box", "pokemon paldean fates premium collection"),

    # Temporal Forces
    ("Temporal Forces Booster Box", "Temporal Forces", "booster_box", "pokemon temporal forces booster box"),
    ("Temporal Forces Elite Trainer Box Iron Leaves", "Temporal Forces", "etb", "pokemon temporal forces iron leaves elite trainer box"),
    ("Temporal Forces Elite Trainer Box Walking Wake", "Temporal Forces", "etb", "pokemon temporal forces walking wake elite trainer box"),
    ("Temporal Forces Booster Bundle", "Temporal Forces", "bundle", "pokemon temporal forces booster bundle"),
    ("Temporal Forces Booster Pack", "Temporal Forces", "pack", "pokemon temporal forces booster pack"),

    # Twilight Masquerade
    ("Twilight Masquerade Booster Box", "Twilight Masquerade", "booster_box", "pokemon twilight masquerade booster box"),
    ("Twilight Masquerade Elite Trainer Box Ogerpon", "Twilight Masquerade", "etb", "pokemon twilight masquerade ogerpon elite trainer box"),
    ("Twilight Masquerade Elite Trainer Box Teal Mask", "Twilight Masquerade", "etb", "pokemon twilight masquerade teal mask etb"),
    ("Twilight Masquerade Booster Bundle", "Twilight Masquerade", "bundle", "pokemon twilight masquerade booster bundle"),
    ("Twilight Masquerade Booster Pack", "Twilight Masquerade", "pack", "pokemon twilight masquerade booster pack"),

    # Shrouded Fable
    ("Shrouded Fable Booster Box", "Shrouded Fable", "booster_box", "pokemon shrouded fable booster box"),
    ("Shrouded Fable Elite Trainer Box", "Shrouded Fable", "etb", "pokemon shrouded fable elite trainer box"),
    ("Shrouded Fable Booster Bundle", "Shrouded Fable", "bundle", "pokemon shrouded fable booster bundle"),

    # Stellar Crown
    ("Stellar Crown Booster Box", "Stellar Crown", "booster_box", "pokemon stellar crown booster box"),
    ("Stellar Crown Elite Trainer Box Terapagos", "Stellar Crown", "etb", "pokemon stellar crown terapagos elite trainer box"),
    ("Stellar Crown Elite Trainer Box Stellar", "Stellar Crown", "etb", "pokemon stellar crown stellar etb"),
    ("Stellar Crown Booster Bundle", "Stellar Crown", "bundle", "pokemon stellar crown booster bundle"),
    ("Stellar Crown Booster Pack", "Stellar Crown", "pack", "pokemon stellar crown booster pack"),

    # Surging Sparks
    ("Surging Sparks Booster Box", "Surging Sparks", "booster_box", "pokemon surging sparks booster box"),
    ("Surging Sparks Elite Trainer Box", "Surging Sparks", "etb", "pokemon surging sparks elite trainer box"),
    ("Surging Sparks Ultra Premium Collection", "Surging Sparks", "upc", "pokemon surging sparks pikachu ultra premium collection"),
    ("Surging Sparks Booster Bundle", "Surging Sparks", "bundle", "pokemon surging sparks booster bundle"),
    ("Surging Sparks Booster Pack", "Surging Sparks", "pack", "pokemon surging sparks booster pack"),

    # Prismatic Evolutions
    ("Prismatic Evolutions Booster Box", "Prismatic Evolutions", "booster_box", "pokemon prismatic evolutions booster box"),
    ("Prismatic Evolutions Elite Trainer Box", "Prismatic Evolutions", "etb", "pokemon prismatic evolutions elite trainer box"),
    ("Prismatic Evolutions Ultra Premium Collection", "Prismatic Evolutions", "upc", "pokemon prismatic evolutions ultra premium collection eevee"),
    ("Prismatic Evolutions Booster Bundle", "Prismatic Evolutions", "bundle", "pokemon prismatic evolutions booster bundle"),
    ("Eevee Tera ex Special Collection", "Prismatic Evolutions", "collection_box", "pokemon eevee tera ex special collection prismatic"),
    ("Prismatic Evolutions Booster Pack", "Prismatic Evolutions", "pack", "pokemon prismatic evolutions booster pack"),

    # Journey Together
    ("Journey Together Booster Box", "Journey Together", "booster_box", "pokemon journey together booster box"),
    ("Journey Together Elite Trainer Box", "Journey Together", "etb", "pokemon journey together elite trainer box"),
    ("Journey Together Booster Bundle", "Journey Together", "bundle", "pokemon journey together booster bundle"),
    ("Journey Together Booster Pack", "Journey Together", "pack", "pokemon journey together booster pack"),

    # Tins (SV era)
    ("Charizard ex Tin", "Scarlet & Violet", "tin", "pokemon charizard ex tin scarlet violet"),
    ("Mewtwo ex Tin", "Scarlet & Violet", "tin", "pokemon mewtwo ex tin scarlet violet"),
    ("Pikachu ex Tin", "Scarlet & Violet", "tin", "pokemon pikachu ex tin scarlet violet"),
    ("Gardevoir ex Tin", "Scarlet & Violet", "tin", "pokemon gardevoir ex tin scarlet violet"),
    ("Miraidon ex Tin", "Scarlet & Violet", "tin", "pokemon miraidon ex tin"),
    ("Koraidon ex Tin", "Scarlet & Violet", "tin", "pokemon koraidon ex tin"),
    ("Paldea Friends Tin Sprigatito", "Scarlet & Violet", "tin", "pokemon paldea friends tin sprigatito"),
    ("Paldea Friends Tin Fuecoco", "Scarlet & Violet", "tin", "pokemon paldea friends tin fuecoco"),
    ("Paldea Friends Tin Quaxly", "Scarlet & Violet", "tin", "pokemon paldea friends tin quaxly"),

    # ═══════════════════════════════════════════════════════════════════════
    # SWORD & SHIELD ERA (2020–2023)
    # ═══════════════════════════════════════════════════════════════════════

    ("Sword & Shield Booster Box", "Sword & Shield", "booster_box", "pokemon sword shield base booster box"),
    ("Sword & Shield Elite Trainer Box", "Sword & Shield", "etb", "pokemon sword shield base elite trainer box"),
    ("Rebel Clash Booster Box", "Rebel Clash", "booster_box", "pokemon rebel clash booster box"),
    ("Rebel Clash Elite Trainer Box", "Rebel Clash", "etb", "pokemon rebel clash elite trainer box"),
    ("Darkness Ablaze Booster Box", "Darkness Ablaze", "booster_box", "pokemon darkness ablaze booster box"),
    ("Darkness Ablaze Elite Trainer Box", "Darkness Ablaze", "etb", "pokemon darkness ablaze elite trainer box"),
    ("Charizard VMAX Premium Collection", "Darkness Ablaze", "collection_box", "pokemon charizard vmax premium collection"),
    ("Vivid Voltage Booster Box", "Vivid Voltage", "booster_box", "pokemon vivid voltage booster box"),
    ("Vivid Voltage Elite Trainer Box", "Vivid Voltage", "etb", "pokemon vivid voltage elite trainer box"),
    ("Shining Fates Elite Trainer Box", "Shining Fates", "etb", "pokemon shining fates elite trainer box"),
    ("Shining Fates Premium Collection Shiny Charizard VMAX", "Shining Fates", "collection_box", "pokemon shining fates shiny charizard vmax premium collection"),
    ("Battle Styles Booster Box", "Battle Styles", "booster_box", "pokemon battle styles booster box"),
    ("Battle Styles Elite Trainer Box Single Strike", "Battle Styles", "etb", "pokemon battle styles single strike elite trainer box"),
    ("Battle Styles Elite Trainer Box Rapid Strike", "Battle Styles", "etb", "pokemon battle styles rapid strike elite trainer box"),
    ("Chilling Reign Booster Box", "Chilling Reign", "booster_box", "pokemon chilling reign booster box"),
    ("Chilling Reign Elite Trainer Box Ice Rider Calyrex", "Chilling Reign", "etb", "pokemon chilling reign ice rider calyrex elite trainer box"),
    ("Chilling Reign Elite Trainer Box Shadow Rider Calyrex", "Chilling Reign", "etb", "pokemon chilling reign shadow rider calyrex elite trainer box"),
    ("Evolving Skies Booster Box", "Evolving Skies", "booster_box", "pokemon evolving skies booster box"),
    ("Evolving Skies Elite Trainer Box", "Evolving Skies", "etb", "pokemon evolving skies eevee elite trainer box"),
    ("Celebrations Ultra Premium Collection", "Celebrations", "upc", "pokemon celebrations ultra premium collection 25th anniversary"),
    ("Celebrations Elite Trainer Box", "Celebrations", "etb", "pokemon celebrations elite trainer box 25th anniversary"),
    ("Celebrations Classic Collection", "Celebrations", "collection_box", "pokemon celebrations classic collection 25th"),
    ("Fusion Strike Booster Box", "Fusion Strike", "booster_box", "pokemon fusion strike booster box"),
    ("Fusion Strike Elite Trainer Box", "Fusion Strike", "etb", "pokemon fusion strike elite trainer box"),
    ("Mew VMAX Premium Collection", "Fusion Strike", "collection_box", "pokemon mew vmax premium collection fusion strike"),
    ("Brilliant Stars Booster Box", "Brilliant Stars", "booster_box", "pokemon brilliant stars booster box"),
    ("Brilliant Stars Elite Trainer Box", "Brilliant Stars", "etb", "pokemon brilliant stars elite trainer box"),
    ("Arceus VSTAR Ultra Premium Collection", "Brilliant Stars", "upc", "pokemon arceus vstar ultra premium collection"),
    ("Astral Radiance Booster Box", "Astral Radiance", "booster_box", "pokemon astral radiance booster box"),
    ("Astral Radiance Elite Trainer Box", "Astral Radiance", "etb", "pokemon astral radiance elite trainer box"),
    ("Pokemon GO Booster Box", "Pokemon GO", "booster_box", "pokemon go booster box swsh10.5"),
    ("Pokemon GO Elite Trainer Box", "Pokemon GO", "etb", "pokemon go elite trainer box"),
    ("Pokemon GO Premier Deck Holder Collection Radiant Eevee", "Pokemon GO", "collection_box", "pokemon go radiant eevee premier deck holder"),
    ("Lost Origin Booster Box", "Lost Origin", "booster_box", "pokemon lost origin booster box"),
    ("Lost Origin Elite Trainer Box Giratina", "Lost Origin", "etb", "pokemon lost origin giratina elite trainer box"),
    ("Silver Tempest Booster Box", "Silver Tempest", "booster_box", "pokemon silver tempest booster box"),
    ("Silver Tempest Elite Trainer Box", "Silver Tempest", "etb", "pokemon silver tempest elite trainer box"),
    ("Lugia VSTAR Premium Collection", "Silver Tempest", "collection_box", "pokemon lugia vstar premium collection"),
    ("Crown Zenith Elite Trainer Box Regieleki", "Crown Zenith", "etb", "pokemon crown zenith regieleki elite trainer box"),
    ("Crown Zenith Elite Trainer Box Regidrago", "Crown Zenith", "etb", "pokemon crown zenith regidrago elite trainer box"),
    ("Crown Zenith Galarian Gallery Premium Figure Collection Morpeko", "Crown Zenith", "collection_box", "pokemon crown zenith morpeko premium figure collection"),
    ("Crown Zenith Galarian Gallery Premium Figure Collection Pikachu VMAX", "Crown Zenith", "collection_box", "pokemon crown zenith pikachu vmax premium figure collection"),

    # SWSH Tins
    ("Eevee Evolutions Tin Vaporeon", "Sword & Shield", "tin", "pokemon eevee evolutions tin vaporeon 2021"),
    ("Eevee Evolutions Tin Jolteon", "Sword & Shield", "tin", "pokemon eevee evolutions tin jolteon 2021"),
    ("Eevee Evolutions Tin Flareon", "Sword & Shield", "tin", "pokemon eevee evolutions tin flareon 2021"),
    ("Charizard VMAX Tin", "Sword & Shield", "tin", "pokemon charizard vmax collector tin"),
    ("Pikachu VMAX Tin", "Sword & Shield", "tin", "pokemon pikachu vmax collector tin"),

    # ═══════════════════════════════════════════════════════════════════════
    # SUN & MOON ERA (2017–2019)
    # ═══════════════════════════════════════════════════════════════════════

    ("Sun & Moon Booster Box", "Sun & Moon", "booster_box", "pokemon sun moon base set booster box"),
    ("Sun & Moon Elite Trainer Box", "Sun & Moon", "etb", "pokemon sun moon base elite trainer box"),
    ("Guardians Rising Booster Box", "Guardians Rising", "booster_box", "pokemon guardians rising booster box"),
    ("Guardians Rising Elite Trainer Box", "Guardians Rising", "etb", "pokemon guardians rising elite trainer box"),
    ("Burning Shadows Booster Box", "Burning Shadows", "booster_box", "pokemon burning shadows booster box"),
    ("Burning Shadows Elite Trainer Box", "Burning Shadows", "etb", "pokemon burning shadows elite trainer box"),
    ("Shining Legends Super Premium Collection", "Shining Legends", "upc", "pokemon shining legends super premium collection mewtwo"),
    ("Shining Legends Elite Trainer Box", "Shining Legends", "etb", "pokemon shining legends elite trainer box"),
    ("Crimson Invasion Booster Box", "Crimson Invasion", "booster_box", "pokemon crimson invasion booster box"),
    ("Crimson Invasion Elite Trainer Box", "Crimson Invasion", "etb", "pokemon crimson invasion elite trainer box"),
    ("Ultra Prism Booster Box", "Ultra Prism", "booster_box", "pokemon ultra prism booster box"),
    ("Ultra Prism Elite Trainer Box Dusk Mane Necrozma", "Ultra Prism", "etb", "pokemon ultra prism dusk mane necrozma elite trainer box"),
    ("Ultra Prism Elite Trainer Box Dawn Wings Necrozma", "Ultra Prism", "etb", "pokemon ultra prism dawn wings necrozma elite trainer box"),
    ("Forbidden Light Booster Box", "Forbidden Light", "booster_box", "pokemon forbidden light booster box"),
    ("Forbidden Light Elite Trainer Box", "Forbidden Light", "etb", "pokemon forbidden light elite trainer box"),
    ("Celestial Storm Booster Box", "Celestial Storm", "booster_box", "pokemon celestial storm booster box"),
    ("Celestial Storm Elite Trainer Box", "Celestial Storm", "etb", "pokemon celestial storm elite trainer box"),
    ("Dragon Majesty Super Premium Collection", "Dragon Majesty", "upc", "pokemon dragon majesty super premium collection"),
    ("Lost Thunder Booster Box", "Lost Thunder", "booster_box", "pokemon lost thunder booster box"),
    ("Lost Thunder Elite Trainer Box", "Lost Thunder", "etb", "pokemon lost thunder elite trainer box"),
    ("Team Up Booster Box", "Team Up", "booster_box", "pokemon team up booster box"),
    ("Team Up Elite Trainer Box", "Team Up", "etb", "pokemon team up elite trainer box"),
    ("Detective Pikachu Booster Box", "Detective Pikachu", "booster_box", "pokemon detective pikachu booster box"),
    ("Unbroken Bonds Booster Box", "Unbroken Bonds", "booster_box", "pokemon unbroken bonds booster box"),
    ("Unbroken Bonds Elite Trainer Box", "Unbroken Bonds", "etb", "pokemon unbroken bonds elite trainer box"),
    ("Unified Minds Booster Box", "Unified Minds", "booster_box", "pokemon unified minds booster box"),
    ("Unified Minds Elite Trainer Box", "Unified Minds", "etb", "pokemon unified minds elite trainer box"),
    ("Hidden Fates Elite Trainer Box", "Hidden Fates", "etb", "pokemon hidden fates elite trainer box"),
    ("Hidden Fates Shiny Vault Premium Collection Mewtwo", "Hidden Fates", "upc", "pokemon hidden fates mewtwo ultra premium collection"),
    ("Cosmic Eclipse Booster Box", "Cosmic Eclipse", "booster_box", "pokemon cosmic eclipse booster box"),
    ("Cosmic Eclipse Elite Trainer Box", "Cosmic Eclipse", "etb", "pokemon cosmic eclipse elite trainer box"),

    # SM Tins
    ("Tapu Koko Tin", "Sun & Moon", "tin", "pokemon tapu koko tin"),
    ("Pikachu-GX Tin", "Sun & Moon", "tin", "pokemon pikachu gx tin"),
    ("Charizard-GX Tin", "Sun & Moon", "tin", "pokemon charizard gx tin"),

    # ═══════════════════════════════════════════════════════════════════════
    # XY ERA (2014–2016)
    # ═══════════════════════════════════════════════════════════════════════

    ("XY Booster Box", "XY", "booster_box", "pokemon xy base set booster box"),
    ("XY Elite Trainer Box", "XY", "etb", "pokemon xy base elite trainer box"),
    ("Flashfire Booster Box", "Flashfire", "booster_box", "pokemon flashfire booster box"),
    ("Furious Fists Booster Box", "Furious Fists", "booster_box", "pokemon furious fists booster box"),
    ("Phantom Forces Booster Box", "Phantom Forces", "booster_box", "pokemon phantom forces booster box"),
    ("Phantom Forces Elite Trainer Box", "Phantom Forces", "etb", "pokemon phantom forces elite trainer box"),
    ("Primal Clash Booster Box", "Primal Clash", "booster_box", "pokemon primal clash booster box"),
    ("Primal Clash Elite Trainer Box Primal Groudon", "Primal Clash", "etb", "pokemon primal clash groudon elite trainer box"),
    ("Primal Clash Elite Trainer Box Primal Kyogre", "Primal Clash", "etb", "pokemon primal clash kyogre elite trainer box"),
    ("Roaring Skies Booster Box", "Roaring Skies", "booster_box", "pokemon roaring skies booster box"),
    ("Ancient Origins Booster Box", "Ancient Origins", "booster_box", "pokemon ancient origins booster box"),
    ("BREAKthrough Booster Box", "BREAKthrough", "booster_box", "pokemon breakthrough booster box"),
    ("BREAKthrough Elite Trainer Box", "BREAKthrough", "etb", "pokemon breakthrough elite trainer box"),
    ("BREAKpoint Booster Box", "BREAKpoint", "booster_box", "pokemon breakpoint booster box"),
    ("Generations Elite Trainer Box", "Generations", "etb", "pokemon generations elite trainer box"),
    ("Fates Collide Booster Box", "Fates Collide", "booster_box", "pokemon fates collide booster box"),
    ("Steam Siege Booster Box", "Steam Siege", "booster_box", "pokemon steam siege booster box"),
    ("Evolutions Booster Box", "Evolutions", "booster_box", "pokemon evolutions booster box"),
    ("Evolutions Elite Trainer Box", "Evolutions", "etb", "pokemon evolutions elite trainer box"),

    # ═══════════════════════════════════════════════════════════════════════
    # BLACK & WHITE ERA (2011–2013)
    # ═══════════════════════════════════════════════════════════════════════

    ("Black & White Booster Box", "Black & White", "booster_box", "pokemon black white base booster box"),
    ("Emerging Powers Booster Box", "Emerging Powers", "booster_box", "pokemon emerging powers booster box"),
    ("Noble Victories Booster Box", "Noble Victories", "booster_box", "pokemon noble victories booster box"),
    ("Next Destinies Booster Box", "Next Destinies", "booster_box", "pokemon next destinies booster box"),
    ("Dark Explorers Booster Box", "Dark Explorers", "booster_box", "pokemon dark explorers booster box"),
    ("Dragons Exalted Booster Box", "Dragons Exalted", "booster_box", "pokemon dragons exalted booster box"),
    ("Boundaries Crossed Booster Box", "Boundaries Crossed", "booster_box", "pokemon boundaries crossed booster box"),
    ("Plasma Storm Booster Box", "Plasma Storm", "booster_box", "pokemon plasma storm booster box"),
    ("Plasma Freeze Booster Box", "Plasma Freeze", "booster_box", "pokemon plasma freeze booster box"),
    ("Plasma Blast Booster Box", "Plasma Blast", "booster_box", "pokemon plasma blast booster box"),
    ("Legendary Treasures Booster Box", "Legendary Treasures", "booster_box", "pokemon legendary treasures booster box"),
    ("Radiant Collection Premium Box", "Legendary Treasures", "collection_box", "pokemon legendary treasures radiant collection premium box"),

    # ═══════════════════════════════════════════════════════════════════════
    # HEARTGOLD SOULSILVER ERA (2010–2011)
    # ═══════════════════════════════════════════════════════════════════════

    ("HeartGold SoulSilver Booster Box", "HeartGold SoulSilver", "booster_box", "pokemon heartgold soulsilver booster box"),
    ("Unleashed Booster Box", "Unleashed", "booster_box", "pokemon unleashed booster box"),
    ("Undaunted Booster Box", "Undaunted", "booster_box", "pokemon undaunted booster box"),
    ("Triumphant Booster Box", "Triumphant", "booster_box", "pokemon triumphant booster box"),
    ("Call of Legends Booster Box", "Call of Legends", "booster_box", "pokemon call of legends booster box"),

    # ═══════════════════════════════════════════════════════════════════════
    # PLATINUM / DIAMOND & PEARL ERA (2007–2010)
    # ═══════════════════════════════════════════════════════════════════════

    ("Diamond & Pearl Booster Box", "Diamond & Pearl", "booster_box", "pokemon diamond pearl base booster box"),
    ("Mysterious Treasures Booster Box", "Mysterious Treasures", "booster_box", "pokemon mysterious treasures booster box"),
    ("Secret Wonders Booster Box", "Secret Wonders", "booster_box", "pokemon secret wonders booster box"),
    ("Great Encounters Booster Box", "Great Encounters", "booster_box", "pokemon great encounters booster box"),
    ("Majestic Dawn Booster Box", "Majestic Dawn", "booster_box", "pokemon majestic dawn booster box"),
    ("Legends Awakened Booster Box", "Legends Awakened", "booster_box", "pokemon legends awakened booster box"),
    ("Stormfront Booster Box", "Stormfront", "booster_box", "pokemon stormfront booster box"),
    ("Platinum Booster Box", "Platinum", "booster_box", "pokemon platinum base booster box"),
    ("Rising Rivals Booster Box", "Rising Rivals", "booster_box", "pokemon rising rivals booster box"),
    ("Supreme Victors Booster Box", "Supreme Victors", "booster_box", "pokemon supreme victors booster box"),
    ("Arceus Booster Box", "Arceus", "booster_box", "pokemon arceus booster box"),

    # ═══════════════════════════════════════════════════════════════════════
    # EX ERA (2003–2007)
    # ═══════════════════════════════════════════════════════════════════════

    ("EX Ruby & Sapphire Booster Box", "EX Ruby & Sapphire", "booster_box", "pokemon ex ruby sapphire booster box"),
    ("EX Sandstorm Booster Box", "EX Sandstorm", "booster_box", "pokemon ex sandstorm booster box"),
    ("EX Dragon Booster Box", "EX Dragon", "booster_box", "pokemon ex dragon booster box"),
    ("EX Team Magma vs Team Aqua Booster Box", "EX Team Magma vs Team Aqua", "booster_box", "pokemon ex team magma aqua booster box"),
    ("EX Hidden Legends Booster Box", "EX Hidden Legends", "booster_box", "pokemon ex hidden legends booster box"),
    ("EX FireRed & LeafGreen Booster Box", "EX FireRed & LeafGreen", "booster_box", "pokemon ex firered leafgreen booster box"),
    ("EX Team Rocket Returns Booster Box", "EX Team Rocket Returns", "booster_box", "pokemon ex team rocket returns booster box"),
    ("EX Deoxys Booster Box", "EX Deoxys", "booster_box", "pokemon ex deoxys booster box"),
    ("EX Emerald Booster Box", "EX Emerald", "booster_box", "pokemon ex emerald booster box"),
    ("EX Unseen Forces Booster Box", "EX Unseen Forces", "booster_box", "pokemon ex unseen forces booster box"),
    ("EX Delta Species Booster Box", "EX Delta Species", "booster_box", "pokemon ex delta species booster box"),
    ("EX Legend Maker Booster Box", "EX Legend Maker", "booster_box", "pokemon ex legend maker booster box"),
    ("EX Holon Phantoms Booster Box", "EX Holon Phantoms", "booster_box", "pokemon ex holon phantoms booster box"),
    ("EX Crystal Guardians Booster Box", "EX Crystal Guardians", "booster_box", "pokemon ex crystal guardians booster box"),
    ("EX Dragon Frontiers Booster Box", "EX Dragon Frontiers", "booster_box", "pokemon ex dragon frontiers booster box"),
    ("EX Power Keepers Booster Box", "EX Power Keepers", "booster_box", "pokemon ex power keepers booster box"),

    # ═══════════════════════════════════════════════════════════════════════
    # VINTAGE / BASE SET ERA (1999–2003) — WOTC
    # ═══════════════════════════════════════════════════════════════════════

    ("Base Set 1st Edition Booster Box", "Base Set", "booster_box", "pokemon base set 1st edition booster box wotc"),
    ("Base Set Shadowless Booster Box", "Base Set", "booster_box", "pokemon base set shadowless booster box wotc"),
    ("Base Set Unlimited Booster Box", "Base Set", "booster_box", "pokemon base set unlimited booster box wotc"),
    ("Jungle 1st Edition Booster Box", "Jungle", "booster_box", "pokemon jungle 1st edition booster box wotc"),
    ("Jungle Unlimited Booster Box", "Jungle", "booster_box", "pokemon jungle unlimited booster box wotc"),
    ("Fossil 1st Edition Booster Box", "Fossil", "booster_box", "pokemon fossil 1st edition booster box wotc"),
    ("Fossil Unlimited Booster Box", "Fossil", "booster_box", "pokemon fossil unlimited booster box wotc"),
    ("Team Rocket 1st Edition Booster Box", "Team Rocket", "booster_box", "pokemon team rocket 1st edition booster box wotc"),
    ("Team Rocket Unlimited Booster Box", "Team Rocket", "booster_box", "pokemon team rocket unlimited booster box wotc"),
    ("Gym Heroes 1st Edition Booster Box", "Gym Heroes", "booster_box", "pokemon gym heroes 1st edition booster box wotc"),
    ("Gym Heroes Unlimited Booster Box", "Gym Heroes", "booster_box", "pokemon gym heroes unlimited booster box wotc"),
    ("Gym Challenge 1st Edition Booster Box", "Gym Challenge", "booster_box", "pokemon gym challenge 1st edition booster box wotc"),
    ("Gym Challenge Unlimited Booster Box", "Gym Challenge", "booster_box", "pokemon gym challenge unlimited booster box wotc"),
    ("Neo Genesis 1st Edition Booster Box", "Neo Genesis", "booster_box", "pokemon neo genesis 1st edition booster box wotc"),
    ("Neo Genesis Unlimited Booster Box", "Neo Genesis", "booster_box", "pokemon neo genesis unlimited booster box wotc"),
    ("Neo Discovery 1st Edition Booster Box", "Neo Discovery", "booster_box", "pokemon neo discovery 1st edition booster box wotc"),
    ("Neo Discovery Unlimited Booster Box", "Neo Discovery", "booster_box", "pokemon neo discovery unlimited booster box wotc"),
    ("Neo Revelation 1st Edition Booster Box", "Neo Revelation", "booster_box", "pokemon neo revelation 1st edition booster box wotc"),
    ("Neo Revelation Unlimited Booster Box", "Neo Revelation", "booster_box", "pokemon neo revelation unlimited booster box wotc"),
    ("Neo Destiny 1st Edition Booster Box", "Neo Destiny", "booster_box", "pokemon neo destiny 1st edition booster box wotc"),
    ("Neo Destiny Unlimited Booster Box", "Neo Destiny", "booster_box", "pokemon neo destiny unlimited booster box wotc"),
    ("Legendary Collection Booster Box", "Legendary Collection", "booster_box", "pokemon legendary collection reverse holo booster box"),
    ("Expedition Booster Box", "Expedition Base Set", "booster_box", "pokemon expedition booster box wotc"),
    ("Aquapolis Booster Box", "Aquapolis", "booster_box", "pokemon aquapolis booster box wotc"),
    ("Skyridge Booster Box", "Skyridge", "booster_box", "pokemon skyridge booster box wotc"),

    # Vintage individual packs (for collectors)
    ("Base Set 1st Edition Booster Pack", "Base Set", "pack", "pokemon base set 1st edition booster pack wotc"),
    ("Base Set Shadowless Booster Pack", "Base Set", "pack", "pokemon base set shadowless booster pack wotc"),
    ("Jungle 1st Edition Booster Pack", "Jungle", "pack", "pokemon jungle 1st edition booster pack wotc"),
    ("Fossil 1st Edition Booster Pack", "Fossil", "pack", "pokemon fossil 1st edition booster pack wotc"),
    ("Team Rocket 1st Edition Booster Pack", "Team Rocket", "pack", "pokemon team rocket 1st edition booster pack wotc"),
    ("Neo Genesis 1st Edition Booster Pack", "Neo Genesis", "pack", "pokemon neo genesis 1st edition booster pack wotc"),
    ("Skyridge Booster Pack", "Skyridge", "pack", "pokemon skyridge booster pack wotc"),
    ("Aquapolis Booster Pack", "Aquapolis", "pack", "pokemon aquapolis booster pack wotc"),
]


# ─── Pricing by product type + era keywords ──────────────────────────────────

def get_product_price(name: str, product_type: str) -> float:
    """Return a realistic heuristic market price for a sealed product."""
    n = name.lower()

    if product_type == "pack":
        # Vintage packs (very high)
        if "1st edition" in n and ("base set" in n or "jungle" in n or "fossil" in n):
            return round(random.uniform(400, 2500), 2)
        if "shadowless" in n:
            return round(random.uniform(150, 600), 2)
        if "1st edition" in n and ("team rocket" in n or "gym" in n or "neo" in n):
            return round(random.uniform(100, 500), 2)
        if "skyridge" in n or "aquapolis" in n:
            return round(random.uniform(40, 150), 2)
        # Modern packs
        return round(random.uniform(4.00, 6.50), 2)

    if product_type == "booster_box":
        # === Vintage 1st Edition ===
        if "base set" in n and "1st edition" in n:
            return round(random.uniform(45000, 75000), 2)
        if ("jungle" in n or "fossil" in n) and "1st edition" in n:
            return round(random.uniform(4000, 8000), 2)
        if "team rocket" in n and "1st edition" in n:
            return round(random.uniform(3000, 6000), 2)
        if ("gym heroes" in n or "gym challenge" in n) and "1st edition" in n:
            return round(random.uniform(2500, 5000), 2)
        if "neo genesis" in n and "1st edition" in n:
            return round(random.uniform(2000, 4500), 2)
        if ("neo discovery" in n or "neo revelation" in n) and "1st edition" in n:
            return round(random.uniform(1200, 2800), 2)
        if "neo destiny" in n and "1st edition" in n:
            return round(random.uniform(3000, 6000), 2)
        # === Vintage Unlimited / Shadowless ===
        if "base set" in n and "shadowless" in n:
            return round(random.uniform(8000, 18000), 2)
        if "base set" in n and "unlimited" in n:
            return round(random.uniform(4000, 9000), 2)
        if ("jungle" in n or "fossil" in n) and "unlimited" in n:
            return round(random.uniform(700, 1800), 2)
        if "team rocket" in n and "unlimited" in n:
            return round(random.uniform(600, 1500), 2)
        if "gym" in n and "unlimited" in n:
            return round(random.uniform(500, 1200), 2)
        if "neo genesis" in n and "unlimited" in n:
            return round(random.uniform(400, 1000), 2)
        if "neo" in n and "unlimited" in n:
            return round(random.uniform(300, 800), 2)
        if "legendary collection" in n or "expedition" in n or "aquapolis" in n:
            return round(random.uniform(800, 2500), 2)
        if "skyridge" in n:
            return round(random.uniform(2000, 5000), 2)
        # === EX era ===
        if n.startswith("ex ") or " ex " in n[:20]:
            return round(random.uniform(200, 700), 2)
        # === Diamond & Pearl / Platinum / HGSS ===
        if any(x in n for x in ["diamond", "pearl", "platinum", "majestic", "legends awakened",
                                  "stormfront", "rising rivals", "supreme victors", "arceus",
                                  "heartgold", "soulsilver", "unleashed", "undaunted", "triumphant",
                                  "call of legends"]):
            return round(random.uniform(150, 450), 2)
        # === Black & White ===
        if any(x in n for x in ["black", "white", "emerging", "noble", "next destinies",
                                  "dark explorers", "dragons exalted", "boundaries", "plasma",
                                  "legendary treasures"]):
            return round(random.uniform(100, 280), 2)
        # === XY ===
        if any(x in n for x in ["flashfire", "furious fists", "phantom forces", "primal clash",
                                  "roaring skies", "ancient origins", "breakthrough", "breakpoint",
                                  "fates collide", "steam siege", "evolutions", "xy "]):
            return round(random.uniform(80, 220), 2)
        # === Sun & Moon ===
        if any(x in n for x in ["sun & moon", "guardians", "burning shadows", "crimson invasion",
                                  "ultra prism", "forbidden light", "celestial storm", "lost thunder",
                                  "team up", "detective pikachu", "unbroken bonds", "unified minds",
                                  "cosmic eclipse"]):
            return round(random.uniform(80, 220), 2)
        # === Sword & Shield ===
        if any(x in n for x in ["sword & shield", "rebel clash", "darkness ablaze", "vivid voltage",
                                  "battle styles", "chilling reign", "evolving skies", "fusion strike",
                                  "brilliant stars", "astral radiance", "pokemon go", "lost origin",
                                  "silver tempest"]):
            return round(random.uniform(90, 180), 2)
        # === Scarlet & Violet (current) ===
        return round(random.uniform(100, 160), 2)

    if product_type == "etb":
        if any(x in n for x in ["evolutions", "generations", "hidden fates", "shining fates",
                                  "celebrations", "shining legends"]):
            return round(random.uniform(80, 250), 2)
        if any(x in n for x in ["evolving skies", "chilling reign", "brilliant stars",
                                  "astral radiance", "fusion strike", "lost origin", "silver tempest",
                                  "crown zenith"]):
            return round(random.uniform(45, 90), 2)
        if any(x in n for x in ["xy", "sun & moon", "guardians", "burning shadows", "crimson",
                                  "ultra prism", "forbidden", "celestial", "lost thunder", "team up",
                                  "unbroken", "unified", "cosmic", "black & white", "battle styles"]):
            return round(random.uniform(40, 80), 2)
        # Current SV era ETBs
        return round(random.uniform(35, 60), 2)

    if product_type == "upc":
        if "celebrations" in n:
            return round(random.uniform(180, 350), 2)
        if "151" in n:
            return round(random.uniform(120, 200), 2)
        if "shining legends" in n or "dragon majesty" in n or "hidden fates" in n:
            return round(random.uniform(120, 300), 2)
        if "arceus" in n or "brilliant stars" in n:
            return round(random.uniform(100, 180), 2)
        # Current UPCs
        return round(random.uniform(90, 150), 2)

    if product_type == "bundle":
        return round(random.uniform(15.00, 28.00), 2)

    if product_type == "tin":
        if any(x in n for x in ["tapu", "charizard", "pikachu", "eevee"]):
            return round(random.uniform(25, 55), 2)
        return round(random.uniform(20, 35), 2)

    if product_type == "collection_box":
        if "ultra premium" in n or "upc" in n:
            return round(random.uniform(90, 200), 2)
        if any(x in n for x in ["charizard", "shiny", "celebrations"]):
            return round(random.uniform(50, 150), 2)
        return round(random.uniform(30, 80), 2)

    return round(random.uniform(20, 50), 2)


CONDITIONS = ["NM", "LP", "MP"]
CONDITION_DISCOUNT = {"NM": 1.00, "LP": 0.90, "MP": 0.78}


async def seed():
    await create_tables()

    async with AsyncSession(engine, expire_on_commit=False) as db:
        # ── Verify demo seller ──────────────────────────────────────────
        result = await db.execute(select(User).where(User.email == "demo@pokemarket.app"))
        seller = result.scalar_one_or_none()
        if not seller:
            print("ERROR: No demo@pokemarket.app user found. Run seed_admin.py first.")
            return

        sp_result = await db.execute(
            select(SellerProfile).where(SellerProfile.user_id == seller.id)
        )
        sp = sp_result.scalar_one_or_none()
        if not sp or not sp.onboarding_complete:
            print("ERROR: Demo user has no completed seller profile.")
            return

        # ── Cancel existing sealed listings ─────────────────────────────
        existing = await db.execute(
            select(Listing).where(
                Listing.seller_id == seller.id,
                Listing.item_type == "sealed",
                Listing.status == "active",
            )
        )
        cancelled = 0
        for lst in existing.scalars().all():
            lst.status = "cancelled"
            cancelled += 1
        await db.commit()
        print(f"Cancelled {cancelled} existing sealed listings.")

        # ── Seed sealed products ─────────────────────────────────────────
        now = datetime.now(timezone.utc)
        print(f"Seeding {len(PRODUCTS)} sealed products...")

        product_ids: dict[str, int] = {}  # name → id
        products_created = 0
        products_updated = 0

        for name, set_name, product_type, ebay_term in PRODUCTS:
            # Check existing
            existing_prod = await db.execute(
                select(SealedProduct).where(SealedProduct.name == name)
            )
            prod = existing_prod.scalar_one_or_none()
            if prod:
                prod.set_name = set_name
                prod.product_type = product_type
                prod.ebay_search_term = ebay_term
                products_updated += 1
            else:
                prod = SealedProduct(
                    name=name,
                    set_name=set_name,
                    product_type=product_type,
                    ebay_search_term=ebay_term,
                    image_url=None,
                    pricecharting_id=None,
                )
                db.add(prod)
                products_created += 1

            await db.flush()  # get id
            product_ids[name] = prod.id

            # Seed ProductPrice
            market_price = get_product_price(name, product_type)
            db.add(ProductPrice(
                product_id=prod.id,
                source="heuristic",
                price_type="market",
                price_usd=market_price,
                recorded_at=now,
            ))

        await db.commit()
        print(f"  Created: {products_created}, Updated: {products_updated}")

        # ── Seed sealed listings ─────────────────────────────────────────
        print("Seeding sealed product listings...")
        listings_created = 0
        batch_size = 100

        prod_names = list(product_ids.keys())
        for batch_start in range(0, len(prod_names), batch_size):
            batch = prod_names[batch_start:batch_start + batch_size]

            for name in batch:
                prod_id = product_ids[name]
                product_type = next(pt for n, _, pt, _ in PRODUCTS if n == name)
                market_price = get_product_price(name, product_type)

                # Determine which conditions to list
                if market_price >= 200:
                    conditions = ["NM"]
                elif market_price >= 50:
                    conditions = ["NM", "LP"]
                else:
                    conditions = ["NM", "LP", "MP"]

                for condition in conditions:
                    disc = CONDITION_DISCOUNT[condition]
                    variation = random.uniform(0.93, 1.07)
                    price = round(max(1.00, market_price * disc * variation), 2)
                    qty = 1 if market_price >= 100 else random.choice([1, 1, 2])

                    db.add(Listing(
                        seller_id=seller.id,
                        item_type="sealed",
                        product_id=prod_id,
                        card_id=None,
                        title=f"{name} - {condition}",
                        condition=condition,
                        quantity=qty,
                        price=price,
                        status="active",
                        grade=None,
                        grading_company=None,
                    ))
                    listings_created += 1

            await db.commit()
            pct = min(100, int((batch_start + len(batch)) / len(prod_names) * 100))
            print(f"  {batch_start + len(batch)}/{len(prod_names)} products ({pct}%) — {listings_created} listings")

        print(f"\nDone! Sealed products: {products_created + products_updated}, Listings: {listings_created}")


if __name__ == "__main__":
    asyncio.run(seed())
