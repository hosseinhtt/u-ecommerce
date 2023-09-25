# actions.py
from store.tasks import set_is_available_false_task, set_is_available_true_task, set_stock_to_zero_task

def set_is_available_false(modeladmin, request, queryset):
    ids = list(queryset.values_list('id', flat=True))
    set_is_available_false_task.delay(ids)
set_is_available_false.short_description = "Set selected products as unavailable"

def set_is_available_true(modeladmin, request, queryset):
    ids = list(queryset.values_list('id', flat=True))
    set_is_available_true_task.delay(ids)
set_is_available_true.short_description = "Set selected products as available"

def set_stock_to_zero(modeladmin, request, queryset):
    ids = list(queryset.values_list('id', flat=True))
    set_stock_to_zero_task.delay(ids)
set_stock_to_zero.short_description = "Set selected products as out of stock"
