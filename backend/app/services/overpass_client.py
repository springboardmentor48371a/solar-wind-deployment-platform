"""
Shared Overpass query helper with a real fallback mirror — used by both
infrastructure.py and land_data.py, which each independently query
Overpass and were each hit by the same underlying flakiness ("0
infrastructure features found", environmental data stuck on "not
fetched"). Public Overpass servers are well known to occasionally
time out, rate-limit, or return errors under load; trying a second,
independent, real public mirror before giving up is a genuine
reliability improvement, not just a longer timeout on the same
unreliable server.
"""

import requests

from app.config import settings


def query_overpass(query: str, timeout: int = 20) -> dict:
    """
    POSTs an Overpass QL query to the primary server, falling back to a
    second real public mirror if the primary fails for any reason.
    Raises the primary server's own exception if BOTH fail, so callers'
    existing try/except + "Warning: ... fetch failed" logging continues
    to work exactly as before — this only adds a real second attempt,
    it doesn't change how a total failure is reported.

    Timeout history, both changes made for real reasons found via live
    testing: originally 30s, lowered to 8s after confirming Overpass
    was fully unreachable from a user's network (a ~42s hang before
    failing) — no point waiting 30s per attempt for a connection that
    was never going to succeed. Raised back up to 20s after a second,
    different real issue: the search radius for protected areas/water
    bodies was separately widened to 75km (from land_data.py's original
    20km) to fix a different bug, but a ~14x larger search area
    genuinely takes public Overpass servers longer to process even when
    the network itself is fine — 8s cut off legitimately slow-but-
    working queries once the network block was actually resolved. 20s
    is still meaningfully faster than the known ~42s network-block
    signature (so a genuine block still fails in well under half that
    time), while giving a real, wider query room to actually complete.
    """
    try:
        response = requests.post(settings.overpass_api_base_url, data={"data": query}, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as primary_exc:  # noqa: BLE001
        print(f"Warning: primary Overpass server failed ({primary_exc}), trying fallback mirror")
        try:
            response = requests.post(settings.overpass_api_fallback_url, data={"data": query}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception:
            # Both failed — re-raise the PRIMARY server's original
            # exception, since that's the one the caller's existing
            # warning message and log-grepping instructions already
            # reference, and it's the one actually configured/expected.
            raise primary_exc
