import sqlite3
import sys
import argparse

def connect_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect('problems.db')
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def list_problems(args):
    """List all problems with optional tag filtering"""
    conn = connect_db()
    cursor = conn.cursor()
    
    query = """
    SELECT p.id, p.problem, p.prompt_title, GROUP_CONCAT(t.name, ', ') as tags
    FROM problems p
    LEFT JOIN problem_tags pt ON p.id = pt.problem_id
    LEFT JOIN tags t ON pt.tag_id = t.id
    """
    
    params = []
    if args.tag:
        query += """
        WHERE p.id IN (
            SELECT problem_id FROM problem_tags 
            JOIN tags ON tags.id = problem_tags.tag_id 
            WHERE tags.name = ?
        )
        """
        params.append(args.tag)
    
    query += "GROUP BY p.id"
    
    if args.limit:
        query += " LIMIT ?"
        params.append(args.limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    if not rows:
        print("No problems found.")
        return
    
    for row in rows:
        print(f"ID: {row['id']}")
        print(f"Problem Type: {row['prompt_title']}")
        print(f"Tags: {row['tags'] or 'None'}")
        print(f"Problem: {row['problem'][:100]}...")  # Truncate for readability
        print("-" * 40)
    
    print(f"Found {len(rows)} problems.")
    conn.close()

def view_problem(args):
    """View a specific problem by ID"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT p.*, GROUP_CONCAT(t.name, ', ') as tags
    FROM problems p
    LEFT JOIN problem_tags pt ON p.id = pt.problem_id
    LEFT JOIN tags t ON pt.tag_id = t.id
    WHERE p.id = ?
    GROUP BY p.id
    """, (args.id,))
    
    problem = cursor.fetchone()
    
    if not problem:
        print(f"No problem found with ID {args.id}")
        return
    
    print(f"ID: {problem['id']}")
    print(f"Problem Type: {problem['prompt_title']}")
    print(f"Tags: {problem['tags'] or 'None'}")
    print("\nPROBLEM:")
    print(problem['problem'])
    print("\nANSWER:")
    print(problem['answer'])
    
    if args.solution:
        print("\nSOLUTION:")
        print(problem['solution'])
    
    conn.close()

def list_tags(args):
    """List all tags and their count"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT t.name, COUNT(pt.problem_id) as problem_count
    FROM tags t
    LEFT JOIN problem_tags pt ON t.id = pt.tag_id
    GROUP BY t.name
    ORDER BY problem_count DESC
    """)
    
    tags = cursor.fetchall()
    
    if not tags:
        print("No tags found.")
        return
    
    print("Available tags:")
    for tag in tags:
        print(f"- {tag['name']} ({tag['problem_count']} problems)")
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Query math problems database")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List problems command
    list_parser = subparsers.add_parser('list', help='List problems')
    list_parser.add_argument('--tag', help='Filter by tag')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # View specific problem command
    view_parser = subparsers.add_parser('view', help='View a specific problem')
    view_parser.add_argument('id', type=int, help='Problem ID')
    view_parser.add_argument('--solution', action='store_true', help='Show solution')
    
    # List tags command
    tags_parser = subparsers.add_parser('tags', help='List all tags')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_problems(args)
    elif args.command == 'view':
        view_problem(args)
    elif args.command == 'tags':
        list_tags(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
