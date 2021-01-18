from django.urls import path
from django.conf.urls import include, url

from .views import (
    ItemDetailView,
    CheckoutView,
    HomeView,
    GuitarsView,
    BassView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    WishlistView,
    add_to_wishlist,
    remove_from_wishlist,
    remove_single_item_from_wishlist,
    TagIndexView,
    searchposts,
    price_filter,
    popular_filter,
    add_to_cart_quantity,
    remove_all_from_cart,
)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("Guitars", GuitarsView.as_view(), name="Guitars"),
    path("Basses", BassView.as_view(), name="Basses"),
    path("wishlist", WishlistView.as_view(), name="wishlist"),
    path("add-to-wishlist/<slug>/", add_to_wishlist, name="add-to-wishlist"),
    path(
        "remove-from-wishlist/<slug>/",
        remove_from_wishlist,
        name="remove-from-wishlist",
    ),
    path(
        "remove-item-from-wishlist/<slug>/",
        remove_single_item_from_wishlist,
        name="remove-single-item-from-wishlist",
    ),
    path("home/filtered", price_filter, name="price_filter"),
    path("most_popular", popular_filter, name="popular_filter"),
    path(
        "add-to-cart-quantity/<slug>/",
        add_to_cart_quantity,
        name="add_to_cart_quantity",
    ),
    path("remove_all_from_cart", remove_all_from_cart, name="remove_all_from_cart"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("order-summary/", OrderSummaryView.as_view(), name="order-summary"),
    path("product/<slug>/", ItemDetailView.as_view(), name="product"),
    path("add-to-cart/<slug>/", add_to_cart, name="add-to-cart"),
    path("add-coupon/", AddCouponView.as_view(), name="add-coupon"),
    path("remove-from-cart/<slug>/", remove_from_cart, name="remove-from-cart"),
    path(
        "remove-item-from-cart/<slug>/",
        remove_single_item_from_cart,
        name="remove-single-item-from-cart",
    ),
    path("payment/<payment_option>/", PaymentView.as_view(), name="payment"),
    path("request-refund/", RequestRefundView.as_view(), name="request-refund"),
    path("tag/<slug>", TagIndexView.as_view(), name="tagged"),
    url(r"^$", searchposts, name="searchposts"),
]
