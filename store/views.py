from django.views.generic import TemplateView, DetailView
from django.shortcuts import get_object_or_404
from django.http import Http404
from store.models import Product
from category.models import Category

class StoreView(TemplateView):
    template_name = 'store/store.html'

    def get_context_data(self, **kwargs):
        category_slug = self.kwargs.get('category_slug')
        
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            products = Product.objects.filter(category=category, is_available=True)
        else:
            products = Product.objects.filter(is_available=True)
        
        product_count = products.count()
        
        context = {
            'products': products,
            'count': product_count,
        }

        return context
    
class ProductDetailView(TemplateView):
    template_name = 'store/product_detail.html'

    def get_object(self, queryset=None):
        """
        Retrieve the product based on category_slug and product_slug.
        Raises Http404 if the product is not found.
        """
        # Get the category_slug and product_slug from URL parameters
        category_slug = self.kwargs.get('category_slug')
        product_slug = self.kwargs.get('product_slug')

        try:
            # Retrieve the product with the given slugs
            product = Product.objects.get(category__slug=category_slug, slug=product_slug, is_available=True)
        except Product.DoesNotExist:
            # If the product does not exist, raise a 404 error
            raise Http404("Product not found")

        return product

    def get_context_data(self, **kwargs):
        # Use the retrieved product in the context
        product = self.get_object()
        context = {
            'product': product,
        }
        return context