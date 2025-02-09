# Base62 Snowflake URL Shortener

This project implements a simple URL shortener service using Flask and a custom Base62 Snowflake ID generator. The service provides endpoints to create, retrieve, update, delete, and view statistics for shortened URLs.

## Features

- **Generate Short URLs:** Uses a custom Base62 Snowflake algorithm for generating unique IDs.
- **CRUD Operations:** Create, read, update, and delete shortened URLs.
- **Statistics:** Track clicks, creation time, and last access time.
- **In-Memory Storage:** URL mappings and statistics are stored in memory.

## Prerequisites

- Python 3.7 or higher
- `pip` (Python package installer)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Neon-Face/Web-Services-and-Cloud-Based-Systems-Group-23.git
   cd Web-Services-and-Cloud-Based-Systems-Group-23/Assignment_1
   ```

2. Install the required packages:
   ```bash
   pip install flask pybase62
   ```


## Running the Application

To start the Flask development server, run:

```bash
python base62_snowflake.py
```

The application will start in debug mode and listen on `http://127.0.0.1:8000/`.

## API Endpoints

### 1. Create a Short URL

- **Endpoint:** `POST /`
- **Payload:** JSON with a `value` key containing the original URL.

  **Example Request:**

  ```json
  {
    "value": "https://github.com"
  }
  ```

  **Response:**

  ```json
  {
    "id": "generated_short_id"
  }
  ```

### 2. Redirect / Retrieve URL

- **Endpoint:** `GET /<short_id>`
- **Response:** Returns the original URL and increments the click counter.

  **Response Example (with status 301):**

  ```json
  {
    "value": "https://github.com"
  }
  ```

### 3. Update URL

- **Endpoint:** `PUT /<short_id>`
- **Payload:** JSON with a `url` key containing the new URL.

  **Example Request:**

  ```json
  {
    "url": "https://gitlab.com"
  }
  ```

  **Response:**

  ```json
  {
    "message": "Updated successfully"
  }
  ```

### 4. Delete a Short URL

- **Endpoint:** `DELETE /<short_id>`
- **Response:** No content (HTTP 204) on success.

### 5. Retrieve URL Statistics

- **Endpoint:** `GET /stats/<short_id>`
- **Response:** Returns statistics including click count, creation timestamp, and last accessed time.

  **Response Example:**

  ```json
  {
    "clicks": 5,
    "created_at": 1672531199.123,
    "last_accessed": 1672531299.456
  }
  ```

### 6. List All Short URLs

- **Endpoint:** `GET /`
- **Response:** JSON list of all stored short URL IDs.

  **Response Example:**

  ```json
  {
    "urls": ["short_id1", "short_id2", "..."]
  }
  ```

### 7. Delete All URLs

- **Endpoint:** `DELETE /`
- **Response:** Returns an empty body with HTTP status 404 after clearing all data.

## Examples

Here are some sample `curl` commands to interact with the API:

1. **Create a Short URL:**

   ```bash
   curl -X POST http://127.0.0.1:8000/ \
        -H "Content-Type: application/json" \
        -d '{"value": "https://github.com"}'
   ```

2. **Retrieve the Original URL:**

   ```bash
   curl -X GET http://127.0.0.1:8000/<short_id>
   ```

3. **Update an Existing URL:**

   ```bash
   curl -X PUT http://127.0.0.1:8000/<short_id> \
        -H "Content-Type: application/json" \
        -d '{"url": "http://gitlab.com"}'
   ```

4. **Delete a Short URL:**

   ```bash
   curl -X DELETE http://127.0.0.1:8000/<short_id>
   ```

5. **Get URL Statistics:**

   ```bash
   curl -X GET http://127.0.0.1:8000/stats/<short_id>
   ```


