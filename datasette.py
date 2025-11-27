import os
import requests
import subprocess
import time
from openai import OpenAI

# 1. Path to your existing database
DB_PATH = "path/to/your/existing/database.db"  # Replace with your actual database path

# 2. Launch Datasette server with your existing database
def start_datasette_server(db_path, port=8001):
    print(f"Starting Datasette server with {db_path} on port {port}...")
    
    # Run in background
    process = subprocess.Popen(
        ["datasette", db_path, "-p", str(port), "--cors"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give it a moment to start
    time.sleep(3)
    print(f"Datasette server running at http://localhost:{port}")
    
    return process, port

# 3. Function to explore database schema
def get_database_schema(port=8001):
    """Get the schema of all tables in the database"""
    url = f"http://localhost:{port}/-/databases.json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        databases = response.json()
        
        schemas = {}
        for db in databases["databases"]:
            db_name = db["name"]
            tables_url = f"http://localhost:{port}/{db_name}.json"
            tables_response = requests.get(tables_url)
            tables_response.raise_for_status()
            schemas[db_name] = tables_response.json()
        
        return schemas
    except Exception as e:
        print(f"Error getting schema: {e}")
        return {}

# 4. Function to query Datasette with custom SQL
def query_datasette(sql_query, db_name=None, port=8001):
    """Execute SQL query against Datasette and return results"""
    # If db_name is not provided, use the database filename without extension
    if db_name is None:
        db_name = os.path.basename(DB_PATH).split('.')[0]
        
    encoded_query = requests.utils.quote(sql_query)
    url = f"http://localhost:{port}/{db_name}.json?sql={encoded_query}&_shape=array"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error querying Datasette: {e}")
        return []

# 5. Function to use retrieved data with an LLM
def ask_llm_with_context(question, context_data, api_key=None):
    """Query an LLM with context from the database"""
    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
    
    # Format the context data for the prompt
    if isinstance(context_data, list) and len(context_data) > 0:
        # Format as a readable table-like structure if it's a list of records
        if len(context_data) > 10:
            context_data = context_data[:10]  # Limit to 10 records if there are many
            context_text = f"{len(context_data)} records found. Here's a sample:\n\n"
        else:
            context_text = f"{len(context_data)} records found:\n\n"
            
        # Get column names from the first record
        if context_data:
            columns = list(context_data[0].keys())
            context_text += "| " + " | ".join(columns) + " |\n"
            context_text += "| " + " | ".join(["---" for _ in columns]) + " |\n"
            
            for record in context_data:
                context_text += "| " + " | ".join([str(record[col])[:50] for col in columns]) + " |\n"
    else:
        context_text = str(context_data)
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided database information."},
                {"role": "user", "content": f"Here is data from my database: \n\n{context_text}\n\nBased on this data, please answer: {question}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error querying LLM: {e}"

# 6. Function to generate SQL from natural language using an LLM
def generate_sql_from_question(question, schema_info, api_key=None):
    """Generate SQL based on a natural language question"""
    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a SQL expert. Generate a valid SQL query based on the user's question and the provided database schema. Return ONLY the SQL query without any explanation or markdown."},
                {"role": "user", "content": f"Database schema information:\n{schema_info}\n\nGenerate a SQL query for the following question: {question}"}
            ]
        )
        sql_query = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query.split("```")[1]
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
        elif sql_query.startswith("```"):
            sql_query = sql_query.split("```")[1]
            
        return sql_query.strip()
    except Exception as e:
        return f"Error generating SQL: {e}"

# 7. Interactive session to query your database with natural language
def interactive_query_session():
    process, port = start_datasette_server(DB_PATH)
    
    try:
        # Get database schema for context
        print("Exploring database schema...")
        schema = get_database_schema(port)
        schema_info = str(schema)
        
        print("\nYou can now ask questions about your database.")
        print("Type 'exit' to quit.")
        
        while True:
            question = input("\nEnter your question: ")
            if question.lower() == 'exit':
                break
                
            # Generate SQL from the question
            print("Generating SQL query...")
            sql_query = generate_sql_from_question(question, schema_info)
            print(f"\nGenerated SQL: {sql_query}")
            
            # Execute the query
            print("Executing query...")
            results = query_datasette(sql_query, port=port)
            
            if not results:
                print("No results found or error in query.")
                continue
                
            # Get insights from LLM
            print("Analyzing results with LLM...")
            answer = ask_llm_with_context(question, results)
            
            print("\n=== Answer ===")
            print(answer)
            
    finally:
        # Clean up: terminate the Datasette server
        print("Shutting down Datasette server...")
        process.terminate()

if __name__ == "__main__":
    interactive_query_session()