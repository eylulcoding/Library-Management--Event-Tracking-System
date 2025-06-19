from django.core.cache import cache

class CurrentRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cache.set('_current_request', request)
        response = self.get_response(request)
        cache.delete('_current_request')
        return response 