import json
import logging

logger = logging.getLogger("ig_client")


def log_request(request):
    """Log the outgoing request details."""
    logger.debug("=== REQUEST ===")
    logger.debug(f"Method: {request.method}")
    logger.debug(f"URL: {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")

    # For httpx, check if request has content to log
    try:
        if hasattr(request, "content") and request.content:
            content = request.content
            if isinstance(content, bytes):
                try:
                    if request.headers.get("content-type", "").startswith(
                        "application/json"
                    ):
                        body = json.loads(content.decode("utf-8"))
                        logger.debug(f"Body: {json.dumps(body, indent=2)}")
                    else:
                        logger.debug(f"Body: {content.decode('utf-8')}")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    logger.debug(f"Body (raw): {content}")
            else:
                logger.debug(f"Body: {content}")
        elif hasattr(request, "stream") and request.stream:
            # For streamed requests, we can't easily log the body without consuming it
            logger.debug("Body: <streamed content>")
    except Exception as e:
        logger.debug(f"Could not log request body: {e}")
    logger.debug("=== END REQUEST ===")


def log_response(response):
    """Log the incoming response details."""
    logger.debug("=== RESPONSE ===")
    logger.debug(f"Status Code: {response.status_code}")
    logger.debug(f"Headers: {dict(response.headers)}")

    try:
        # Ensure the response content is read
        if not response.is_closed:
            # For sync responses, .read() ensures content; async hook ensures aread() beforehand
            if hasattr(response, "_content") and response._content is None:
                try:
                    response.read()
                except Exception:
                    # In async context, read is handled in async hook
                    pass

        if response.content:
            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = response.json()
                    logger.debug(f"Body: {json.dumps(body, indent=2)}")
                except json.JSONDecodeError:
                    # Fallback to text if JSON parsing fails
                    logger.debug(f"Body: {response.text}")
            else:
                logger.debug(f"Body: {response.text}")
        else:
            logger.debug("Body: <empty>")
    except (json.JSONDecodeError, UnicodeDecodeError):
        try:
            logger.debug(f"Body (raw): {response.content}")
        except Exception:
            logger.debug("Body: <could not decode>")
    except Exception as e:
        logger.debug(f"Could not log response body: {e}")
    logger.debug("=== END RESPONSE ===")


def request_hook(request):
    """Hook called before sending a request (sync client)."""
    log_request(request)


def response_hook(response):
    """Hook called after receiving a response (sync client)."""
    log_response(response)


async def async_request_hook(request):
    """Async hook called before sending a request (AsyncClient)."""
    log_request(request)


async def async_response_hook(response):
    """Async hook called after receiving a response (AsyncClient)."""
    try:
        # Ensure content is read in async context for safe logging
        await response.aread()
    except Exception:
        pass
    log_response(response)
