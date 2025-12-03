'''
# AI Quiz Generator with RAG

A Flask-based application that makes quiz questions from study notes with Retrieval-Augmented Generation (RAG).


## Presentation
https://www.youtube.com/watch?v=ljyhb_3cCDw

### Core Features
- **Quiz Generation**: Generates quiz questions with hints and grading rubrics
- **RAG Enhancement**: Uses embeddings and vector search to retrieve relevant context
- **Web Interface**:Basic, User-friendly web UI
- **Safety & Robustness**:
  - Input validation and length limits (50K characters)
  - Prompt injection detection
  - Error handling with fallback messages
  - System prompt with explicit safety rules

### Telemetry
Tracks:
- Timestamp
- Pathway (RAG/error)
- Latency (ms)
- Token usage
- Estimated cost
- Number of chunks retrieved

### Evaluation
- 16 test cases covering diverse topics
- Automated evaluation script
- Pass rate reporting

## Installation

### Prerequisites
- Python 3.8+
- Gemini API key

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. Run the application:
```bash
python app.py
```

5. Open browser to `http://localhost:5000`

## Usage

### Web Interface
1. Visit `http://localhost:5000`
2. Paste your study notes into the text area
3. Configure options (hints, rubrics)
4. Click "Generate Quiz"
5. View generated questions with hints and rubrics

### Running Evaluation
```bash
python evaluate.py
```

This runs all test cases from `tests.json` and outputs:
- Individual test results
- Pass/fail status
- Overall pass rate


# Components

1. **app.py**: Flask application with routes and request handling
2. **llm_client.py**: Gemini API wrapper with system prompt
3. **rag_engine.py**: RAG implementation with text chunking and embedding
4. **telemetry.py**: Request logging and statistics
5. **evaluate.py**: Automated evaluation script

### RAG Pipeline
1. **Chunking**: Split notes into 300-word chunks with 50-word overlap
2. **Embedding**: Generate embeddings using Gemini's text-embedding-004
3. **Retrieval**: Find the top-5 relevant chunks if total chunks are over 8.
4. **Generation**: Pass retrieved context to Gemini for quiz generation

## Configuration

### Environment Variables (.env)
- `GEMINI_API_KEY`: Your Gemini API key

### Security Settings (app.py)
- `MAX_INPUT_LENGTH`: Maximum input length (default: 50000 characters)
- `INJECTION_PATTERNS`: Regex patterns for prompt injection detection

### RAG Settings (rag_engine.py)
- `chunk_size`: Size of text chunks (default: 300 words)
- `overlap`: Overlap between chunks (default: 50 words)
- `top_k`: Number of chunks to retrieve (default: 3)
- `min_chunks`: Number of chunks before RAG is utilized (default: 8)


## Telemetry

All requests are logged to `telemetry.jsonl` with:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "pathway": "RAG",
  "latency_ms": 2500,
  "tokens": 1543,
  "cost": 0.0015,
  "chunks_retrieved": 3,
  "error": null
}
```

View aggregated statistics:
```python
from telemetry import TelemetryLogger
logger = TelemetryLogger()
print(logger.get_stats())
```

## Evaluation

The evaluation suite includes 16 test cases covering:
- Basic concept extraction
- Technical definitions
- Multi-concept coverage
- Process-based questions
- Comparisons
- Historical context
- Mathematical concepts
- Scientific domains
- Programming concepts

Each test specifies:
- Input notes
- Number of questions to generate
- Expected patterns (keywords/concepts)
- Pass threshold (default: 50%)

### Running Tests
```bash
python evaluate.py
```

## Cost Estimation

Gemini 2.5 Flash pricing :
- Input: ~$0.30 per 1M tokens
- Output: ~$2.5 per 1M tokens

Typical quiz generation:
- Input tokens: ~1000-1500
- Output tokens: ~500-1000

## Maker

Guillermo Rebolledo 100865463