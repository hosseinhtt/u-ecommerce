from ecommerce.celery import app
from store.models import Product


@app.task
def set_is_deleted_true_task(product_ids):
    products = Product.objects.filter(id__in=product_ids)
    for product in products:
        product.is_deleted = True
        product.save()
