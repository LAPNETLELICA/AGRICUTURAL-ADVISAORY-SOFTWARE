from pathlib import Path

from scripts.check_structure import validate_layout


def test_repository_matches_conception_section_14():
    project_root = Path(__file__).resolve().parents[2]
    assert validate_layout(project_root) == []
