from BASE_CONNAISSANCES_AGRICOLES.reader import CameroonKnowledgeBase


def _repository() -> CameroonKnowledgeBase:
    return CameroonKnowledgeBase("BASE_CONNAISSANCES_AGRICOLES")


def test_potato_profile_exists():
    profile = _repository().get_culture("POMME_DE_TERRE")
    assert profile is not None
    assert profile["code"] == "CULT_POMME_DE_TERRE"
    assert profile["famille_code"] == "FAM_TUBERCULES_RACINES"


def test_rules_are_crop_scoped():
    links = _repository().resolve_culture_links("POMME_DE_TERRE")
    assert links["culture"]["code"] == "CULT_POMME_DE_TERRE"
    assert links["sols_favorables"]


def test_tomato_profile_exists():
    profile = _repository().get_culture("TOMATE")
    assert profile is not None
    assert profile["code"] == "CULT_TOMATE"
    assert profile["nom_courant"] == "Tomate"
    assert profile["famille_code"] == "FAM_MARAICHAGE"
    assert profile["cycle_jours"]["optimal"] == 125
    assert "pepiniere_jours" in profile["caracteristiques_cycle"]
    assert "maturation_recolte_jours" in profile["caracteristiques_cycle"]
    assert profile["besoins"]["temperature_optimale_c"] == [20, 25]
    assert profile["besoins"]["ph_optimal"] == [5.5, 6.8]


def test_tomato_rules_coverage():
    links = _repository().resolve_culture_links("TOMATE")
    assert links["regions_principales"]
    assert links["engrais_recommandes"]
    assert links["varietes"]


def test_irish_potato_profile_and_rules_exist():
    profile = _repository().get_culture("POMME_DE_TERRE")
    assert profile is not None
    assert profile["nom_courant"] == "Pomme de terre"
    assert _repository().get_sols_favorables("POMME_DE_TERRE")
