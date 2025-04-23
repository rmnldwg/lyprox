"""Define the home view and a maintenance view."""

import logging
from typing import Any

import yaml
from django.shortcuts import render

from lyprox.settings import GITHUB, PUBLICATIONS_PATH

logger = logging.getLogger(__name__)


def add_publications_to_context(context: dict[str, Any]) -> dict[str, Any]:
    """Add the publications stored in a YAML file to the context."""
    with open(PUBLICATIONS_PATH) as file:
        publications = yaml.safe_load(file)

    context["publications"] = publications["references"]
    return context


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


def index(request):
    """Return the landing page HTML.

    This adds the installed apps to the context where the ``add_to_navbar`` attribute
    is set to ``True``.

    It also adds the publications stored in a YAML file to the context.
    """
    context = add_publications_to_context(context={})
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
    return render(request, "index.html", context)


def maintenance(request):
    """Redirect to maintenance page when `lyprox.settings.MAINTENANCE` is ``True``."""
    return render(request, "maintenance.html", {})
