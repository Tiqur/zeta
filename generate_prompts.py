import sys
import json
import re
from shared_utils import validate_config, call_deepseek_api, save_to_json, load_from_json

# Function to create a prompt for generating subtopics and problem prompts
def create_topic_breakdown_prompt(topic_title, class_name):
    # Create a snake_case ID from the topic title
    topic_id = re.sub(r'[^a-zA-Z0-9\s]', '', topic_title).lower().replace(' ', '_')
    
    return f"""
You are an expert math content creator with deep reasoning capabilities. Given a topic from {class_name}, your task is to generate a comprehensive list of problem subtypes with associated problem-generation prompts.

### Topic to analyze: {topic_title}

### Instructions:

1. **Reflect** on this topic and identify various **problem types** and **subtypes** within {topic_title}.
2. For each problem type/subtype, create a **problem-generation prompt** that can be used to generate specific math problems.
3. **Output format**:
   - For each problem type, output a **JSON object** containing:
     - `"id"`: a unique snake_case identifier (start with "{topic_id}_")
     - `"title"`: a human-readable title (capitalized)
     - `"topic"`: "{topic_title}"
     - `"tags"`: an array of tags that describe this problem type
     - `"prompt"`: a **problem-generation prompt** for that type. This should be specific enough to generate good practice problems.

### IMPORTANT:
Return your response as a well-formed JSON object with a single "problem_types" key containing an array of problem type objects.

### Example format:
{{
  "problem_types": [
    {{
      "id": "linear_equations_single_variable",
      "title": "Linear Equations (Single Variable)",
      "topic": "Algebra 1",
      "tags": ["linear equations", "one variable", "solving"],
      "prompt": "Generate a problem that involves solving a linear equation with one variable. The equation should include integers or simple fractions, and the solution should be a single value."
    }},
    {{
      "id": "linear_equations_multi_variable",
      "title": "Linear Equations (Multi-variable)",
      "topic": "Algebra 1",
      "tags": ["linear equations", "two variables", "solving"],
      "prompt": "Generate a problem that involves solving a system of linear equations with two variables. The equations should be solvable using either substitution or elimination methods."
    }},
    {{
      "id": "factoring_quadratic_trinomial",
      "title": "Factoring Quadratic Trinomials",
      "topic": "Algebra 1",
      "tags": ["factoring", "quadratic equations", "polynomials"],
      "prompt": "Generate a problem where a quadratic trinomial needs to be factored. The equation should have integer coefficients and factor into two binomials."
    }},
    {{
      "id": "systems_of_equations_substitution_method",
      "title": "Solving Systems of Equations (Substitution Method)",
      "topic": "Algebra 1",
      "tags": ["systems of equations", "substitution", "solving"],
      "prompt": "Generate a problem that requires solving a system of linear equations using the substitution method. The equations should be simple and solvable with integers."
    }}
  ]
}}

Do not nest problem types within each other; provide a flat list of all problem types/subtypes.
"""

# Main function
def generate_topic_breakdowns():
    # Validate configuration
    math_topic = validate_config()
    print(f"Processing topic breakdowns for: {math_topic}")
    
    try:
        # Load the topics file
        topics_file = "topics.json"
        topics_data = load_from_json(topics_file)
        
        if not topics_data or not isinstance(topics_data, dict) or "topics" not in topics_data:
            print(f"ERROR: Topics file not found or invalid format: {topics_file}")
            print("Please run generate_topics.py first to create the topics file.")
            sys.exit(1)
        
        topics = topics_data["topics"]
        print(f"Loaded {len(topics)} topics from {topics_file}")
        
        # Create a list to store all prompts
        all_prompts = []
        
        # Process each topic
        for i, topic_title in enumerate(topics, 1):
            topic_id = re.sub(r'[^a-zA-Z0-9\s]', '', topic_title).lower().replace(' ', '_')
            
            print(f"Processing topic {i}/{len(topics)}: {topic_title}...")
            
            # Create the prompt for this topic
            prompt = create_topic_breakdown_prompt(topic_title, math_topic)
            
            # Make API call for this topic (expecting JSON)
            response = call_deepseek_api(prompt, expect_json=True)
            
            try:
                # Parse JSON response
                try:
                    response_data = json.loads(response)
                except:
                    # If already parsed by API call
                    response_data = response
                
                # Check for expected format
                if isinstance(response_data, dict) and "problem_types" in response_data:
                    problem_types = response_data["problem_types"]
                    if isinstance(problem_types, list):
                        print(f"  Retrieved {len(problem_types)} problem types for {topic_title}")
                        
                        # Add to our master list
                        all_prompts.extend(problem_types)
                    else:
                        print(f"  Error: 'problem_types' is not a list for {topic_title}")
                else:
                    print(f"  Error: Invalid response format for {topic_title}. Expected a JSON object with a 'problem_types' key.")
                    if isinstance(response_data, dict):
                        print(f"  Response keys: {list(response_data.keys())}")
                
            except Exception as e:
                print(f"  Error processing response for {topic_title}: {str(e)}")
                print(f"  Raw response: {response[:100]}...")  # Show first 100 chars of response
        
        # Save all prompts to a single file
        prompts_filename = "prompts.json"
        save_to_json(all_prompts, prompts_filename)
        print(f"\nSuccessfully generated prompts for all topics.")
        print(f"All results saved to {prompts_filename}")
        
    except Exception as e:
        print(f"Error in main process: {str(e)}")
        sys.exit(1)

# Run the program
if __name__ == "__main__":
    generate_topic_breakdowns()
