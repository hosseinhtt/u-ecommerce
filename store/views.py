from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, DetailView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db import connection
from django.contrib import messages
from django.http import HttpResponseRedirect

from store.models import Product, ReviewRating
from store.forms import ReviewForm
from category.models import Category
from carts.models import CartItem
from carts.views import CartMixin
from order.models import OrderProduct



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
        
        if self.request.user.is_authenticated:

            try:
                orderproduct = OrderProduct.objects.filter(user=self.request.user, product_id=product.id).exists()
            except OrderProduct.DoesNotExist:
                orderproduct = None
        else:
            orderproduct = None

        reviews = ReviewRating.objects.filter(product_id=product.id, status=True)

        context = {
            'product': product,
            'in_cart': in_cart,
            'reviews': reviews,
            'order_product': orderproduct,

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

class SubmitReviewView(View):
    def post(self, request, product_id):
        url = request.META.get('HTTP_REFERER')
        if request.method == 'POST':
            try:
                review = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
                form = ReviewForm(request.POST, instance=review)
                form.save()
                messages.success(request, 'Thank you! Your review has been updated.')
                return redirect(url)
            except ReviewRating.DoesNotExist:
                form = ReviewForm(request.POST)
                if form.is_valid():
                    review = form.save(commit=False)  # Create a new review object but don't save it yet
                    review.user = request.user
                    review.product_id = product_id
                    review.ip = request.META.get('REMOTE_ADDR')
                    review.save()  # Save the review now
                    messages.success(request, 'Thank you! Your review has been submitted.')
                    return redirect(url)