# admin.py
from django.contrib import admin
from store.models import Product, Variation, ReviewRating, ProductGallery
from store.actions import *
import admin_thumbnails

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'price', 'stock', 'category', 'modified_date', 'is_available']
    prepopulated_fields = {'slug': ('product_name',)}
    actions = [set_is_available_false, set_is_available_true, set_stock_to_zero]
    inlines = [ProductGalleryInline]

admin.site.register(Product, ProductAdmin)

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active', 'created_date')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

admin.site.register(Variation, VariationAdmin)

admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
