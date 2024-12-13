from app import create_app

app = create_app()

@app.template_filter('dict_without')
def dict_without(d, key):
    """
    Remove a key from a dictionary.
    """
    return {k: v for k, v in d.items() if k != key}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
