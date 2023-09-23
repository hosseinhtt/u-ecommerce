from django.shortcuts import render
from django.views.generic import View, TemplateView, DetailView
from django.shortcuts import get_object_or_404
from django.http import Http404
from store.models import Product
from category.models import Category
from carts.models import CartItem
from carts.views import CartMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db import connection



class StoreView(TemplateView):
    template_name = 'store/store.html'

    def get_context_data(self, **kwargs):
        category_slug = self.kwargs.get('category_slug')
        
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            products = Product.objects.filter(category=category, is_available=True)
        else:
            products = Product.objects.filter(is_available=True).order_by('-created_date')
        
        paginator = Paginator(products, 3)
        page = self.request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
        
        context = {
            'products': products,
            'product_count': product_count,
            'paged_products': paged_products
        }

        return context
    

class ProductDetailView(TemplateView):
    template_name = 'store/product_detail.html'

    def get_context_data(self, **kwargs):
        # Get the category_slug and product_slug from URL parameters
        category_slug = self.kwargs.get('category_slug')
        product_slug = self.kwargs.get('product_slug')

        try:
            # Retrieve the product with the given slugs
            product = Product.objects.get(category__slug=category_slug, slug=product_slug, is_available=True)
            
            # Create an instance of CartMixin
            cart_mixin = CartMixin()
            # Use the _cart_id method from CartMixin
            cart_id = cart_mixin._cart_id(self.request)
            
            in_cart = CartItem.objects.filter(cart__cart_id=cart_id, product=product).exists()

        except Product.DoesNotExist:
            # If the product does not exist, raise a 404 error
            raise Http404("Product not found")

        context = {
            'product': product,
            'in_cart': in_cart,
        }
        return context

import logging

logger = logging.getLogger(__name__)

class SearchView(View):
    template_name = 'store/store.html'

    def get(self, request):
        keyword = request.GET.get('keyword', '')

        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            
            product_count = products.count()
        else:
            products = []
            product_count = 0

        paginator = Paginator(products, 3)
        page = self.request.GET.get('page')
        paged_products = paginator.get_page(page)

        context = {
            'products': products,
            'product_count': product_count,
            'paged_products': paged_products,
        }
        
        return render(request, self.template_name, context)
