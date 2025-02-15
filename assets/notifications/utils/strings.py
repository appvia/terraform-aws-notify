def format_key_name(key: str) -> str:
    """
    Format a key string by replacing underscores with spaces and titlecasing each word.

    Args:
        key (str): The key string to format

    Returns:
        str: The formatted string
    """
    return " ".join(word.title() for word in key.replace("_", " ").split())
