# Mini Project 1 - Practice Hub API client

An object-oriented Python client for the Practice Hub REST API. It authenticates
with a bearer token and runs a full create / read / update / delete cycle against
`/api/v1/posts`.

## Running it

```powershell
$env:PRACTICE_API_TOKEN = "<your token>"
python client.py
```

requests is the only dependency (pip install requests).

Expected output:

```
posts on the hub: 12
CREATE -> #17: Week 3 lab
READ   -> #17: Week 3 lab / body='My first created post.
UPDATE -> #17: body='Edited after review.' tags=['done']
DELETE -> #17 removed
VERIFY -> #17 is gone
```

## Notes on changes

Starting point was a PracticeHubClient with create_post and list_posts
only, no error handling, and a TODO for the rest of CRUD.

### 1. Finished the CRUD surface

| Method | HTTP call | Notes |
| --- | --- | --- |
| create_post(title, body, tags) | POST /api/v1/posts | unchanged behavior |
| list_posts(mine, tag) | GET /api/v1/posts | mine is now sent as "true"/"false" instead of a Python True/False, which some servers don't parse |
| get_post(post_id) | GET /api/v1/posts/{id} | new |
| update_post(post_id, **fields) | PATCH /api/v1/posts/{id} | new; partial update, rejects an empty call |
| delete_post(post_id) | DELETE /api/v1/posts/{id} | new; returns True once the server confirms |

### 2. Typed exceptions

Every failure now raises a subclass of PracticeHubError, so calling code can
catch exactly what it wants instead of parsing status codes:

- PracticeHubAuthError - 401 / 403 (token missing, invalid, or not allowed)
- PracticeHubNotFoundError - 404
- PracticeHubValidationError - 400 / 409 / 422 (bad payload)
- PracticeHubServerError - 5xx
- PracticeHubConnectionError - the request never got an HTTP response
  (DNS failure, timeout, connection refused)

### 3. One place that handles responses

_request builds the URL, applies a timeout, and wraps any
requests.RequestException in PracticeHubConnectionError . _handle then:

- returns None for 204 / empty bodies,
- returns parsed JSON on success (raises PracticeHubError if the body isn't
  JSON when it should be),
- maps error status codes to the exceptions above,
- pulls a readable message out of the error body (detail / message /
  error / errors keys), falling back to raw text.

### 4. Session and lifecycle

- Uses a single requests.Session so the auth header is set once and the TCP
  connection is reused across the CRUD cycle.
- Added __enter__ / __exit__ / close, so with PracticeHubClient(...)
  always releases the socket.
- Constructor raises PracticeHubAuthError immediately if no token is given.
- timeout (default 10s) and a session object are constructor parameters,
  the latter making the client easy to unit-test without real network calls.

### 5. Demo in __main__

The bottom of the file now runs an explicit
create -> read -> update -> delete -> verify-404 sequence and prints each step,
wrapped in handlers that exit cleanly on auth, connection, or generic API
errors.

## AI Usage

I used AI, including Claude Code and ChatGPT, for this assignment. AI helped me with the overall structure of the PracticeHubClient class, the CRUD methods, error handling, debugging, and reviewing the project requirements.
I personally ran and tested the program against the Practice Hub API and made changes based on the results. I also reviewed the code so I could understand what each method does, including how authentication works, how requests are sent, how posts are created, read, updated, and deleted, and how HTTP errors are handled. I changed and tested AI-generated code as needed to make sure it worked correctly for this project. I understand that I am responsible for the final code I submit and should be able to explain how it works. PS i has claude commit this because i was having account issues with the terminal. 
