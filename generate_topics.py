import sys
import json
from shared_utils import validate_config, call_deepseek_api, save_to_json

def generate_topics_prompt(math_topic):
    return f"""
You are an expert math educator and curriculum designer. Given a class name (e.g., Algebra 1, Calculus 1, Linear Algebra), your task is to generate a **detailed, flat list** of all specific topics and subtopics typically covered in this course.

The class to analyze is: **{math_topic}**

### Instructions:

- Think deeply about every concept and skill taught in this class.
- Break down every main topic into **granular, specific subtopics or problem types**.
- The goal is to generate a flat, exhaustive list that could be used for generating individual math problems or flashcards.
- Include specific techniques, problem types, representations, and variations.
- List as many distinct items as possible.

### Example (for Algebra 1):

"Solving single-variable linear equations"  
"Graphing linear equations in slope-intercept form"  
"Solving absolute value equations"  
"Solving linear inequalities with one variable"  
"Graphing inequalities on a number line"  
"Factoring trinomials"  
"Solving quadratic equations by factoring"  
"Solving quadratic equations with the quadratic formula"  
"Completing the square"  
"Solving systems of equations by substitution"  
"Solving systems of equations by elimination"  
"Solving word problems involving systems of equations"  

### IMPORTANT:
Return your response as a well-formed JSON object with a single "topics" key containing an array of topic strings. Format example:
{{
  "topics": [
    "Topic 1",
    "Topic 2",
    "Topic 3"
  ]
}}

### Now begin:

List of detailed topics for: **{math_topic}**
"""

# Main function
def generate_math_topics():
    # Validate configuration
    math_topic = validate_config()
    print(f"Generating topic list for: {math_topic}...")
    
    try:
        # Make API call for topic list (expecting JSON)
        prompt = generate_topics_prompt(math_topic)
        response = call_deepseek_api(prompt, expect_json=True)
        
        # Parse JSON response
        try:
            topics_data = json.loads(response)
            if isinstance(topics_data, dict) and "topics" in topics_data:
                topics = topics_data["topics"]
                print(f"Retrieved {len(topics)} main topics for {math_topic}")
                
                # Create a JSON file with the topics
                filename = "topics.json"
                
                if save_to_json(topics_data, filename):
                    print(f"Successfully generated topic list for {math_topic}.")
                    print(f"Results saved to {filename}")
            else:
                print("Error: Invalid response format. Expected a JSON object with a 'topics' key.")
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            print(f"Raw response: {response}")
    
    except Exception as e:
        print(f"Error in main process: {str(e)}")
        sys.exit(1)

# Run the program
if __name__ == "__main__":
    generate_math_topics()
