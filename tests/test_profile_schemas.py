"""Schema validation for every YAML profile shipped in profiles/."""
import pytest
import yaml
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"
PROFILE_FILES = sorted(PROFILE_DIR.glob("*.yaml")) + sorted(PROFILE_DIR.glob("*.yml"))

REQUIRED_FIELDS = ["name", "description", "version", "skills", "stages", "metadata"]


def _is_non_empty_str(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def test_profiles_discovered():
    """The profiles directory must contain at least one YAML profile."""
    assert PROFILE_FILES, f"No YAML profiles found in {PROFILE_DIR}"


@pytest.fixture(params=PROFILE_FILES, ids=lambda p: p.name)
def profile(request):
    """Load each profile file as a dict."""
    path = request.param
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"{path.name}: top level must be a mapping"
    return path.name, data


class TestProfileSchema:
    """Validate the structure of each profile YAML."""

    def test_required_fields_present(self, profile):
        filename, data = profile
        missing = [field for field in REQUIRED_FIELDS if field not in data]
        assert not missing, f"{filename}: missing required fields {missing}"

    def test_name_and_description(self, profile):
        filename, data = profile
        assert _is_non_empty_str(data.get("name")), f"{filename}: 'name' must be a non-empty string"
        assert _is_non_empty_str(data.get("description")), f"{filename}: 'description' must be a non-empty string"

    def test_version_is_string(self, profile):
        filename, data = profile
        assert _is_non_empty_str(data.get("version")), (
            f"{filename}: 'version' must be a quoted string, e.g. version: \"1.0.0\""
        )

    def test_skills_is_non_empty_list_of_strings(self, profile):
        filename, data = profile
        skills = data.get("skills")
        assert isinstance(skills, list) and skills, f"{filename}: 'skills' must be a non-empty list"
        bad = [s for s in skills if not _is_non_empty_str(s)]
        assert not bad, f"{filename}: 'skills' contains non-string or empty entries {bad}"

    def test_stages_is_dict_of_string_lists(self, profile):
        filename, data = profile
        stages = data.get("stages")
        assert isinstance(stages, dict) and stages, f"{filename}: 'stages' must be a non-empty mapping"
        for stage, steps in stages.items():
            assert isinstance(steps, list) and steps, (
                f"{filename}: stage '{stage}' must be a non-empty list"
            )
            bad = [s for s in steps if not _is_non_empty_str(s)]
            assert not bad, f"{filename}: stage '{stage}' contains non-string or empty entries {bad}"

    def test_metadata_tags_and_author(self, profile):
        filename, data = profile
        metadata = data.get("metadata")
        assert isinstance(metadata, dict), f"{filename}: 'metadata' must be a mapping"
        tags = metadata.get("tags")
        assert isinstance(tags, list), f"{filename}: 'metadata.tags' must be a list"
        assert all(_is_non_empty_str(t) for t in tags), f"{filename}: 'metadata.tags' must contain strings"
        assert _is_non_empty_str(metadata.get("author")), f"{filename}: 'metadata.author' must be non-empty"
