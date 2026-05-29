"""Skill loading and simple runtime selection."""

from __future__ import annotations

from pathlib import Path
import re

import yaml

from app.models import SkillDefinition


def load_skills(skills_dir: Path) -> list[SkillDefinition]:
    """Load markdown skills with YAML front matter."""
    skills: list[SkillDefinition] = []
    for path in sorted(skills_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, instructions = _split_front_matter(text)
        skills.append(
            SkillDefinition(
                name=metadata["name"],
                description=metadata.get("description", ""),
                when_to_use=metadata.get("when_to_use", []),
                required_tools=metadata.get("required_tools", []),
                examples=metadata.get("examples", []),
                instructions=instructions.strip(),
                source_path=str(path),
            )
        )
    return skills


def select_skills(task: str, skills: list[SkillDefinition], default_skill: str) -> list[SkillDefinition]:
    """Perform transparent keyword-based skill selection."""
    query_terms = set(_tokenize(task))
    selected: list[SkillDefinition] = []
    for skill in skills:
        corpus = " ".join([skill.name, skill.description, *skill.when_to_use]).lower()
        corpus_terms = set(_tokenize(corpus))
        if query_terms & corpus_terms:
            selected.append(skill)

    if not selected:
        for skill in skills:
            if skill.name == default_skill:
                return [skill]
    return selected


def _split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ValueError("Skill file is missing YAML front matter.")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Skill file front matter is malformed.")
    metadata = yaml.safe_load(parts[1]) or {}
    instructions = parts[2]
    return metadata, instructions


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())
