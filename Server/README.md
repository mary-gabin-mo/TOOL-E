# TOOL-E Server

This is the backend server for the TOOL-E project, built with **FastAPI**. It handles user authentication, tool inventory management, transactions, ML-based tool identification, and analytics.

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   MySQL Database

### Installation

1.  **Clone the repository** and navigate to the `Server` directory.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
### Running the Server

Run the starter script to launch the API:
```bash
python server_entrypoint.py
```
The server will start at `http://0.0.0.0:5000`.

---

### Swagger UI

`http://localhost:5000/docs`

## 📡 API Endpoints

### 🔐 Authentication (`/api/auth`)

#### `POST /validate_user`
Validates a user's Makerspace access via UCID or Barcode. Checks if their waiver is active.
*   **Body**: `{"UCID": 12345678}` or `{"barcode": "28000..."}`
*   **Response**: `{"success": true, "message": "Access Granted, John"}`

#### `POST /api/auth/login`
Admin login for the web dashboard.
*   **Body**: `{"email": "admin@example.com", "password": "..."}`
*   **Response**: `{"token": "...", "user": {...}}`

### 🔧 Tools (`/tools`)

#### `GET /tools`
Returns a list of all tools in the inventory.
*   **Response**: `[{"id": 1, "name": "Hammer", "status": "Available", ...}]`

#### `POST /tools`
Creates a new tool.
*   **Body**: `{"tool_name": "Drill", "tool_type": "Power", "total_quantity": 5, ...}`

#### `PUT /tools/{tool_id}`
Updates an existing tool's details or inventory count.

### 📦 Transactions (`/transactions`)

#### `GET /transactions`
Retrieves transaction history with filtering and pagination.
*   **Query Params**: `page`, `limit`, `start_date`, `end_date`, `status`, `search_term`
*   **Response**: `{"items": [...], "total": 100, "page": 1}`

#### `POST /transactions`
Records a checkout (borrowing) of a tool.
*   **Special Logic**: If `image_path` (filename from ML) is provided, the server moves the image from the `temp/` folder to `captured_images/Yes/ToolName/` or `captured_images/No/ToolName/` based on `classification_correct`.
*   **Body**:
    ```json
    {
      "user_id": "<UCID>",
      "tool_id": 5,
      "image_path": "uuid.jpg",
      "classification_correct": true,
      "quantity": 1
    }
    ```

#### `PUT /transactions/{transaction_id}`
Updates a transaction (e.g., marking it as returned by setting `return_timestamp`).

### 🤖 Machine Learning (`/identify_tool`)

#### `POST /identify_tool`
Uploads an image to identify the tool. The image is saved temporarily.
*   **Form Data**: `file` (Image Upload)
*   **Response**:
    ```json
    {
      "success": true,
      "prediction": "Hammer",
      "score": 0.98,
      "image_filename": "550e8400-e29b-....jpg"
    }
    ```

### 📊 Analytics (`/analytics`)

#### `GET /analytics/dashboard`
Provides aggregated stats for the admin dashboard.
*   **Query Params**: `period` (e.g., `1_month`, `winter_2026`)
*   **Response**:
    ```json
    {
      "live_stats": {"total_tools": 50, "current_borrowed": 12},
      "period_stats": {"top_tools": [...]}
    }
    ```
