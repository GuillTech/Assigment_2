from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
from datetime import datetime
from llm_client import GeminiClient
from rag_engine import RAGEngine
from telemetry import TelemetryLogger
import re

app = Flask(__name__)
CORS(app)

# Initialize components
gemini = GeminiClient(api_key=os.getenv('GEMINI_API_KEY'))
rag = RAGEngine(gemini)
telemetry = TelemetryLogger()

# Security configurations
MAX_INPUT_LENGTH = 50000  # characters
INJECTION_PATTERNS = [
    r'ignore\s+(previous|above|all)\s+instructions',
    r'disregard\s+.*\s+instructions',
    r'you\s+are\s+now',
    r'new\s+instructions',
    r'system\s*:\s*',
    r'<\|.*\|>',
]

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Quiz Generator</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }
        .card { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
        textarea { width: 100%; height: 300px; padding: 15px; border: 2px solid #e0e0e0; border-radius: 8px; font-family: monospace; font-size: 14px; }
        button { padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: 600; }
        button:hover { background: #5568d3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .question { margin-bottom: 30px; padding-bottom: 30px; border-bottom: 1px solid #e0e0e0; }
        .hint { background: #fff3cd; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 3px solid #ffc107; }
        .answer { background: #e8f5e9; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 3px solid #4caf50; }
        .rubric { background: #f3e5f5; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 3px solid #9c27b0; }
        .loading { text-align: center; padding: 50px; }
        .spinner { border: 4px solid #f0f0f0; border-top: 4px solid #667eea; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .telemetry { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .metric { display: flex; align-items: center; gap: 10px; }
        .error { background: #fee; border: 1px solid #fcc; color: #c33; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .info { background: #e3f2fd; padding: 12px; border-radius: 6px; margin: 10px 0; border-left: 3px solid #2196f3; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Quiz Generator</h1>
            <p>Generate quiz questions from your notes using RAG-powered AI</p>
        </div>
        <div id="app">
            <div class="card">
                <h2>Upload Your Notes</h2>
                <textarea id="notes" placeholder="Paste your study notes here..."></textarea>
                <br><br>
                <label><input type="checkbox" id="include-hints" checked> Include hints</label>
                <label><input type="checkbox" id="include-rubric" checked> Include rubric</label>
                <br><br>
                <button onclick="generateQuiz()">Generate Quiz</button>
            </div>
        </div>
    </div>
    <script>
        async function generateQuiz() {
            const notes = document.getElementById('notes').value;
            const includeHints = document.getElementById('include-hints').checked;
            const includeRubric = document.getElementById('include-rubric').checked;
            
            if (!notes.trim()) {
                alert('Please enter your notes first');
                return;
            }
            
            document.getElementById('app').innerHTML = '<div class="card loading"><div class="spinner"></div><h3>Generating Quiz...</h3><p>Processing your notes with RAG...</p></div>';
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes, include_hints: includeHints, include_rubric: includeRubric })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('app').innerHTML = `<div class="card"><div class="error">${data.error}</div></div>`;
                    return;
                }
                
                let html = '<div class="card"><div class="telemetry">';
                html += `<div class="metric">⏱Latency: ${data.telemetry.latency_ms}ms</div>`;
                html += `<div class="metric">Input Tokens: ${data.telemetry.input_tokens}</div>`;
                html += `<div class="metric">Output Tokens: ${data.telemetry.output_tokens}</div>`;
                html += `<div class="metric">Total Tokens: ${data.telemetry.total_tokens}</div>`;
                html += `<div class="metric">Input Cost: $${data.telemetry.input_cost.toFixed(6)}</div>`;
                html += `<div class="metric">Output Cost: $${data.telemetry.output_cost.toFixed(6)}</div>`;
                html += `<div class="metric">Total Cost: $${data.telemetry.total_cost.toFixed(6)}</div>`;
                html += `<div class="metric">Total Chunks: ${data.telemetry.total_chunks}</div>`;
                html += `<div class="metric">Retrieved: ${data.telemetry.chunks_retrieved}</div>`;
                html += '</div>';
                
                if (data.telemetry.rag_strategy) {
                    html += `<div class="info">Strategy: ${data.telemetry.rag_strategy}</div>`;
                }
                
                html += '</div>';
                
                html += '<div class="card"><h2>Generated Quiz</h2>';
                data.questions.forEach((q, i) => {
                    html += `<div class="question">`;
                    html += `<h3>Question ${i+1}</h3>`;
                    html += `<p><strong>${q.question}</strong></p>`;
                    if (q.hint) html += `<div class="hint">Hint: ${q.hint}</div>`;
                    if (q.answer) html += `<details><summary>Show Answer</summary><div class="answer">${q.answer}</div></details>`;
                    if (q.rubric) html += `<details><summary>Show Rubric</summary><div class="rubric">${q.rubric}</div></details>`;
                    html += '</div>';
                });
                html += '<button onclick="location.reload()">Generate Another Quiz</button>';
                html += '</div>';
                
                document.getElementById('app').innerHTML = html;
            } catch (error) {
                document.getElementById('app').innerHTML = `<div class="card"><div class="error">Error: ${error.message}</div></div>`;
            }
        }
    </script>
</body>
</html>
'''

def check_prompt_injection(text):
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def validate_input(notes):
    if not notes or not isinstance(notes, str):
        return False, "Notes must be a non-empty string"
    
    if len(notes) > MAX_INPUT_LENGTH:
        return False, f"Notes exceed maximum length of {MAX_INPUT_LENGTH} characters"
    
    if check_prompt_injection(notes):
        return False, "Potential prompt injection detected. Please rephrase your input."
    
    return True, None

def extract_key_topics(notes: str, max_topics: int = 5) -> list[str]:
    words = notes.lower().split()
    
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
    word_freq = {}
    
    for word in words:
        clean_word = word.strip('.,!?;:')
        if clean_word and len(clean_word) > 3 and clean_word not in stop_words:
            word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_topics]]

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/generate', methods=['POST'])
def generate_quiz():
    start_time = datetime.now()
    
    try:
        data = request.json
        notes = data.get('notes', '')
        include_hints = data.get('include_hints', True)
        include_rubric = data.get('include_rubric', True)
        num_questions = data.get('num_questions', 4)
        
        is_valid, error_msg = validate_input(notes)
        if not is_valid:
            telemetry.log_request(
                pathway='validation_failed',
                latency_ms=0,
                tokens=0,
                cost=0,
                error=error_msg
            )
            return jsonify({'error': error_msg}), 400
        
        rag.index_documents([notes])
        total_chunks = rag.get_chunk_count()
        
        if rag.should_use_rag():
            key_topics = extract_key_topics(notes)
            query = f"Key concepts related to: {', '.join(key_topics)}"
            retrieved_chunks = rag.retrieve(query, top_k=5)
            context = "\n\n".join(retrieved_chunks)
            strategy = f"RAG retrieval (5 chunks from {total_chunks} total)"
        else:
            retrieved_chunks = rag.retrieve_all_chunks()
            context = "\n\n".join(retrieved_chunks)
            strategy = f"Full content ({total_chunks} chunks)"
        
        # Generate quiz
        result = gemini.generate_quiz(
            context=context,
            num_questions=num_questions,
            include_hints=include_hints,
            include_rubric=include_rubric
        )
        
        # Calculate metrics
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Log telemetry
        telemetry.log_request(
            pathway='RAG',
            latency_ms=latency_ms,
            tokens=result.get('total_tokens', 0),
            cost=result.get('total_cost', 0),
            chunks_retrieved=len(retrieved_chunks)
        )
        
        return jsonify({
            'questions': result['questions'],
            'telemetry': {
                'latency_ms': latency_ms,
                'input_tokens': result.get('input_tokens', 0),
                'output_tokens': result.get('output_tokens', 0),
                'total_tokens': result.get('total_tokens', 0),
                'input_cost': result.get('input_cost', 0),
                'output_cost': result.get('output_cost', 0),
                'total_cost': result.get('total_cost', 0),
                'total_chunks': total_chunks,
                'chunks_retrieved': len(retrieved_chunks),
                'rag_strategy': strategy,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        error_msg = f"Error generating quiz: {str(e)}"
        telemetry.log_request(
            pathway='error',
            latency_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            tokens=0,
            cost=0,
            error=error_msg
        )
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)