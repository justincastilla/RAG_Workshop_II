import math

# Our "database" - just a simple list of cached items
cache_storage = []


def simple_embedding(text):
    """
    Convert text to a simple number vector (embedding).
    We'll count how often each letter appears.
    """
    # Clean the text - lowercase, only letters
    clean_text = "".join(c.lower() for c in text if c.isalpha())

    # Count each letter (a=0, b=1, c=2, etc.)
    letter_counts = [0] * 26
    for char in clean_text:
        if "a" <= char <= "z":
            letter_counts[ord(char) - ord("a")] += 1

    return letter_counts


def similarity(embedding1, embedding2):
    """
    Calculate how similar two embeddings are (0 = different, 1 = identical).
    Uses cosine similarity - measures the angle between vectors.
    """
    # Dot product: multiply corresponding elements and sum
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

    # Magnitude: square root of sum of squares
    mag1 = math.sqrt(sum(x * x for x in embedding1))
    mag2 = math.sqrt(sum(x * x for x in embedding2))

    # Avoid division by zero
    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def find_similar_cache_entry(query, threshold=0.8):
    """
    Look through our cache for something similar to the query.
    Returns the cached answer if found, None if not found.
    """
    query_embedding = simple_embedding(query)

    for cached_item in cache_storage:
        cached_query = cached_item["query"]
        cached_embedding = cached_item["embedding"]
        cached_answer = cached_item["answer"]

        sim = similarity(query_embedding, cached_embedding)

        if sim >= threshold:
            print(
                f"Cache HIT! '{query}' is similar to '{cached_query}' (similarity: {sim:.2f})"
            )
            return cached_answer

    print(f"Cache MISS for '{query}'")
    return None


def add_to_cache(query, answer):
    """
    Store a new query and answer in our cache.
    """
    query_embedding = simple_embedding(query)

    cache_item = {"query": query, "answer": answer, "embedding": query_embedding}

    cache_storage.append(cache_item)
    print(f"Added to cache: '{query}' -> '{answer}'")


def cached_function(func, threshold=0.8):
    """
    A decorator that adds semantic caching to any function.
    This is a higher-order function - it takes a function and returns a new function.
    """

    def wrapper(query):
        # First, check if we have a similar answer cached
        cached_result = find_similar_cache_entry(query, threshold)

        if cached_result is not None:
            return cached_result

        # If not cached, run the original function
        result = func(query)

        # Save the result for next time
        add_to_cache(query, result)

        return result

    return wrapper


def show_cache():
    """
    Display what's currently in our cache.
    """
    print("\n=== CACHE CONTENTS ===")
    if not cache_storage:
        print("Cache is empty")
    else:
        for i, item in enumerate(cache_storage):
            print(f"{i+1}. Query: '{item['query']}' -> Answer: '{item['answer']}'")
    print("=====================\n")


# Example: A slow function we want to cache
def slow_answer_function(question):
    """
    Pretend this is a slow function (like calling an AI API).
    """
    print(f"Thinking hard about: '{question}'...")

    # Some simple responses based on keywords
    question_lower = question.lower()

    if "python" in question_lower:
        return "Python is a great programming language!"
    elif "cache" in question_lower:
        return "Caching stores results to make things faster!"
    elif "weather" in question_lower:
        return "I don't know the weather, try a weather app!"
    else:
        return "That's an interesting question!"


# Wrap our slow function with caching
cached_answer_function = cached_function(slow_answer_function, threshold=0.7)

# Test it out!
if __name__ == "__main__":
    print("=== SEMANTIC CACHE DEMO ===\n")

    # First time asking - will be slow
    q1 = "What is Python programming?"
    print(f"1. First question: '{q1}'")
    answer1 = cached_answer_function(q1)
    print(f"Answer: {answer1}\n")

    # Similar question - should use cache
    q2 = "Tell me about Python coding"
    print(f"2. Similar question: '{q2}'")
    answer2 = cached_answer_function(q2)
    print(f"Answer: {answer2}\n")

    # Different question - will be slow again
    q3 = "How does caching work?"
    print(f"3. Different question: '{q3}'")
    answer3 = cached_answer_function(q3)
    print(f"Answer: {answer3}\n")

    # Another similar question - should use cache
    q4 = "Explain caching to me"
    print(f"4. Another similar question: '{q4}'")
    answer4 = cached_answer_function(q4)
    print(f"Answer: {answer4}\n")

    # Show what's in our cache
    show_cache()

    # Test manual cache operations
    print("=== MANUAL CACHE OPERATIONS ===")
    add_to_cache("machine learning", "ML is AI that learns from data!")

    result = find_similar_cache_entry("what is ML?", threshold=0.6)
    if result:
        print(f"Found: {result}")

    show_cache()
