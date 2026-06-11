from .logging import clean_request_id, reset_request_id, set_request_id


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = clean_request_id(request.headers.get("X-Request-ID"))
        token = set_request_id(request_id)
        request.request_id = request_id

        try:
            response = self.get_response(request)
        finally:
            reset_request_id(token)

        response["X-Request-ID"] = request_id
        return response
