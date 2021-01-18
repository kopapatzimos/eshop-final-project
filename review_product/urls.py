from django.conf.urls import url
from django.urls import path
from django.conf.urls import include

from . import views

urlpatterns = [
    # ex: /
    url(r"^$", views.review_list, name="review_list"),
    # ex: /review/5/
    url(r"^review/(?P<review_id>[0-9]+)/$", views.review_detail, name="review_detail"),
    # ex: /wine/
    url(r"^item$", views.item_list, name="item_list"),
    url(r"^item/(?P<item_id>[0-9]+)/$", views.item_detail, name="item_detail"),
    url(
        r"^itemzz/(?P<item_id>[0-9]+)/add_review/$", views.add_review, name="add_review"
    ),
]