# Intelligent Multi-Agent Knowledge System

A sophisticated multi-agent system powered by **Google Gemini 2.0 Flash**, designed to intelligently route user queries to specific knowledge namespaces and provide context-aware responses.

## 🚀 Features

-   **Multi-Agent Architecture**:
    -   **User Interaction Agent**: Handles user communication.
    -   **Query Analysis Agent**: Performs semantic analysis to route queries to the correct knowledge domain.
    -   **Namespace Response Agent**: Retrieves specific data and formulates educational responses.
-   **Intelligent Routing**: Dynamically identifies relevant knowledge "namespaces" (e.g., Math, History, Science) based on query intent.
-   **Interactive & CLI Modes**: Run as a chat session or a single-command tool.
-   **Extensible Knowledge Base**: JSON-based data structure (`dummy_data.json`) that is easy to expand.

## 🛠️ Prerequisites

-   Python 3.8+
-   Google Gemini API Key

## 📥 Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd google-adk
    ```

2.  **Create and activate a virtual environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```bash
    GOOGLE_API_KEY=your_gemini_api_key_here
    ```

## 💻 Usage

### Interactive Mode
Start a continuous chat session:
```bash
python main.py
```
*Type `exit` to quit.*

### Command Line Mode
Run a single query:
```bash
python main.py "Tell me about the history of World War II"
```

## 📂 Project Structure

-   `main.py`: Core logic containing agent definitions and orchestration.
-   `dummy_data.json`: The knowledge base containing various namespaces (Math, Science, History, etc.).
-   `requirements.txt`: Python package dependencies.
-   `.env`: Configuration file for API keys (not committed).

## 🤖 Agent Workflow

1.  **User** sends a query.
2.  **Agent 1** (Interaction) forwards it for processing.
3.  **Agent 2** (Analysis) scans `dummy_data.json` to find the matching `namespace_id` (e.g., `namespace_004`).
4.  **Agent 3** (Response) reads the data for that namespace and generates a detailed answer.
