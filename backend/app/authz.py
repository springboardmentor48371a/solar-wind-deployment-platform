"""
Project-level authorization.

Role-based route access (auth.require_roles) only checks WHAT a role is
allowed to do in general. It does not check WHICH specific project/site a
Planner is allowed to touch. Without this module, a Planner authenticated
as themselves could still read or write another Planner's project just by
guessing/incrementing its ID — a classic IDOR (Insecure Direct Object
Reference) gap. Every route that takes a project_id or site_id must call
one of these before touching the data.

Policy (matches the architecture's per-role service breakdown):
- Administrator, Project Manager: full read + write on every project (portfolio oversight)
- GIS Analyst: full read on every project, and can run analysis (refresh
  environmental/terrain/infrastructure data, recompute scores) on any
  project — that's their whole job per the GIS & Spatial Service — but
  cannot create, edit, or delete a project or site. Their "action set" is
  intentionally different from Planner/PM, not a smaller version of it.
- Investor / Developer, Government / Regulator: read-only oversight
  across every project (portfolio visibility for investment decisions /
  compliance review) — no write, no analysis-triggering.
- Renewable Energy Planner: read + write + run-analysis, but only on
  projects they own.
"""

from fastapi import HTTPException

from app import models

FULL_ACCESS_ROLES = {models.RoleEnum.admin, models.RoleEnum.project_manager}
READ_ONLY_OVERSIGHT_ROLES = {models.RoleEnum.investor_developer, models.RoleEnum.government_regulator}
READ_ALL_ROLES = FULL_ACCESS_ROLES | {models.RoleEnum.gis_analyst} | READ_ONLY_OVERSIGHT_ROLES
ANALYSIS_ROLES = FULL_ACCESS_ROLES | {models.RoleEnum.gis_analyst}

# Roles allowed to create a project/site at all. Ownership rules above
# still apply for reading/writing/analyzing a *specific* existing one.
CAN_CREATE_ROLES = {models.RoleEnum.planner, models.RoleEnum.project_manager, models.RoleEnum.admin}


def can_read_project(project: models.Project, user: models.User) -> bool:
    if user.role in READ_ALL_ROLES:
        return True
    return project.owner_id == user.id


def can_write_project(project: models.Project, user: models.User) -> bool:
    if user.role in FULL_ACCESS_ROLES:
        return True
    return project.owner_id == user.id and user.role in CAN_CREATE_ROLES


def can_run_analysis(project: models.Project, user: models.User) -> bool:
    """
    Analysis = re-pulling environmental/terrain/infrastructure data and
    recomputing suitability for an existing site. Distinct from
    can_write_project: a GIS Analyst can run analysis on any project
    (that's the point of the role) without being able to create, rename,
    or delete it.
    """
    if user.role in ANALYSIS_ROLES:
        return True
    return project.owner_id == user.id and user.role in CAN_CREATE_ROLES


def require_project_read(project: models.Project, user: models.User) -> None:
    if not can_read_project(project, user):
        raise HTTPException(status_code=403, detail="You don't have access to this project")


def require_project_write(project: models.Project, user: models.User) -> None:
    if not can_write_project(project, user):
        raise HTTPException(status_code=403, detail="You don't have permission to modify this project")


def require_project_analysis(project: models.Project, user: models.User) -> None:
    if not can_run_analysis(project, user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to run analysis on this project",
        )
