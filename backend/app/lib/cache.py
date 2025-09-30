from urllib.parse import urlparse


def parse_redis_url(redis_url: str) -> dict:
    """Parse a Redis URL into its components.

    Args:
        redis_url (str): The Redis URL to parse (e.g. redis://:password@host:port/db).

    Returns:
        dict: A dictionary containing the parsed components:
            - host (str): The Redis host.
            - port (int): The Redis port.
            - db (int): The Redis database number.
            - password (str | None): The Redis password, if provided.
    """
    parsed_url = urlparse(redis_url)
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or 6379
    db = int((parsed_url.path or "/0").lstrip("/")) if parsed_url.path else 0
    password = parsed_url.password
    return {
        "host": host or None,
        "port": port or None,
        "db": db or None,
        "password": password or None,
    }
