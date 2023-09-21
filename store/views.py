from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
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
