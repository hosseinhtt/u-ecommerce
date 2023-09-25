# tasks.py
from ecommerce.celery import app
from store.models import Product

@app.task
def set_is_available_false_task(product_ids):
    products = Product.objects.filter(id__in=product_ids)
    for product in products:
        product.is_available = False
        product.save()

@app.task
def set_is_available_true_task(product_ids):
    products = Product.objects.filter(id__in=product_ids)
    for product in products:
        product.is_available = True
        product.save()

@app.task
def set_stock_to_zero_task(product_ids):
    products = Product.objects.filter(id__in=product_ids)
    for product in products:
        product.stock = 0
        product.save()
