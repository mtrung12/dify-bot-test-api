# Dify Bot Test API

This repository provides an API service for automatically testing chatbot agents deployed on Dify using predefined test datasets. It evaluates bot responses against expected answers using semantic similarity.

## Features

- **Asynchronous Testing**: Upload a test dataset and process it in the background.
- **Semantic Evaluation**: Uses the `dangvantuan/vietnamese-embedding` model to calculate cosine similarity between bot answers and expected answers.
- **Conversation Support**: Maintains conversation context via `conversation_id`.
- **Result Export**: Generates an Excel file with bot responses, similarity scores, and evaluation results.

## Prerequisites

- Python 3.8+
- [Dify API Key](https://docs.dify.ai/v/zh-hans/user-guide/creating-dify-apps/api-access) for the bot you want to test.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/dify-bot-test-api.git
   cd dify-bot-test-api
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the API:
   ```bash
   uvicorn api.main:api --reload
   ```

## API Documentation

### 1. Start a Bot Test
**Endpoint:** `POST /bot-test`

Upload an Excel file containing test cases.

**Headers:**
- `dify-api-key`: Your Dify Application API Key.

**Body (Multipart Form-Data):**
- `file`: An `.xlsx` file.

**Response:**
```json
{
  "request_id": "uuid-string",
  "message": "Test processing started in the background."
}
```

### 2. Get Test Results
**Endpoint:** `GET /bot-test/{request_id}`

Retrieve the results of a specific test.

**Path Parameters:**
- `request_id`: The ID returned by the `/bot-test` endpoint.

**Response:**
- If ready: Downloads the result Excel file.
- If processing: Returns a status message indicating the result is not ready.

---

## Excel File Format

The input Excel file should contain the following columns:

| Column Name | Description | Required |
| :--- | :--- | :--- |
| `message` | The query/input to send to the bot. | Yes |
| `expected_answer` | The reference answer to compare against. | No (Evaluation will be "N/A") |
| `conversation_id` | Unique ID to group messages into a conversation. | No |
| `agent_id` | Reserved for future use. | No |

### Output Columns
The generated result file will include all original columns plus:
- `bot_answer`: The response received from the Dify API.
- `evaluation`: "Đúng" (Correct) if similarity score ≥ 0.5, "Sai" (Incorrect) otherwise.
- `score`: The semantic similarity score (0 to 1).

## Evaluation Logic

The API uses the `SentenceTransformer` model `dangvantuan/vietnamese-embedding` to compute the cosine similarity between the bot's response and the `expected_answer`. 
- **Similarity ≥ 0.5**: Evaluation is "Đúng".
- **Similarity < 0.5**: Evaluation is "Sai".
- **Empty Expected Answer**: Evaluation is "N/A".

## License
MIT
