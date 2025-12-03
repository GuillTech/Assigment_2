# AI Quiz Generator with RAG - Technical Note

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (Flask Web App + HTML)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (app.py)                       │
│  • Input validation (50K char limit)                         │
│  • Prompt injection detection                                │
│  • Request routing & error handling                          │
└─────────┬───────────────────────────┬───────────────────────┘
          │                           │
          ▼                           ▼
┌──────────────────────┐    ┌─────────────────────────────────┐
│   RAG Engine         │    │    Telemetry Logger             │
│  (rag_engine.py)     │    │    (telemetry.py)               │
│                      │    │                                 │
│  1. Text Chunking    │    │  • Request logging              │
│     (300w, 50w lap)  │    │  • Cost tracking                │
│  2. Embedding        │    │  • Performance metrics          │
│     (text-embed-004) │    │  • JSONL output                 │
│  3. Vector Search    │    └─────────────────────────────────┘
│     (Cosine Sim)     │
│  4. Top-k Retrieval  │
│     (5 chunks)       │
└─────────┬────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM Client (llm_client.py)                      │
│                                                               │
│  • Gemini 2.5 Flash API                                      │
│  • System prompt with safety rules                           │
│  • JSON response parsing (3-tier fallback)                   │
│  • Token counting & cost calculation                         │
└─────────────────────────────────────────────────────────────┘
```

## Guardrails

### Input Validation
- **Length Limit**: 50,000 characters maximum
- **Type Checking**: Ensures input is a valid string

### Prompt Injection Protection
Regex patterns detect and block:
- "ignore previous/all instructions"
- "disregard ... instructions"
- "you are now ..."
- "system:" delimiter attempts
- Special tokens (e.g., `<|...|>`)

### LLM Safety Rules (System Prompt)
- No inappropriate, offensive, or harmful content
- No illegal activity questions
- No personal information (PII)
- Refuse instruction override attempts
- Stay focused on educational content only

### Error Handling
- **3-Tier JSON Parsing**:
  1. Direct JSON parsing
  2. Markdown code block extraction + parsing
  3. Regex-based field extraction as fallback
- **Graceful Degradation**: Returns error messages instead of crashes
- **API Fallback**: Simple hash-based embeddings if API fails

## Evaluation 

### Test Suite Design
- **16 diverse test cases** covering:
  - Basic concept extraction (ML, neural networks)
  - Technical definitions and processes
  - Science and Mathematics coveragage (biology, physics, economics, psychology)
  - Different question types (comparison, historical, mathematical)

### Evaluation Metrics
- **Pattern Matching**: Checks for expected keywords/concepts in generated questions
- **Pass Threshold**: 50% keyword match required
- **Score Calculation**: `matches / total_expected_patterns`

### Automated Testing
- Script: `evaluate.py`
- Runs all test cases automatically
- Generates structured results in `evaluation_results.json`
- **Current Performance**: 93.75% pass rate (15/16 tests passed)


## Known Limitations

### 1. Rate Limiting
- Free tier has strict limits

### 2. Consistency issues
- Occasional missing questions
- Strict json format that llm can ocasionally mess up.

### 3. Evaluation Coverage
- Pattern matching is keyword-based
- May miss correct but differently worded answers

### 4. No Conversation Memory
- Cannot refine questions based on user feedback