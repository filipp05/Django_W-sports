from .forms import SearchForm


def set_search_form(request):
    return {"search_form": SearchForm()}