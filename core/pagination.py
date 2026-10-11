# Pagination that only kicks in when the client asks for it with ?page=N.
# Without the parameter the list endpoints return a plain JSON array.
from rest_framework.pagination import PageNumberPagination


class OptionalPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        if self.page_query_param not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)
