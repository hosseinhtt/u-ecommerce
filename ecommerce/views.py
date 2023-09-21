from django.views.generic import TemplateView
from store.models import Product


class IndexView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        # Retrieve the products you want to pass to the template
        products = Product.objects.filter(is_available=True)

        # Create a context dictionary with the data you want to pass
        context = {
            'products': products,
        }

        return context