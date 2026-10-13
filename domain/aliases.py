"""Table de correspondance et de normalisation des identifiants agronomiques du Cameroun."""

from __future__ import annotations

# Alias cultures -> Codes canoniques BASE_CONNAISSANCES_AGRICOLES
CROP_ALIASES: dict[str, str] = {
    "tomate": "CULT_TOMATE",
    "tomato": "CULT_TOMATE",
    "cult_tomate": "CULT_TOMATE",
    "pomme de terre": "CULT_POMME_DE_TERRE",
    "pomme_de_terre": "CULT_POMME_DE_TERRE",
    "pomme-de-terre": "CULT_POMME_DE_TERRE",
    "potato": "CULT_POMME_DE_TERRE",
    "irish-potato": "CULT_POMME_DE_TERRE",
    "irish_potato": "CULT_POMME_DE_TERRE",
    "cult_pomme_de_terre": "CULT_POMME_DE_TERRE",
    "mais": "CULT_MAIS",
    "maïs": "CULT_MAIS",
    "maize": "CULT_MAIS",
    "corn": "CULT_MAIS",
    "cult_mais": "CULT_MAIS",
    "haricot": "CULT_HARICOT",
    "bean": "CULT_HARICOT",
    "common bean": "CULT_HARICOT",
    "cult_haricot": "CULT_HARICOT",
    "manioc": "CULT_MANIOC",
    "cassava": "CULT_MANIOC",
    "cult_manioc": "CULT_MANIOC",
    "bananier plantain": "CULT_BANANIER_PLANTAIN",
    "bananier_plantain": "CULT_BANANIER_PLANTAIN",
    "bananier-plantain": "CULT_BANANIER_PLANTAIN",
    "plantain": "CULT_BANANIER_PLANTAIN",
    "banana plantain": "CULT_BANANIER_PLANTAIN",
    "cult_bananier_plantain": "CULT_BANANIER_PLANTAIN",
}

# Alias régions -> Codes régionaux MINADER
REGION_ALIASES: dict[str, str] = {
    "adamaoua": "REG_AD",
    "adamawa": "REG_AD",
    "reg_ad": "REG_AD",
    "centre": "REG_CE",
    "reg_ce": "REG_CE",
    "est": "REG_ES",
    "east": "REG_ES",
    "reg_es": "REG_ES",
    "extreme-nord": "REG_EN",
    "extreme_nord": "REG_EN",
    "far north": "REG_EN",
    "reg_en": "REG_EN",
    "littoral": "REG_LT",
    "reg_lt": "REG_LT",
    "nord": "REG_NO",
    "north": "REG_NO",
    "reg_no": "REG_NO",
    "nord-ouest": "REG_NW",
    "nord_ouest": "REG_NW",
    "north-west": "REG_NW",
    "northwest": "REG_NW",
    "reg_nw": "REG_NW",
    "ouest": "REG_OU",
    "west": "REG_OU",
    "reg_ou": "REG_OU",
    "sud": "REG_SU",
    "south": "REG_SU",
    "reg_su": "REG_SU",
    "sud-ouest": "REG_SW",
    "sud_ouest": "REG_SW",
    "south-west": "REG_SW",
    "southwest": "REG_SW",
    "reg_sw": "REG_SW",
}

# Alias sols -> Codes sols canoniques
SOIL_ALIASES: dict[str, str] = {
    "sol volcanique": "SOL_VOLCANIQUE",
    "volcanique": "SOL_VOLCANIQUE",
    "andosol": "SOL_VOLCANIQUE",
    "andosols": "SOL_VOLCANIQUE",
    "sol_volcanique": "SOL_VOLCANIQUE",
    "sol ferrallitique": "SOL_FERRALLITIQUE",
    "ferrallitique": "SOL_FERRALLITIQUE",
    "ferralsol": "SOL_FERRALLITIQUE",
    "sol_ferrallitique": "SOL_FERRALLITIQUE",
    "sol ferrugineux": "SOL_FERRUGINEUX",
    "ferrugineux": "SOL_FERRUGINEUX",
    "sol_ferrugineux": "SOL_FERRUGINEUX",
    "vertisol": "SOL_VERTISOL",
    "vertisols": "SOL_VERTISOL",
    "sol_vertisol": "SOL_VERTISOL",
    "sol hydromorphe": "SOL_HYDROMORPHE",
    "hydromorphe": "SOL_HYDROMORPHE",
    "sol_hydromorphe": "SOL_HYDROMORPHE",
    "sol sableux": "SOL_SABLEUX",
    "sableux": "SOL_SABLEUX",
    "sol_sableux": "SOL_SABLEUX",
}


def normalize_crop_id(crop_id: str) -> str:
    cleaned = crop_id.strip().lower()
    return CROP_ALIASES.get(cleaned, crop_id.strip().upper())


def normalize_region_id(region_id: str) -> str:
    cleaned = region_id.strip().lower()
    return REGION_ALIASES.get(cleaned, region_id.strip().upper())


def normalize_soil_id(soil_id: str) -> str:
    cleaned = soil_id.strip().lower()
    return SOIL_ALIASES.get(cleaned, soil_id.strip().upper())

