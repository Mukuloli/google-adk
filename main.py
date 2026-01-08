import json
import os
import sys
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")
    print("Set it with: export GOOGLE_API_KEY='your-api-key'")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)


# --- Data Layer ---

def load_data(filepath: str = "dummy_data.json") -> Dict[str, Any]:
    """Loads the knowledge base from JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filepath} not found. Please ensure dummy_data.json exists.")
        sys.exit(1)


DATA = load_data()


def get_namespace_summaries() -> str:
    """Returns summaries of all namespaces for Agent 2 to analyze."""
    summaries = []
    
    # Handle both "namespaces" and "dataset" as potential keys
    namespaces = DATA.get("namespaces", DATA.get("dataset", []))
    
    for ns in namespaces:
        summary = f"""
Namespace ID: {ns.get('namespace_id', 'N/A')}
Title: {ns.get('title', 'N/A')}
Description: {ns.get('description', 'N/A')}
"""
        summaries.append(summary.strip())
    
    return "\n\n".join(summaries)


def get_namespace_data(namespace_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full data for a specific namespace."""
    namespaces = DATA.get("namespaces", DATA.get("dataset", []))
    
    for ns in namespaces:
        if ns.get('namespace_id') == namespace_id:
            return ns
    return None


# --- Agent Classes ---

class Agent:
    """Base agent class using Google Gemini API."""
    
    def __init__(self, name: str, model_name: str, system_instruction: str):
        self.name = name
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
    
    def generate(self, prompt: str) -> str:
        """Generates a response from the agent."""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in {self.name}: {e}")
            return f"Error: {str(e)}"


class UserInteractionAgent(Agent):
    """Agent 1: Captures and forwards user input."""
    
    def __init__(self):
        super().__init__(
            name="UserInteractionAgent",
            model_name="gemini-2.0-flash-exp",
            system_instruction="""You are the user interface agent.
Your role is simple:
1. Acknowledge receipt of the user's query
2. Confirm you are forwarding it for analysis
3. Do NOT attempt to answer the query yourself

Keep your response brief and professional."""
        )
    
    def process_input(self, user_query: str) -> str:
        """Processes user input and forwards to next agent."""
        # Simple acknowledgment - no need to call LLM for this
        return user_query


class QueryAnalysisAgent(Agent):
    """Agent 2: Analyzes query and identifies ALL relevant namespaces."""
    
    def __init__(self):
        # Get namespace summaries dynamically
        namespace_info = get_namespace_summaries()
        
        super().__init__(
            name="QueryAnalysisAgent",
            model_name="gemini-2.0-flash-exp",
            system_instruction=f"""You are an expert semantic analysis agent specializing in query understanding and intelligent routing.

Your task:
1. Carefully analyze the USER'S QUERY to understand their intent, topic, and what information they're seeking
2. Review ALL available knowledge namespaces below
3. Identify ALL namespaces that contain relevant information for the query
4. A query may match MULTIPLE namespaces if the same information exists in different namespaces
5. If the query does NOT match ANY namespace, output exactly: "NO_NAMESPACE_FOUND"
6. Otherwise output ALL matching namespace_ids separated by commas

Available Knowledge Namespaces:
{namespace_info}

CRITICAL RULES:
- Output ALL relevant namespace_ids separated by commas (example: namespace_001,namespace_009,namespace_010)
- OR output "NO_NAMESPACE_FOUND" if no matches
- No explanations, no extra text, no spaces around commas
- If multiple namespaces have the same title/description and are relevant, include ALL of them
- Example outputs:
  * Single match: namespace_001
  * Multiple matches: namespace_001,namespace_009,namespace_010
  * No match: NO_NAMESPACE_FOUND"""
        )
    
    def analyze_query(self, user_query: str) -> Optional[List[str]]:
        """Analyzes query and returns list of ALL selected namespace IDs."""
        prompt = f"User Query: {user_query}"
        response = self.generate(prompt).strip()
        
        # Check if no namespace found
        if "NO_NAMESPACE_FOUND" in response.upper():
            print("This query has no namespace")
            return None
        
        # Split by comma to get all namespace IDs
        namespace_ids = [ns.strip() for ns in response.split(',')]
        
        return namespace_ids


class NamespaceResponseAgent(Agent):
    """Agent 3: Retrieves data and formulates response."""
    
    def __init__(self):
        super().__init__(
            name="NamespaceResponseAgent",
            model_name="gemini-2.0-flash-exp",
            system_instruction="""You are a knowledgeable educational response agent.

Your task:
1. You will receive namespace data and the original user query
2. The namespace contains comprehensive knowledge on a specific subject
3. Carefully analyze what the user is asking
4. Extract and synthesize relevant information from the namespace description and content
5. Provide a clear, accurate, and educational response
6. If the query asks for specific formulas, steps, or examples, provide them
7. Structure your response in a user-friendly, easy-to-understand manner

Response Guidelines:
- Be comprehensive but concise
- Use examples when helpful
- Break down complex concepts into simpler terms
- If the data covers the topic generally but not the specific question, provide the closest relevant information
- Format your response with proper structure (use line breaks for readability)
- Be educational and helpful in tone"""
        )
    
    def formulate_response(self, namespace_id: str, user_query: str) -> str:
        """Retrieves namespace data and formulates final response."""
        
        # Retrieve namespace data
        namespace_data = get_namespace_data(namespace_id)
        
        if not namespace_data:
            return f"Error: Could not find data for namespace {namespace_id}"
        
        # Prepare prompt with namespace data and user query
        prompt = f"""
User Query: {user_query}

Namespace Data:
{json.dumps(namespace_data, indent=2)}

Based on the namespace data above, provide a comprehensive answer to the user's query."""
        
        response = self.generate(prompt)
        return response


# --- Orchestrator ---

class MultiAgentOrchestrator:
    """Orchestrates the multi-agent system."""
    
    def __init__(self):
        self.agent1 = UserInteractionAgent()
        self.agent2 = QueryAnalysisAgent()
        self.agent3 = NamespaceResponseAgent()
    
    def process_query(self, user_query: str) -> Optional[List[str]]:
        """Processes a user query through all agents."""
        
        # Agent 1: User Interaction (simple forwarding)
        forwarded_query = self.agent1.process_input(user_query)
        
        # Agent 2: Query Analysis & Namespace Identification
        namespace_ids = self.agent2.analyze_query(forwarded_query)
        
        # If no namespace found, stop here
        if namespace_ids is None:
            return None
        
        # Print only namespace names
        print(f"Matching Namespaces: {', '.join(namespace_ids)}")
        
        return namespace_ids


# --- Main Execution ---

def main():
    """Main execution function."""
    orchestrator = MultiAgentOrchestrator()
    
    if len(sys.argv) > 1:
        # Query provided as command line argument
        query = " ".join(sys.argv[1:])
        orchestrator.process_query(query)
    else:
        # Interactive mode
        print("\nMulti-Agent System - Interactive Mode")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                if not query:
                    continue
                
                orchestrator.process_query(query)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
