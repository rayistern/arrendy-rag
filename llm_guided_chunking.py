def get_chunk_boundaries(text, llm, approximate_chunk_size=200):
    prompt = f"""
    Given the following text, suggest a good starting point for a chunk of approximately {approximate_chunk_size} characters. 
    Provide the answer as a line number and character position, like this: 'line 3, character 25'.
    If the text is one continuous line, just provide the character position.
    Here's the text:

    {text[:1000]}  # We'll only send the first 1000 characters to save tokens

    Suggested chunk start:
    """
    start_position = llm.generate(prompt)  # This would return something like "line 1, character 0" or just "character 0"

    # Now we ask for the end position
    prompt = f"""
    Now, starting from the position you just suggested ({start_position}), 
    suggest an ending point for a chunk of approximately {approximate_chunk_size} characters.
    Provide the answer as a line number and character position, or just character position if it's one continuous line.
    
    Suggested chunk end:
    """
    end_position = llm.generate(prompt)

    return start_position, end_position

def create_chunks_with_llm(text, llm):
    chunks = []
    current_position = 0
    while current_position < len(text):
        start, end = get_chunk_boundaries(text[current_position:], llm)
        # Convert the LLM's response to actual indices
        start_index = convert_to_index(text, start, current_position)
        end_index = convert_to_index(text, end, current_position)
        chunks.append(text[start_index:end_index])
        current_position = end_index
    return chunks

def convert_to_index(text, position_str, offset):
    # This function would convert "line 3, character 25" or "character 25" to an actual index
    # The implementation would depend on how your text is structured (single line or multiple lines)
    # Here's a simple version assuming it's all one line:
    return offset + int(position_str.split()[-1])