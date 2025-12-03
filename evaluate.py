import json
import os
from llm_client import GeminiClient
from rag_engine import RAGEngine

def load_tests(test_file='tests.json'):
    """Load test cases"""
    with open(test_file, 'r') as f:
        return json.load(f)

def evaluate_response(generated, expected_patterns):
    """Evaluate if generated response matches expected patterns"""
    generated_lower = generated.lower()
    
    matches = 0
    for pattern in expected_patterns:
        if isinstance(pattern, str):
            if pattern.lower() in generated_lower:
                matches += 1
        elif isinstance(pattern, dict):
            # Check for presence of required keys/concepts
            if all(k.lower() in generated_lower for k in pattern.get('required', [])):
                matches += 1
    
    return matches / len(expected_patterns) if expected_patterns else 0

def run_evaluation():
    """Run evaluation on test cases"""
    print("=" * 60)
    print("QUIZ GENERATOR EVALUATION")
    print("=" * 60)
    
    # Initialize components
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        return
    
    gemini = GeminiClient(api_key=api_key)
    rag = RAGEngine(gemini)
    
    # Load tests
    tests = load_tests()
    
    passed = 0
    failed = 0
    results = []
    
    for i, test in enumerate(tests['test_cases'], 1):
        print(f"\nTest {i}/{len(tests['test_cases'])}: {test['name']}")
        print("-" * 60)
        
        try:
            # Index documents
            rag.index_documents([test['input_notes']])
            
            # Retrieve context
            retrieved = rag.retrieve("generate quiz questions", top_k=2)
            context = "\n".join(retrieved)
            
            # Generate quiz
            result = gemini.generate_quiz(
                context=context,
                num_questions=test.get('num_questions', 2),
                include_hints=True,
                include_rubric=True
            )
            
            # Evaluate
            generated_text = json.dumps(result['questions'])
            score = evaluate_response(generated_text, test['expected_patterns'])
            
            if score >= test.get('pass_threshold', 0.6):
                passed += 1
                status = "✓ PASS"
            else:
                failed += 1
                status = "✗ FAIL"
            
            print(f"Status: {status}")
            print(f"Score: {score:.2%}")
            print(f"Questions generated: {len(result['questions'])}")
            
            results.append({
                'test': test['name'],
                'status': 'pass' if score >= test.get('pass_threshold', 0.6) else 'fail',
                'score': score,
                'questions_generated': len(result['questions'])
            })
            
        except Exception as e:
            failed += 1
            print(f"Status: ✗ FAIL (Error: {str(e)})")
            results.append({
                'test': test['name'],
                'status': 'fail',
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed} ({passed/(passed+failed)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/(passed+failed)*100:.1f}%)")
    print(f"Pass rate: {passed/(passed+failed)*100:.1f}%")
    
    # Save results
    with open('evaluation_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total': passed + failed,
                'passed': passed,
                'failed': failed,
                'pass_rate': passed/(passed+failed) if (passed+failed) > 0 else 0
            },
            'results': results
        }, f, indent=2)
    
    print("\nDetailed results saved to evaluation_results.json")

if __name__ == '__main__':
    run_evaluation()
