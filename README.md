
# 🔬 LLM-Powered Autonomous Fact-Checker

This project is a Streamlit web application that leverages Large Language Models (LLMs), web search capabilities, a local knowledge base, and source reliability assessment to autonomously fact-check claims.

**[Link to Deployed App - e.g., your-app-name.streamlit.app](https://your-app-name.streamlit.app)** (Replace with your actual link once deployed)

## 🌟 Features

*   **Claim Analysis:** Breaks down user-submitted claims into key components for verification.
*   **Web Search Integration:** Utilizes DuckDuckGo to gather real-time evidence from the web.
*   **Source Reliability Evaluation:** Assesses the credibility of information sources found during web search using an LLM and a pre-defined reliability score for common domains.
*   **Knowledge Base:** Maintains a local vector database (ChromaDB with HuggingFace embeddings) of verified facts. High-confidence "True" or "False" verdicts are added to this knowledge base.
*   **Enhanced Verdict Generation:** Provides a detailed verdict ("True", "False", "Partially True", "Unverifiable") along with:
    *   Confidence Score (0-100)
    *   Detailed Explanation
    *   Key Evidence Points
    *   List of Supporting Source Domains
    *   Contradicting Evidence (if any)
    *   Relevance of Knowledge Base
*   **Caching:** Implements caching for search results and final verdicts to improve performance and reduce redundant API calls.
*   **Interactive Web Interface:** Built with Streamlit for an easy-to-use experience.
*   **Fact-Checking History:** Stores and displays previous fact-checks.
*   **Reasoning Visualization:** (Basic) Graph visualization of the claim, entities, evidence, and verdict.

## ⚙️ Technology Stack

*   **Language Model:** Google Gemini (via `langchain-google-genai`)
*   **Orchestration:** LangChain
*   **Web Framework:** Streamlit
*   **Web Search:** DuckDuckGo (`langchain_community.utilities.DuckDuckGoSearchAPIWrapper`)
*   **Vector Database:** ChromaDB (`langchain_community.vectorstores.Chroma`)
*   **Embeddings:** HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`)
*   **Programming Language:** Python 3
*   **Visualizations:** Plotly, Streamlit-Agraph

## 🛠️ Setup and Installation

### Prerequisites

*   Python 3.10+
*   Git
*   A Google API Key with the Gemini API enabled.

### Local Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory of the project and add your Google API key:
    ```env
    GOOGLE_API_KEY="your_google_api_key_here"
    ```
    **Note:** The `.env` file is included in `.gitignore` and should NOT be committed to version control.

## 🚀 Running the Application

### Streamlit Web App

To run the web application:
```bash
streamlit run app.py
```
Open your browser and go to `http://localhost:8501`.

### Command-Line Interface (CLI)

To run the CLI version:
```bash
python main_cli.py
```

## 📂 Project Structure

```
your_project_directory/
├── .env                   # Stores API keys (not committed)
├── .gitignore             # Specifies intentionally untracked files
├── app.py                 # Main Streamlit application file
├── cache_manager.py       # Handles caching of search results and verdicts
├── fact_checker.py        # Core fact-checking logic and orchestration
├── knowledge_base.py      # Manages the ChromaDB vector store
├── llm_utils.py           # Initializes LLM and search tools
├── main_cli.py            # Command-line interface entry point
├── requirements.txt       # Python dependencies
├── source_evaluator.py    # Evaluates the reliability of information sources
├── verdict_generator.py   # Generates the final verdict
├── README.md              # This file
└── cache_data/            # (Generated) Directory for cached data
└── knowledge_base_db/     # (Generated) Directory for ChromaDB data
```

## 📜 How It Works

1.  **Claim Input:** The user enters a claim into the Streamlit interface.
2.  **Claim Analysis:** The LLM analyzes the claim to identify key entities and sub-claims that need verification, and generates relevant search queries.
3.  **Evidence Gathering:** The system uses the generated queries to search the web (DuckDuckGo).
4.  **Source Evaluation:** For each piece of evidence, the source is evaluated for reliability.
5.  **Knowledge Base Query:** The claim is checked against the existing knowledge base for relevant pre-verified facts.
6.  **Verdict Generation:** The LLM synthesizes the claim, collected evidence, source reliability scores, and knowledge base facts to produce a comprehensive verdict, confidence score, and explanation.
7.  **Caching:** Results are cached to speed up future identical requests.
8.  **Knowledge Base Update:** If the verdict is "True" or "False" with high confidence, the (negated) claim is added to the knowledge base.
9.  **Display:** The results, including analysis, evidence, and the final verdict, are displayed to the user.

## 🔗 Deployment

This application can be deployed on platforms like [Streamlit Community Cloud](https://share.streamlit.io/), Hugging Face Spaces, Google Cloud Run, etc.
Remember to set the `GOOGLE_API_KEY` as a secret or environment variable on your chosen deployment platform.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for bugs, feature requests, or improvements.

## 📝 License

This project is licensed under the MIT License 


