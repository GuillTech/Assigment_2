import json
from datetime import datetime
import os

class TelemetryLogger:
    def __init__(self, log_file='telemetry.jsonl'):
        self.log_file = log_file
    
    def log_request(self, pathway, latency_ms, tokens, cost, chunks_retrieved=0, error=None):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'pathway': pathway,
            'latency_ms': latency_ms,
            'tokens': tokens,
            'cost': cost,
            'chunks_retrieved': chunks_retrieved,
            'error': error
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_stats(self):
        if not os.path.exists(self.log_file):
            return {}
        
        total_requests = 0
        total_latency = 0
        total_cost = 0
        total_tokens = 0
        pathways = {}
        
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                total_requests += 1
                total_latency += entry['latency_ms']
                total_cost += entry['cost']
                total_tokens += entry['tokens']
                
                pathway = entry['pathway']
                pathways[pathway] = pathways.get(pathway, 0) + 1
        
        return {
            'total_requests': total_requests,
            'avg_latency_ms': total_latency / total_requests if total_requests > 0 else 0,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'pathways': pathways
        }
