# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 1

"""Object-oriented client for the Practice Hub REST API.

Mini Project 1: authenticate with a bearer token and run a full
create / read / update / delete cycle against ``/api/v1/posts``,
turning HTTP and network failures into meaningful exceptions.
"""

import os

import requests # type: ignore

BASE = "https://practice.fhsucyber.com"
TOKEN = os.environ.get("PRACTICE_API_TOKEN")



# Exceptions

class PracticeHubError(Exception):
    """Base class for every error raised by :class:`PracticeHubClient`."""


class PracticeHubAuthError(PracticeHubError):
    """401 / 403 - the token is missing, invalid, or lacks permission."""


class PracticeHubNotFoundError(PracticeHubError):
    """404 - the requested post does not exist."""


class PracticeHubValidationError(PracticeHubError):
    """400 / 409 / 422 - the server rejected the request payload."""


class PracticeHubServerError(PracticeHubError):
    """5xx - the API failed while handling an otherwise valid request."""


class PracticeHubConnectionError(PracticeHubError):
    """The request never produced an HTTP response (DNS, timeout, refused)."""


# Client

class PracticeHubClient:
    """Talks to the Practice Hub posts API over a persistent session.

    Parameters
    ----------
    base_url:
        Root URL of the API, e.g. ``https://practice.fhsucyber.com``.
    token:
        Bearer token used for authentication.
    timeout:
        Per-request timeout in seconds (default 10).
    session:
        Optional pre-built ``requests.Session`` (handy for tests).
    """

    API_PREFIX = "/api/v1"

    def __init__(self, base_url, token, *, timeout=10, session=None):
        if not token:
            raise PracticeHubAuthError("An API token is required to build the client.")
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )

    # context-manager so the socket is always released
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self):
        self.session.close()

    # CRUD
    def create_post(self, title, body="", tags=None):
        """POST a new post and return the created resource."""
        payload = {"title": title, "body": body, "tags": tags or []}
        return self._request("POST", "/posts", json=payload)

    def list_posts(self, mine=False, tag=None):
        """GET the collection, optionally filtered to ``mine`` and/or a tag."""
        params = {"mine": str(bool(mine)).lower()}
        if tag:
            params["tag"] = tag
        return self._request("GET", "/posts", params=params)

    def get_post(self, post_id):
        """GET a single post by id."""
        return self._request("GET", f"/posts/{post_id}")

    def update_post(self, post_id, **fields):
        """PATCH one or more fields (``title``, ``body``, ``tags``) of a post."""
        if not fields:
            raise PracticeHubValidationError(
                "update_post needs at least one field to change."
            )
        return self._request("PATCH", f"/posts/{post_id}", json=fields)

    def delete_post(self, post_id):
        """DELETE a post. Returns ``True`` once the server confirms removal."""
        self._request("DELETE", f"/posts/{post_id}")
        return True

    # internals
    def _request(self, method, path, **kwargs):
        url = f"{self.base}{self.API_PREFIX}{path}"
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.request(method, url, **kwargs)
        except requests.RequestException as exc:
            raise PracticeHubConnectionError(f"{method} {url} failed: {exc}") from exc
        return self._handle(resp)

    @classmethod
    def _handle(cls, resp):
        """Return the decoded body on success, else raise a typed error."""
        if resp.ok:
            if resp.status_code == 204 or not resp.content:
                return None
            try:
                return resp.json()
            except ValueError as exc:
                raise PracticeHubError(
                    f"Expected JSON from {resp.url} but got: {resp.text[:200]!r}"
                ) from exc

        detail = cls._error_detail(resp)
        status = resp.status_code
        if status in (401, 403):
            raise PracticeHubAuthError(f"{status}: {detail}")
        if status == 404:
            raise PracticeHubNotFoundError(f"{status}: {detail}")
        if status in (400, 409, 422):
            raise PracticeHubValidationError(f"{status}: {detail}")
        if status >= 500:
            raise PracticeHubServerError(f"{status}: {detail}")
        raise PracticeHubError(f"{status}: {detail}")

    @staticmethod
    def _error_detail(resp):
        """Pull the most useful human-readable string out of an error body."""
        try:
            data = resp.json()
        except ValueError:
            return resp.text.strip()[:200] or resp.reason
        if isinstance(data, dict):
            for key in ("detail", "message", "error", "errors"):
                if key in data:
                    return data[key]
        return str(data)[:200]


# CRUD cycle

def _demo(client):
    print(f"posts on the hub: {len(client.list_posts())}")

    created = client.create_post(
        "Week 3 lab", body="My first created post.", tags=["lab", "week3"]
    )
    post_id = created["id"]
    print(f"CREATE -> #{post_id}: {created['title']}")

    fetched = client.get_post(post_id)
    print(f"READ   -> #{post_id}: {fetched['title']!r} / body={fetched.get('body')!r}")

    updated = client.update_post(post_id, body="Edited after review.", tags=["done"])
    print(f"UPDATE -> #{post_id}: body={updated.get('body')!r} tags={updated.get('tags')}")

    client.delete_post(post_id)
    print(f"DELETE -> #{post_id} removed")

    try:
        client.get_post(post_id)
    except PracticeHubNotFoundError:
        print(f"VERIFY -> #{post_id} is gone")
    else:
        print(f"VERIFY -> #{post_id} still readable - delete may not have taken")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "PRACTICE_API_TOKEN is not set - see 'Set your token' in Week 2."
        )

    try:
        with PracticeHubClient(BASE, TOKEN) as client:
            _demo(client)
    except PracticeHubAuthError as exc:
        raise SystemExit(f"Authentication failed: {exc}")
    except PracticeHubConnectionError as exc:
        raise SystemExit(f"Could not reach the API: {exc}")
    except PracticeHubError as exc:
        raise SystemExit(f"API error: {exc}")
