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

4. **IMPORTANT**: Return your response as a well-formed JSON array of all problem types. Do not nest problem types within each other; provide a flat list of all problem types/subtypes.

For example, if discussing Linear Equations, don't just have a single entry for "solving linear equations" - break it down into multiple entries like "solving one-step linear equations", "solving two-step linear equations", etc., each with their own specific problem-generation prompt.

Please return your response as a well-formed JSON array and nothing else.
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
                # Parse the JSON response
                problem_types = response
                if not isinstance(problem_types, list):
                    print(f"  Warning: Expected list but got {type(problem_types)} for {topic_title}")
                    continue
                    
                print(f"  Retrieved {len(problem_types)} problem types for {topic_title}")
                
                # Add to our master list
                all_prompts.extend(problem_types)
                
            except Exception as e:
                print(f"  Error processing response for {topic_title}: {str(e)}")
        
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
