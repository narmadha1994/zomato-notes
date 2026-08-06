# Zomato Notes

An internal notes and knowledge-base application for on-call engineers.

The project uses a **FastAPI + SQLAlchemy backend** and a **HTML/CSS/JavaScript frontend**. It includes CRUD operations, search, custom sorting algorithms, binary search, linear search, SQL reporting, recursive category rendering, and frontend integration.
---

## Project Overview

Zomato Notes is designed as an internal knowledge-base application where users can:

* Create notes
* View notes
* Update notes
* Delete notes using token authentication
* Search notes
* Sort notes by relevance or date
* Find notes by exact title
* Use iterative or recursive binary search
* Quickly find notes by tag
* Navigate notes using Quick Tag Jump
* View a recursive category tree
* Import notes from a text file
* Generate SQL-based reports

The backend is implemented using **FastAPI**, with **SQLAlchemy** used for database access.

The frontend is a plain **HTML/CSS/JavaScript** application served using a local static development server.

---

# Project Structure

zomato-notes/
│
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── crud.py
│   ├── algorithms.py
│   ├── seed.py
│   ├── ranking_dataset.py
│   ├── ai_service.py
│   ├── semantic_search.py
│   ├── ai_sample_notes.py
│   ├── requirements.txt
│   ├── .env.example
│   └── zomato_notes.db
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── README.md
└── sample_import.txt

---

# Technologies Used

## Backend

* Python
* FastAPI
* SQLAlchemy
* SQLite
* Pydantic
* Uvicorn

## Frontend

* HTML5
* CSS3
* JavaScript
* Fetch API

## Algorithms

* Insertion Sort
* Iterative Binary Search
* Recursive Binary Search
* Linear Search with found-flag

---

# Backend Setup

## 1. Open the backend folder

cd zomato-notes/backend

## 2. Create a virtual environment
python -m venv venv

## 3. Activate the virtual environment

venv\Scripts\activate

## 4. Install dependencies
pip install -r requirements.txt
---

# Database Setup

The application uses SQLite with SQLAlchemy.
The database tables are created automatically when the FastAPI application starts.
To populate the database with sample users and notes:

python seed.py

The seed process creates:
* Sample users
* Part 1 notes
* Demo knowledge-base notes
* Ranking dataset notes

The seed script also prints the notes that were inserted into the database.

---

# Running the Backend

From the `backend` directory:

uvicorn main:app --reload
The backend runs at:

http://127.0.0.1:8000
FastAPI Swagger documentation is available at:

http://127.0.0.1:8000/docs
---

# Running the Frontend

The frontend is served using a local static development server.
The expected frontend origin is:

http://127.0.0.1:5500

Open:
frontend/index.html
using the static development server.
The frontend communicates with the FastAPI backend at http://127.0.0.1:8000

---

# CORS Configuration
The frontend is served locally using a static development server.
Allowed frontend origin: http://127.0.0.1:5500

The FastAPI backend is served at:http://127.0.0.1:8000
The backend uses FastAPI `CORSMiddleware` to allow the frontend to communicate with the API across origins.

---

# API Endpoints
## Root Endpoint

### GET `/`

Checks whether the API is running.
Example:

GET http://127.0.0.1:8000/
Response:
json
{
  "message": "Zomato Notes API is running"
}
---

# User Endpoints
## Create User

### POST `/users`

Creates a new user.
The endpoint checks whether the email already exists before creating the user.
Duplicate email addresses return:

text
409 Conflict
---

# Note CRUD Endpoints

## Create Note
### POST `/notes`

Creates a new note.

Required fields include:

* title
* content
* tag
* owner_id

The backend checks whether the owner exists before creating the note.

---

## Get Notes

### GET `/notes`

Returns notes ordered by creation date.
Optional tag filtering is supported:

text
GET /notes?tag=work
---

## Get Single Note
### GET `/notes/{note_id}`

Returns a specific note using its ID.
If the note does not exist:

text
404 Not Found
---

## Update Note
### PUT `/notes/{note_id}`

Updates an existing note.
---

## Delete Note

### DELETE `/notes/{note_id}`

Deletes a note.

The endpoint requires the custom header:

x-token: zomato-secret-token
Invalid or missing tokens return:
403 Forbidden
---

# Import Notes

## POST `/notes/import`

Imports notes from a `.txt` file.
Each non-empty line in the uploaded text file becomes a separate note.
The endpoint checks that the supplied owner exists before processing the file.

Example:
POST /notes/import?owner_id=1

---

# Part 2 — Integrated Ranking Engine

The ranking engine is implemented in:

backend/algorithms.py
and integrated with the live FastAPI application.

---

# 2.1 Custom Insertion Sort

The function:

python
insertion_sort_by_key(items: list[dict], key: str) -> list[dict]
sorts dictionaries in **descending order** based on a specified numeric key.

The implementation is written from scratch and does not use Python's built-in `sort()` or `sorted()` functions.

The algorithm uses:

* An outer loop over each element
* A backward inner loop
* Element movement/swapping
* A specified dictionary key

The same function is reused for both relevance sorting and date sorting.

---

# 2.2 Relevance Search

The endpoint is:
GET /notes/search?keyword=<value>

For relevance search:

1. The current notes are fetched from the database.
2. The keyword is converted to lowercase.
3. Each note's content is converted to lowercase.
4. The number of case-insensitive keyword occurrences is counted using the string `count()` method.
5. The count is stored in a `score` field.
6. `insertion_sort_by_key()` sorts the notes by score in descending order.
7. Only the top five results are returned.

No regular expressions are used.

### Test Request

GET /notes/search?keyword=apple

### Test Result

HTTP 200 OK

Example result:

json
[
  {
    "id": 11,
    "title": "Apple Harvest Notes",
    "content": "The apple orchard yielded a strong apple harvest this season with apple crates ready.",
    "tag": "random",
    "owner_id": 1,
    "created_at": "2026-07-30T17:14:29.111102",
    "score": 3
  },
  {
    "id": 17,
    "title": "Garden Update",
    "content": "The garden apple tree is finally blooming after the apple tree pruning last month.",
    "tag": "random",
    "owner_id": 1,
    "created_at": "2026-07-30T17:14:29.111113",
    "score": 2
  },
  
  {
    "id": 22,
    "title": "Language Practice",
    "content": "Practiced twenty new vocabulary words during today's language session.",
    "tag": "random",
    "owner_id": 1,
    "created_at": "2026-07-30T17:14:29.111119",
    "score": 0
  },
  
This test demonstrates that:

* The keyword occurrences are counted correctly.
* Notes are ranked by descending score.
* The result is limited to five notes.
* The custom insertion-sort implementation is being used.

---

# 2.3 Date Sorting

The same `insertion_sort_by_key()` function is reused for date sorting.

The endpoint is:
GET /notes/search?sort_by=date

For this mode:

1. Current notes are fetched.
2. Each note's `created_at` value is converted into a numeric `created_at_epoch` value.
3. The same insertion-sort function is called using:

python
insertion_sort_by_key(
    notes_data,
    key="created_at_epoch"
)


### Test Request
GET /notes/search?sort_by=date

### Test Result
HTTP 200 OK

Example response:

json
[
  {
    "id": 22,
    "title": "Language Practice",
    "content": "Practiced twenty new vocabulary words during today's language session.",
    "tag": "random",
    "owner_id": 1,
    "created_at": "2026-07-30T17:14:29.111119",
    "created_at_epoch": 1785411869.111119
  },
  {
    "id": 21,
    "title": "Kitchen Inventory",
    "content": "Checked the kitchen inventory; running low on coffee and sugar.",
    "tag": "random",
    "owner_id": 1,
    "created_at": "2026-07-30T17:14:29.111118",
    "created_at_epoch": 1785411869.111118
  },
  
]

The results demonstrate that the notes are sorted by descending creation time.

This also demonstrates that `insertion_sort_by_key()` is reusable with different numeric keys rather than being hardcoded for relevance scores.

---

# 2.4 Iterative Binary Search

The function:

python
binary_search_iterative(
    sorted_titles: list[str],
    target: str
) -> int

searches for an exact title in an alphabetically sorted list.

The implementation is iterative and uses the overflow-safe midpoint formula:

python
mid = start + (end - start) // 2

If the title is found, its index is returned.
If the title is absent:

text
-1
is returned.

---

# 2.5 Recursive Binary Search

The function:

python
binary_search_recursive(
    sorted_titles: list[str],
    target: str,
    start: int,
    end: int
) -> int
performs the same exact-title search recursively.
It has an explicit base case:

python
if start > end:
    return -1

The function recursively searches either the left or right half of the sorted title list.

---

# 2.6 Binary Search API Integration

Both binary-search functions are integrated into:

text
GET /notes/lookup?title=<exact title>&algo=iterative|recursive
The backend first obtains notes using SQL-level ordering:
.order_by(Note.title.asc())

This ensures that the title list is alphabetically sorted before binary search is performed.
Python built-in sorting is not used.

The `algo` parameter determines which search implementation is used.

---

## Iterative Test

Request:GET /notes/lookup?title=Morning%20Run&algo=iterative
Result: HTTP 200 OK
Response:

json
{
  "id": 4,
  "title": "Morning Run",
  "content": "Ran 5km along the river trail before breakfast, felt great.",
  "tag": "health",
  "owner_id": 1,
  "created_at": "2026-07-30T17:14:29.096502"
}

---

## Recursive Test

Request:GET /notes/lookup?title=Morning%20Run&algo=recursive
The endpoint selects:
algo=recursive
and calls the recursive binary-search implementation.
Both iterative and recursive modes successfully locate the exact title.

---

# 2.7 Linear Search with Found Flag

The function:
linear_search(
    items: list[dict],
    key: str,
    value
) -> dict | None

scans a list sequentially.

It uses an explicit found-flag pattern:found = False
The function continues scanning until:

* A matching item is found, or
* The end of the list is reached.

The first matching dictionary is returned.
If there is no match:None is returned.
---

# 2.8 Quick Tag Find API

The linear-search function is integrated into:
GET /notes/quick-find?tag=<value>

Example:GET /notes/quick-find?tag=work

The endpoint fetches notes and calls:

linear_search(
    notes_data,
    key="tag",
    value=tag
)

The first matching note is returned.
If no matching note exists, the API returns a message indicating that no note was found.

### Test Result

GET /notes/quick-find?tag=work

Response:

json
{
  "id": 1,
  "title": "Standup Summary",
  "content": "Discussed sprint progress, blockers on the payments API integration, and the plan for the demo on Friday.",
  "tag": "work",
  "owner_id": 1
}
---

# 2.9 Frontend Algorithm Controls

The frontend provides real controls connected to the backend APIs.

## Sort by

The search interface provides:
Sort by:
[ Relevance ▼ ]

Options:

* Relevance
* Date

Relevance uses:/notes/search?keyword=<value>

Date sorting uses:/notes/search?sort_by=date
---

## Jump to Exact Title

The frontend provides:

Jump to Exact Title
[ Enter exact title ]
[ Iterative ▼ ]
[ Find ]

The user can select:

* Iterative
* Recursive

The frontend calls:/notes/lookup
with the selected algorithm.

---

## Quick Tag Jump

The frontend provides Quick Tag Jump functionality for real tags:

* Work
* Health
* Recipes
* Travel
* Random

Clicking a tag button calls:/notes/quick-find?tag=<value>

The returned note is then:

1. Located in the notes dashboard.
2. Scrolled into view.
3. Highlighted for the user.

---

# Recursive Category Tree

The frontend includes a recursive category tree.
The category structure contains nested categories such as:

All Tags
├── Work
│   ├── Standups
│   └── Retros
│
├── Personal
│   ├── Health
│   │   └── Fitness
│   └── Recipes
│
└── Travel

The tree is rendered using the recursive JavaScript function:

javascript
renderCategoryTree(node, parentElement)
Categories with children can be expanded and collapsed.

---

# SQL Reporting Endpoints

The backend also includes SQL reporting endpoints.

## Tag Summary

GET /reports/tag-summary
Uses SQL `GROUP BY` and `HAVING`.

The report returns tags having more than one note and orders them by note count.
---

## Long Notes

GET /reports/long-notes
Returns notes whose content length is greater than the average note content length.

The query uses SQL `AVG()` and `LENGTH()`.

---

## User Notes Report

GET /reports/user-notes
Uses a SQL `LEFT JOIN` between users and notes.

The report shows:

* User ID
* User name
* User email
* Number of notes

Results are ordered by note count.

---

# Middleware

The backend includes custom ASGI middleware that calculates request processing time.

The response includes:X-Process-Time
The value represents the approximate time required to process the request.

---

# Background Task

When creating a note, the backend includes a background indexing task.
The indexing function simulates a delayed indexing operation:

python
def index_note(note_id: int):
    time.sleep(3)
The purpose is to demonstrate FastAPI `BackgroundTasks`.
# Verification

The following endpoints have been tested successfully through FastAPI Swagger:

GET /notes/search?keyword=apple
GET /notes/search?sort_by=date
GET /notes/lookup?title=Morning%20Run&algo=iterative
GET /notes/lookup?title=Morning%20Run&algo=recursive
GET /notes/quick-find?tag=work

The tested endpoints returned:
HTTP 200 OK


The frontend was also tested to verify:

* Relevance search
* Date sorting
* Exact title lookup
* Iterative binary search selection
* Recursive binary search selection
* Quick Tag Jump
* Scrolling to the matching note
* Highlighting the matching note
* Recursive category tree rendering

---

# Algorithm Requirements

The project intentionally implements the required algorithms from scratch.

## Insertion Sort

No built-in Python sorting is used.

```python
insertion_sort_by_key(items, key)
```

Sorts in descending order.

## Iterative Binary Search

Uses:

mid = start + (end - start) // 2
and performs the search iteratively.

## Recursive Binary Search

Uses recursion with the explicit base case:
```python
if start > end:
    return -1
```
## Linear Search

Uses an explicit:
```python
found = False
```
flag to sequentially scan the list.
---

# Example API Testing

Swagger UI can be used to test all endpoints:
http://127.0.0.1:8000/docs

Recommended tests:
### Relevance
/notes/search?keyword=apple

### Date
/notes/search?sort_by=date
### Iterative lookup
/notes/lookup?title=Morning%20Run&algo=iterative

### Recursive lookup
/notes/lookup?title=Morning%20Run&algo=recursive
### Linear search
/notes/quick-find?tag=work
---

# Part 3 – Integrated Intelligence Layer

## Overview

Part 3 extends the Zomato Notes application with AI-powered note intelligence and semantic search.
It introduces two major capabilities:
- AI Auto-Tagging using a mock LLM interface
- Offline Semantic Search using Sentence Transformers

---

## Features

### 1. AI Auto-Tagging

When a new note is created:

- The backend sends the note content to `get_ai_response()`.
- The AI returns:
  - Suggested tags
  - A one-sentence summary
- The response is parsed using `json.loads()`.
- The API returns:

```json
{
  "ai_suggestion": {
    "tags": [
      "work",
      "backend"
    ],
    "summary": "Backend API deployment reminder."
  }
}
```

If parsing fails:

- The note is still created successfully.
- `ai_suggestion` is returned as `null`.
- The raw AI response is logged for debugging.

---

### 2. AI Suggestion Panel

After creating a note, the frontend displays:

- Suggested tags
- AI-generated summary
- "Apply as Tag" button

The Apply button updates the note using the existing
PUT /notes/{id}
endpoint.
---

### 3. Local Semantic Search

The project uses

``` sentence-transformers==3.0.0 ```
with the pretrained model
sentence-transformers/all-MiniLM-L6-v2
The model generates embeddings for every sample note.
A search query is converted into an embedding and compared against all notes using cosine similarity.
The backend returns the Top 3 most relevant notes ranked by similarity.

Example response:

```json
[
    {
        "title": "Gym schedule change",
        "score": 0.6546
    },
    {
        "title": "Morning workout plan",
        "score": 0.6399
    },
    
]
---

### 4. Smart Search API

Endpoint
GET /notes/smart-search?q=<query>
Example

GET /notes/smart-search?q=leg day exercise plan


Returns
- Top 3 semantically similar notes
- Similarity score
- Ranked from highest similarity to lowest

---

### 5. Frontend Integration

The frontend includes:

- Smart Search (AI) input
- Search button
- Ranked semantic search results
- Similarity score display
- AI Suggestion panel for newly created notes
- Apply Tag functionality

---

## Notes
- Semantic search works completely offline after the model has been downloaded once.
- No API key is required for semantic search.
- AI Auto-Tagging currently uses a deterministic mock AI service for reproducible outputs.

