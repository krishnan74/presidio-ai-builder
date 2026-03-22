from openai import OpenAI

# Ollama exposes an OpenAI-compatible API on localhost
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

def get_prompt(context: str, conversation_history: str, query: str):
    """Generate a prompt combining context, history, and query"""
    prompt = f"""Based on the following context and conversation history,
    please provide a relevant and contextual response. If the answer cannot
    be derived from the context, only use the conversation history or say
    "I cannot answer this based on the provided information."

    Context from documents:
    {context}

    Previous conversation:
    {conversation_history}

    Human: {query}

    Assistant:"""

    return prompt

def generate_response(query: str, context: str, conversation_history: str = ""):
    """Generate a response using local Ollama deepseek-r1 with conversation history"""
    prompt = get_prompt(context, conversation_history, query)

    try:
        response = client.chat.completions.create(
            model="deepseek-r1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"
