from repositories import CameroonKnowledgeRepository


def test_base_is_canonical_and_lists_crops() -> None:
    repo = CameroonKnowledgeRepository()
    crops = repo.list_crops()
    assert crops
    assert any(crop.get("code") == "CULT_TOMATE" for crop in crops)


def test_get_crop_accepts_short_code() -> None:
    repo = CameroonKnowledgeRepository()
    crop = repo.get_crop("TOMATE")
    assert crop is not None
    assert crop["code"] == "CULT_TOMATE"
