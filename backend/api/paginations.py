from rest_framework.pagination import PageNumberPagination


class RecipesPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
