"""Define the home view and a maintenance view."""

from __future__ import annotations

import logging
from typing import Any

from django.shortcuts import render
from habanero import Crossref, WorksContainer
from pydantic import BaseModel

from lyprox.settings import (
    CROSSREF,
    GITHUB,
    JOBLIB_MEMORY,
    REFERENCES,
)

logger = logging.getLogger(__name__)


def add_lycosystem_repos_to_context(
    context: dict[str, Any],
    repo_ids_and_img_paths: list[tuple[str, str]],
    ref: str = "main",
) -> dict[str, Any]:
    """Add infos about the repositories of the lycosystem to the context."""
    context["lycosystem_repos"] = []

    for repo_id, img_path in repo_ids_and_img_paths:
        repo = GITHUB.get_repo(repo_id)
        context["lycosystem_repos"].append(
            {
                "owner": repo.owner.login,
                "name": repo.name,
                "description": repo.description,
                "url": repo.html_url,
                "docs_url": f"https://{repo.owner.login}.github.io/{repo.name}/",
                "num_stars": repo.stargazers_count,
                "num_forks": repo.forks_count,
                "social_card_url": f"https://github.com/{repo_id}/blob/{ref}/{img_path}?raw=true",
            }
        )

    return context


class AuthorName(BaseModel):
    """Model for an author name."""

    given: str
    family: str
    orcid: str | None = None

    @property
    def full_name(self) -> str:
        """Return the full name of the author."""
        return f"{self.given} {self.family}"

    @property
    def short_name(self) -> str:
        """Return the short name of the author."""
        return f"{self.given[0]}. {self.family}"


class Publication(BaseModel):
    """Model for a publication."""

    title: str
    authors: list[AuthorName]
    year: int
    doi: str
    journal: str
    volume: str
    num_citations: int = 0

    @classmethod
    def from_works_container(cls: type, works_container: WorksContainer) -> Publication:
        """Create a Publication instance from a WorksContainer."""
        return cls(
            title=works_container.title[0][0],
            authors=[
                AuthorName(
                    given=author["given"],
                    family=author["family"],
                    orcid=author.get("ORCID"),
                )
                for author in works_container.author[0]
            ],
            year=works_container.published[0]["date-parts"][0][0],
            doi=works_container.doi[0],
            journal=works_container.container_title[0][0],
            volume=works_container.volume[0],
            num_citations=works_container.is_referenced_by_count[0],
        )

    @property
    def author_names(self) -> str:
        """Return the authors as a string."""
        return ", ".join(author.full_name for author in self.authors)

    def bibliography(self) -> str:
        """Return the publication as a bibliographic string."""
        authors = ", ".join(author.full_name for author in self.authors)
        return (
            f"{authors}. {self.title}. "
            f"{self.journal}, {self.volume} ({self.year}). "
            f"https://doi.org/{self.doi}"
        )


@JOBLIB_MEMORY.cache
def fetch_works_from_doi(
    crossref: Crossref,
    doi: str,
) -> WorksContainer | None:
    """Get the reference from a DOI using Crossref.

    This function is cached to avoid hitting the Crossref API too often.
    """
    try:
        response = crossref.works(ids=doi)
        return WorksContainer(response)
    except Exception as e:
        logger.error(f"Error getting reference for DOI {doi}: {e}")
        return None


def add_publications_to_context(
    context: dict[str, Any],
    dois: list[str],
) -> dict[str, Any]:
    """Add resolved references of publicationsto the context, given a list of DOIs."""
    context["publications"] = []

    for doi in dois:
        works = fetch_works_from_doi(crossref=CROSSREF, doi=doi)
        publication = Publication.from_works_container(works) if works else None
        if not publication:
            logger.warning(f"Could not resolve DOI {doi}")
            continue
        context["publications"].append(publication)

    return context


def index(request):
    """Return the landing page HTML.

    This adds the installed apps to the context where the ``add_to_navbar`` attribute
    is set to ``True``.

    It also adds the publications stored in a YAML file to the context.
    """
    context = {}
    context = add_lycosystem_repos_to_context(
        context=context,
        repo_ids_and_img_paths=[
            ("rmnldwg/lymph", "docs/source/_static/github-social-card.png"),
            ("lycosystem/lyprox", "lyprox/static/github-social-card.png"),
            ("rmnldwg/lydata", "github-social-card.png"),
            ("rmnldwg/lyscripts", "github-social-card.png"),
            ("lycosystem/lymixture", "github-social-card.png"),
        ],
        ref="main",
    )
    context = add_publications_to_context(
        context=context,
        dois=REFERENCES,
    )
    return render(request, "index.html", context)


def maintenance(request):
    """Redirect to maintenance page when `lyprox.settings.MAINTENANCE` is ``True``."""
    return render(request, "maintenance.html", {})
