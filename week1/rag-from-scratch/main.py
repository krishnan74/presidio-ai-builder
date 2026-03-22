from vector_store import collection
from processing import process_and_add_documents
from llm import generate_response
from conversation import create_session, add_message, format_history_for_prompt, contextualize_query

def semantic_search(collection, query: str, n_results: int = 2):
    """Perform semantic search on the collection"""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results

def get_context_with_sources(results):
    """Extract context and source information from search results"""
    context = "\n\n".join(results['documents'][0])
    sources = [
        f"{meta['source']} (chunk {meta['chunk']})"
        for meta in results['metadatas'][0]
    ]
    return context, sources

def print_search_results(results):
    """Print formatted search results"""
    print("\nSearch Results:\n" + "-" * 50)
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        print(f"\nResult {i + 1}")
        print(f"Source: {meta['source']}, Chunk {meta['chunk']}")
        print(f"Distance: {distance}")
        print(f"Content: {doc}\n")

def rag_query(collection, query: str, n_chunks: int = 2):
    """Perform RAG query: retrieve relevant chunks and generate answer"""
    results = semantic_search(collection, query, n_chunks)
    context, sources = get_context_with_sources(results)
    response = generate_response(query, context)
    return response, sources

def conversational_rag_query(collection, query: str, session_id: str, n_chunks: int = 3):
    """Perform RAG query with conversation history"""
    conversation_history = format_history_for_prompt(session_id)

    # Reformulate follow-up questions into standalone queries
    query = contextualize_query(query, conversation_history)
    print("Contextualized Query:", query)

    context, sources = get_context_with_sources(
        semantic_search(collection, query, n_chunks)
    )

    response = generate_response(query, context, conversation_history)

    add_message(session_id, "user", query)
    add_message(session_id, "assistant", response)

    return response, sources


if __name__ == "__main__":
    # Process and add documents from a folder
    folder_path = "./docs"
    process_and_add_documents(collection, folder_path)

    session_id = create_session()

    # First question
    query = "When was Nexus AI Technologies founded?"
    response, sources = conversational_rag_query(collection, query, session_id)
    print("\nQuery:", query)
    print("\nAnswer:", response)
    print("\nSources used:")
    for source in sources:
        print(f"- {source}")

    # Follow-up question (relies on conversation history to be contextualized)
    query = "Where is it headquartered?"
    response, sources = conversational_rag_query(collection, query, session_id)
    print("\nQuery:", query)
    print("\nAnswer:", response)
    print("\nSources used:")
    for source in sources:
        print(f"- {source}")
