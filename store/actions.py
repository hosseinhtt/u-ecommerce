import time

from store.tasks import *


def set_is_deleted_true(modeladmin, request, queryset):
    # time.sleep(20)
    ids = list(queryset.values_list('id', flat=True))
    set_is_deleted_true_task.delay(ids)
