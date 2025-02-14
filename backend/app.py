from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from typing import Dict, Any
import requests
import time

app = Flask(__name__)

CORS(app)

OLLAMA_API_BASE = "http://localhost:11434/api"
REQUEST_TIMEOUT = 300 

def check_ollama_service():
    """Check if Ollama service is running"""
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_ollama_completion(question: str) -> Dict[Any, Any]:
    """
    Create a completion using Ollama API
    """
    try:
        # First check if Ollama service is running
        if not check_ollama_service():
            raise Exception("Ollama service is not running. Please start it with 'ollama serve'")

        # Add explicit JSON formatting instruction
        system_message = """You are a graph generation assistant. You must generate a graph of thought in VALID JSON format.
        CRITICAL: Your response must be ONLY the JSON object, with no additional text, markdown, or explanations.
        
        Follow these rules strictly:
        1. Break down the main question into sub-questions when applicable
        2. Each sub-question and its solution should be a separate node
        3. Show the progression from sub-questions to final answer
        4. IMPORTANT: You must generate ALL required edges and clusters:
           - Every node must be connected to at least one other node
           - Every node must belong to a cluster
           - The edges array must contain connections between ALL sequential nodes
           - ALL three clusters (Main Question, Sub Questions, Final Answer) must be included

        The response must follow this exact structure and requirements:
        {
            "nodes": [
                {
                    "key": "node_0",
                    "label": "Main Question",
                    "tag": "Question",
                    "cluster": "0",
                    "x": 0,
                    "y": 45,
                    "sizenode": 30,
                    "thoughts": [
                        {
                            "question": "original_question",
                            "current": "",
                            "phase": 0
                        }
                    ]
                }
            ],
            "edges": [
                ["node_0", "node_1", "Break down question"],
                ["node_1", "node_2", "Continue analysis"],
                ["node_2", "node_final", "Draw conclusion"]
            ],
            "clusters": [
                {
                    "key": "0",
                    "color": "#00ffbc",
                    "clusterLabel": "Main Question"
                },
                {
                    "key": "1",
                    "color": "#ff004f",
                    "clusterLabel": "Sub Questions"
                },
                {
                    "key": "2",
                    "color": "#f9a11b",
                    "clusterLabel": "Final Answer"
                }
            ],
            "tags": [
                {
                    "key": "Question",
                    "image": "question.svg"
                },
                {
                    "key": "SubQuestion",
                    "image": "subquestion.svg"
                },
                {
                    "key": "Answer",
                    "image": "answer.svg"
                }
            ]
        }

        Critical requirements:
        1. ALL three clusters must be included in the response
        2. Edges must connect ALL nodes in sequence
        3. Each node must have a valid cluster assignment
        4. The edges array must contain ALL connections
        5. No node can be isolated (every node must have at least one connection)
        6. Generate appropriate edges for ALL node transitions
        7. Include ALL required fields in the response
        8. Verify that ALL nodes are properly connected before returning
        9. ALL cluster definitions must be present regardless of usage
        10. The tags array must always contain all three tag types

        Before returning the response, verify:
        1. All nodes are connected
        2. All three clusters are defined
        3. All edges are properly specified
        4. All tags are included
        5. JSON structure is valid"""

        # Create the prompt with explicit JSON instruction
        prompt = f"""
        <<SYS>>
        {system_message}
        <</SYS>>

        Generate a graph of thought for this question: {question}
        IMPORTANT: Return ONLY the JSON object. Do not include any other text or explanations.
        The response must be valid JSON that can be parsed by json.loads().
        """

        # Call Ollama API with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{OLLAMA_API_BASE}/generate",
                    json={
                        "model": "llama2",
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.7,
                        "top_p": 0.9
                    },
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    break
                    
                time.sleep(1)
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} timed out, retrying...")
                continue

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.text}")

        # Extract and parse JSON from the response with improved error handling
        try:
            response_text = response.json()['response'].strip()
            print(f"Raw response: {response_text}")  # Debug log
            
            # Find the first '{' and last '}'
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start == -1 or end <= start:
                raise ValueError("No valid JSON object found in response")
                
            json_str = response_text[start:end]
            
            # Remove any potential markdown code block markers
            json_str = json_str.replace('```json', '').replace('```', '').strip()
            
            # Try to parse the JSON
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error at position {e.pos}: {e.msg}")
                print(f"Problematic JSON string: {json_str}")
                raise ValueError(f"Invalid JSON format: {str(e)}")

            # Validate required structure
            required_keys = ['nodes', 'edges', 'clusters', 'tags']
            if not all(key in result for key in required_keys):
                missing_keys = [key for key in required_keys if key not in result]
                raise ValueError(f"Missing required keys in JSON: {missing_keys}")

            return result

        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            print(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            print(f"Error processing response: {str(e)}")
            print(f"Response text: {response_text}")
            raise ValueError(f"Error processing response: {str(e)}")

    except requests.exceptions.Timeout:
        raise Exception("Request to Ollama timed out. Please check if the model is loaded correctly.")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to Ollama service. Please make sure 'ollama serve' is running.")
    except Exception as e:
        raise Exception(f"Error in Ollama completion: {str(e)}")

def validate_response(response: Dict[Any, Any]) -> None:
    """
    Validate the response structure
    """
    required_keys = ['nodes', 'edges', 'clusters', 'tags']
    if not all(key in response for key in required_keys):
        raise ValueError("Response missing required keys")

    # Validate nodes structure
    for node in response['nodes']:
        required_node_keys = ['key', 'label', 'tag', 'cluster', 'thoughts']
        if not all(key in node for key in required_node_keys):
            raise ValueError("Invalid node structure")

    # Validate edges structure and add default label if missing
    for i, edge in enumerate(response['edges']):
        if isinstance(edge, list):
            if len(edge) == 2:
                # Add default empty label if missing
                response['edges'][i] = [edge[0], edge[1], ""]
            elif not len(edge) == 3:
                raise ValueError("Invalid edge structure")
        else:
            raise ValueError("Edge must be a list")

    # Validate clusters structure
    for cluster in response['clusters']:
        required_cluster_keys = ['key', 'color', 'clusterLabel']
        if not all(key in cluster for key in required_cluster_keys):
            raise ValueError("Invalid cluster structure")

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        print("Received request") # Debug log
        data = request.json
        question = data.get('question')
        
        if not question:
            print("No question provided") # Debug log
            return jsonify({'error': 'No question provided'}), 400

        print(f"Processing question: {question}") # Debug log
        # Generate response using Ollama
        response = create_ollama_completion(question)
        
        print("Validating response") # Debug log
        # Validate response format
        validate_response(response)
        
        print("Sending response") # Debug log
        return jsonify(response)

    except ValueError as ve:
        print(f"Validation error: {str(ve)}") # Debug log
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        print(f"Server error: {str(e)}") # Debug log
        return jsonify({'error': f"Server error: {str(e)}"}), 500

# Add a test endpoint
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'Backend server is running'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  