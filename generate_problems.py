import sys
import json
import sqlite3
from shared_utils import validate_config, call_deepseek_api, load_from_json

def setup_database():
    """Create SQLite database tables if they don't exist"""
    conn = sqlite3.connect('problems.db')
    cursor = conn.cursor()
    
    # Create problems table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem TEXT NOT NULL,
        answer TEXT NOT NULL,
        solution TEXT NOT NULL,
        prompt_title TEXT NOT NULL
    )
    ''')
    
    # Create tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # Create problem_tags junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS problem_tags (
        problem_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (problem_id, tag_id),
        FOREIGN KEY (problem_id) REFERENCES problems (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id)
    )
    ''')
    
    conn.commit()
    return conn

def get_recent_problems_by_type(conn, prompt_title, num_recent=10):
    """Get a list of recently added problem statements of the same type to avoid duplication"""
    cursor = conn.cursor()
    cursor.execute('''
    SELECT problem FROM problems 
    WHERE prompt_title = ? 
    ORDER BY id DESC LIMIT ?
    ''', (prompt_title, num_recent))
    return [row[0] for row in cursor.fetchall()]

def save_problem_to_db(conn, problem, prompt_data):
    """Save a problem and its tags to the database"""
    cursor = conn.cursor()
    
    # Insert the problem
    cursor.execute('''
    INSERT INTO problems (problem, answer, solution, prompt_title)
    VALUES (?, ?, ?, ?)
    ''', (problem["problem"], problem["answer"], problem["solution"], prompt_data["title"]))
    
    problem_id = cursor.lastrowid
    
    # Insert or get tags
    for tag in prompt_data.get("tags", []):
        # Try to insert the tag, ignore if it already exists
        cursor.execute('''
        INSERT OR IGNORE INTO tags (name) VALUES (?)
        ''', (tag,))
        
        # Get the tag ID
        cursor.execute('SELECT id FROM tags WHERE name = ?', (tag,))
        tag_id = cursor.fetchone()[0]
        
        # Link the problem to the tag
        cursor.execute('''
        INSERT INTO problem_tags (problem_id, tag_id) VALUES (?, ?)
        ''', (problem_id, tag_id))
    
    conn.commit()
    return problem_id

def create_problem_generation_prompt(prompt_data, num_problems=3, recent_problems=None):
    """
    Create a prompt for generating multiple math problems
    based on the provided prompt data, with duplication prevention.
    """
    # Extract data from prompt object
    prompt_text = prompt_data["prompt"]
    topic = prompt_data["topic"]
    tags = prompt_data.get("tags", [])
    
    # Create a comma-separated string of tags
    tags_str = ', '.join([f'"{tag}"' for tag in tags])
    
    # Add duplication prevention section if we have recent problems
    duplication_prevention = ""
    if recent_problems and len(recent_problems) > 0:
        duplication_prevention = f"IMPORTANT: Below are recently created problems of the same type ('{prompt_data['title']}'). Make sure your new problems are significantly different:\n\n"
        for i, prob in enumerate(recent_problems, 1):
            duplication_prevention += f"Recent Problem {i}: {prob}\n\n"
    
    return f"""
Generate {num_problems} different math problems based on the following input:
- `"prompt"`: {prompt_text}
- `"type"`: "{prompt_data["title"]}"
- `"topic"`: "{topic}"
- `"tags"`: [{tags_str}]

{duplication_prevention}

Respond with ONLY a valid JSON object with a "problems" key containing an array of {num_problems} problem objects. Each problem object should have:
- `"problem"`: The question, written in LaTeX and suitable for the front of an Anki card. Use `$$...$$` to wrap display math.
- `"answer"`: The final, concise answer, also using LaTeX with `$$...$$`.
- `"solution"`: A clear, step-by-step explanation of how to solve the problem, fully formatted with LaTeX (`$$...$$` where appropriate).

The response MUST be valid JSON with NO explanatory text outside of the JSON object.

Example JSON structure:
{{
  "problems": [
    {{
      "problem": "Question text here",
      "answer": "Answer text here",
      "solution": "Solution text here"
    }},
    ...
  ]
}}

DO NOT include any text before or after the JSON object. The response should start with {{ and end with }}.
"""

def generate_problems():
    """Generate math problems for all prompts and save them to SQLite database"""
    # Number of problems to generate per prompt
    num_problems = 3
    num_recent_for_dedup = 15  # Number of recent problems to check for duplicates
    
    # Validate configuration
    math_topic = validate_config()
    
    try:
        # Set up the database
        conn = setup_database()
        
        # Load prompts
        prompts_file = "prompts.json"
        prompts = load_from_json(prompts_file)
        
        if not prompts or not isinstance(prompts, list):
            print(f"ERROR: Prompts file not found or invalid format: {prompts_file}")
            print("Please run generate_prompts.py first to create the prompts file.")
            conn.close()
            sys.exit(1)
        
        print(f"Loaded {len(prompts)} problem types from {prompts_file}")
        print(f"Generating {num_problems} problems for each type...")
        
        # Generate problems for each prompt
        total_problems_generated = 0
        
        for i, prompt_data in enumerate(prompts, 1):
            prompt_title = prompt_data["title"]
            print(f"Processing prompt {i}/{len(prompts)}: {prompt_title}...")
            
            # Get recent problems of the same type to prevent duplication
            recent_problems = get_recent_problems_by_type(conn, prompt_title, num_recent_for_dedup)
            if recent_problems:
                print(f"  Found {len(recent_problems)} existing problems of this type for duplication prevention")
            
            # Create the problem generation prompt with duplication prevention
            prompt = create_problem_generation_prompt(prompt_data, num_problems, recent_problems)
            
            # Make API call to generate the problems (expecting JSON)
            response = call_deepseek_api(prompt, expect_json=True)
            
            try:
                # Try to parse the response as JSON
                try:
                    # If response is already a dict (pre-parsed by API call)
                    if isinstance(response, dict):
                        response_data = response
                    else:
                        # Parse as JSON string
                        response_data = json.loads(response)
                except json.JSONDecodeError as e:
                    print(f"  JSON parsing error: {str(e)}")
                    print(f"  Raw response: {response[:200]}...")  # Show first 200 chars of response
                    continue
                
                # Check for expected format
                if isinstance(response_data, dict) and "problems" in response_data:
                    problems_batch = response_data["problems"]
                    
                    if isinstance(problems_batch, list):
                        problems_added = 0
                        
                        for problem in problems_batch:
                            if "problem" in problem and "answer" in problem and "solution" in problem:
                                # Keep only the required fields
                                clean_problem = {
                                    "problem": problem["problem"],
                                    "answer": problem["answer"],
                                    "solution": problem["solution"]
                                }
                                
                                # Save to database
                                problem_id = save_problem_to_db(conn, clean_problem, prompt_data)
                                problems_added += 1
                                total_problems_generated += 1
                        
                        print(f"  Successfully added {problems_added} problems for: {prompt_title}")
                    else:
                        print(f"  Error: 'problems' is not a list for {prompt_title}")
                else:
                    print(f"  Error: Invalid response format for {prompt_title}. Expected a JSON object with a 'problems' key.")
                    if isinstance(response_data, dict):
                        print(f"  Response keys: {list(response_data.keys())}")
                    print(f"  Raw response preview: {str(response)[:100]}...")
            
            except Exception as e:
                print(f"  Error processing problems for {prompt_title}: {str(e)}")
                print(f"  Raw response preview: {str(response)[:100]}...")  # Show first 100 chars of response
        
        # Print summary of results
        print(f"\nSuccessfully generated {total_problems_generated} problems in total.")
        print(f"Results saved to problems.db")
        
        # Close the database connection
        conn.close()
        
    except Exception as e:
        print(f"Error in main process: {str(e)}")
        sys.exit(1)

# Main entry point
if __name__ == "__main__":
    generate_problems()
