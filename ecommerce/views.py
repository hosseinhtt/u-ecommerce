from django.views.generic import TemplateView
from store.models import Product, ReviewRating


class IndexView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        # Retrieve the products you want to pass to the template
        products = Product.objects.filter(is_available=True).order_by('-created_date')

        for product in products:
            reviews = ReviewRating.objects.filter(product_id=product.id, status=True)


        # Create a context dictionary with the data you want to pass
        context = {
            'products': products,
            'reviews': reviews
        }

        return context