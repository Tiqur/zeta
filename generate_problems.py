import sys
import json
from shared_utils import validate_config, call_deepseek_api, save_to_json, load_from_json

def create_problem_generation_prompt(prompt_data, num_problems=3):
    """
    Create a prompt for generating multiple math problems
    based on the provided prompt data.
    """
    # Extract data from prompt object
    prompt_text = prompt_data["prompt"]
    topic = prompt_data["topic"]
    tags = prompt_data.get("tags", [])
    
    # Create a comma-separated string of tags
    tags_str = ', '.join([f'"{tag}"' for tag in tags])
    
    
    return f"""
Generate {num_problems} different math problems based on the following input:
- `"prompt"`: {prompt_text}
- `"type"`: "{prompt_data["title"]}"
- `"topic"`: "{topic}"
- `"tags"`: [{tags_str}]

Respond only with a valid JSON object with a "problems" key containing an array of {num_problems} problem objects. Each problem object should have:
- `"problem"`: The question, written in LaTeX and suitable for the front of an Anki card. Use `$$...$$` to wrap display math.
- `"answer"`: The final, concise answer, also using LaTeX with `$$...$$`.
- `"solution"`: A clear, step-by-step explanation of how to solve the problem, fully formatted with LaTeX (`$$...$$` where appropriate).

### Example response for 2 problems (Integration by Substitution):
{{
  "problems": [
    {{
      "problem": "Evaluate the indefinite integral $$\\int \\cos(3x) \\sin^2(3x) dx$$.",
      "answer": "$$\\frac{{-\\cos^3(3x)}}{{9}} + C$$",
      "solution": "Let's use substitution to solve this integral.\\n\\nFirst, we notice that this involves powers of sine and cosine. Let's set $u = \\sin(3x)$.\\n\\nThen $du = 3\\cos(3x)dx$ or $dx = \\frac{{du}}{{3\\cos(3x)}}$.\\n\\nSubstituting this into our integral:\\n\\n$$\\int \\cos(3x) \\sin^2(3x) dx = \\int \\sin^2(3x) \\cdot \\cos(3x) dx$$\\n\\nWith our substitution: $u = \\sin(3x)$ and $dx = \\frac{{du}}{{3\\cos(3x)}}$, the integral becomes:\\n\\n$$\\int u^2 \\cdot \\cos(3x) \\cdot \\frac{{du}}{{3\\cos(3x)}} = \\frac{{1}}{{3}}\\int u^2 du$$\\n\\nNow we can easily integrate: $\\frac{{1}}{{3}}\\int u^2 du = \\frac{{1}}{{3}} \\cdot \\frac{{u^3}}{{3}} + C = \\frac{{u^3}}{{9}} + C$\\n\\nSubstituting back $u = \\sin(3x)$, we get:\\n\\n$$\\frac{{\\sin^3(3x)}}{{9}} + C$$"
    }},
    {{
      "problem": "Evaluate $$\\int x e^{{x^2}} dx$$.",
      "answer": "$$\\frac{{1}}{{2}} e^{{x^2}} + C$$",
      "solution": "To solve this integral, we'll use substitution.\\n\\nLet's set $u = x^2$, which means $du = 2x\\,dx$ or $x\\,dx = \\frac{{du}}{{2}}$.\\n\\nSubstituting into our integral:\\n\\n$$\\int x e^{{x^2}} dx = \\int e^u \\cdot \\frac{{du}}{{2}} = \\frac{{1}}{{2}}\\int e^u du$$\\n\\nNow we can easily integrate:\\n\\n$$\\frac{{1}}{{2}}\\int e^u du = \\frac{{1}}{{2}} e^u + C$$\\n\\nSubstituting back $u = x^2$:\\n\\n$$\\frac{{1}}{{2}} e^{{x^2}} + C$$"
    }}
  ]
}}

**Only output a valid JSON object. Do not include any explanatory text outside the JSON.**
"""

def generate_problems():
    """Generate math problems for all prompts and save them to problems.json"""
    # Number of problems to generate per prompt
    num_problems = 3
    
    # Validate configuration
    math_topic = validate_config()
    
    try:
        # Load prompts
        prompts_file = "prompts.json"
        prompts = load_from_json(prompts_file)
        
        if not prompts or not isinstance(prompts, list):
            print(f"ERROR: Prompts file not found or invalid format: {prompts_file}")
            print("Please run generate_prompts.py first to create the prompts file.")
            sys.exit(1)
        
        print(f"Loaded {len(prompts)} problem types from {prompts_file}")
        print(f"Generating {num_problems} problems for each type...")
        
        # Generate problems for each prompt
        all_problems = []
        
        for i, prompt_data in enumerate(prompts, 1):
            prompt_title = prompt_data["title"]
            print(f"Processing prompt {i}/{len(prompts)}: {prompt_title}...")
            
            # Create the problem generation prompt
            prompt = create_problem_generation_prompt(prompt_data, num_problems)
            
            # Make API call to generate the problems (expecting JSON)
            response = call_deepseek_api(prompt, expect_json=True)
            
            try:
                # Parse JSON response
                try:
                    response_data = json.loads(response)
                except:
                    # If already parsed by API call
                    response_data = response
                
                # Check for expected format
                if isinstance(response_data, dict) and "problems" in response_data:
                    problems_batch = response_data["problems"]
                    
                    if isinstance(problems_batch, list):
                        for problem in problems_batch:
                            if "problem" in problem and "answer" in problem and "solution" in problem:
                                # Keep only the required fields
                                clean_problem = {
                                    "problem": problem["problem"],
                                    "answer": problem["answer"],
                                    "solution": problem["solution"]
                                }
                                all_problems.append(clean_problem)
                        
                        print(f"  Successfully generated {len(problems_batch)} problems for: {prompt_title}")
                    else:
                        print(f"  Error: 'problems' is not a list for {prompt_title}")
                else:
                    print(f"  Error: Invalid response format for {prompt_title}. Expected a JSON object with a 'problems' key.")
                    if isinstance(response_data, dict):
                        print(f"  Response keys: {list(response_data.keys())}")
            
            except Exception as e:
                print(f"  Error processing problems for {prompt_title}: {str(e)}")
                print(f"  Raw response: {response[:100]}...")  # Show first 100 chars of response
        
        # Save all generated problems to a file
        problems_filename = "problems.json"
        save_to_json(all_problems, problems_filename)
        print(f"\nSuccessfully generated {len(all_problems)} problems in total.")
        print(f"Results saved to {problems_filename}")
        
    except Exception as e:
        print(f"Error in main process: {str(e)}")
        sys.exit(1)

# Main entry point
if __name__ == "__main__":
    generate_problems()
