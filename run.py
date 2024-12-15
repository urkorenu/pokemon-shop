from app import create_app

# Create the Flask application instance
app = create_app()


@app.template_filter("dict_without")
def dict_without(d, key):
    """
    Remove a key from a dictionary.

    Args:
        d (dict): The dictionary to remove the key from.
        key: The key to remove from the dictionary.

    Returns:
        dict: A new dictionary without the specified key.
    """
    return {k: v for k, v in d.items() if k != key}


if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000)
