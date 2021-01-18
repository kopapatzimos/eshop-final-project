from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm
from .models import (
    Item,
    OrderItem,
    Order,
    Address,
    Payment,
    Coupon,
    Refund,
    UserProfile,
    Wishlist,
    WishlistItem,
)
from review_product.models import Review

from django.db.models import Q
from search.views import searchposts
from django.db.models import Sum, Avg, Count
from taggit.models import Tag

import random
import string
import stripe

from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.views.generic.list import MultipleObjectMixin

stripe.api_key = settings.STRIPE_SECRET_KEY


def price_filter(request):

    model = Item
    template_name = "home.html"

    if request.method == "POST":

        # get the input values from the form
        low = int(request.POST.get("lowest"))

        high = int(request.POST.get("highest"))
        # print(high)
        # print(low)
        submitbutton = request.POST.get("submit")

        if high != 0:

            results = (
                Item.objects.filter(price__range=(low, high))
                .distinct()
                .order_by("price")
            )
            # print(results)
            context = {"results": results, "submitbutton": submitbutton}

            return render(request, template_name, context)
        else:
            return render(request, template_name)

    else:
        return render(request, template_name)


def popular_filter(request):

    model = Item
    template_name = "home.html"
    ratings = []

    popular = Item.objects.annotate(
        num_rev=Count("review"), average_rating=Avg("review__rating")
    ).order_by("-num_rev")

    for i in popular:
        if i.average_rating == None:
            i.average_rating = 0
            i.average_rating = int(i.average_rating)
        else:
            i.average_rating = int(i.average_rating)
        print(i.average_rating)
    context = {"results": popular}

    return render(request, template_name, context)


def create_ref_code():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {"items": Item.objects.all()}
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                "form": form,
                "couponform": CouponForm(),
                "order": order,
                "DISPLAY_COUPON_FORM": True,
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user, address_type="S", default=True
            )
            if shipping_address_qs.exists():
                context.update({"default_shipping_address": shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user, address_type="B", default=True
            )
            if billing_address_qs.exists():
                context.update({"default_billing_address": billing_address_qs[0]})

            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                print("User is entering a new shipping address")
                shipping_address1 = form.cleaned_data.get("shipping_address")
                print("Shipping Address:" + shipping_address1)

                shipping_address2 = form.cleaned_data.get("shipping_address2")
                shipping_country = form.cleaned_data.get("shipping_country")
                print("Shipping country:" + shipping_country)
                shipping_zip = form.cleaned_data.get("shipping_zip")
                print("Shipping Zip:" + shipping_address1)
                if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                    shipping_address = Address(
                        user=self.request.user,
                        street_address=shipping_address1,
                        apartment_address=shipping_address2,
                        country=shipping_country,
                        zip=shipping_zip,
                        address_type="S",
                    )
                    shipping_address.save()

                    order.shipping_address = shipping_address

                    order.save()

                else:
                    messages.info(
                        self.request,
                        "Please fill in the required shipping address fields",
                    )

                print("User is entering a new billing address")
                billing_address1 = form.cleaned_data.get("billing_address")
                print("Billing 1:" + billing_address1)
                billing_address2 = form.cleaned_data.get("billing_address2")
                billing_country = form.cleaned_data.get("billing_country")
                print("Billing country:" + billing_country)
                billing_zip = form.cleaned_data.get("billing_zip")
                print("Billing zip:" + billing_zip)
                if is_valid_form([billing_address1, billing_country, billing_zip]):
                    billing_address = Address(
                        user=self.request.user,
                        street_address=billing_address1,
                        apartment_address=billing_address2,
                        country=billing_country,
                        zip=billing_zip,
                        address_type="B",
                    )
                    billing_address.save()

                    order.billing_address = billing_address
                    order.save()

                else:
                    messages.info(
                        self.request,
                        "Please fill in the required billing address fields",
                    )

            payment_option = form.cleaned_data.get("payment_option")
            context = {
                "shipping": shipping_address1,
                "billing": billing_address1,
                "shipping_country": shipping_country,
                "billing_country": billing_country,
                "zip1": shipping_zip,
                "zip2": billing_zip,
                "order": order,
            }
            return render(self.request, "gameover.html", context)

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {"order": order, "DISPLAY_COUPON_FORM": False}
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id, limit=3, object="card"
                )
                card_list = cards["data"]
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({"card": card_list[0]})
            return render(self.request, "payment.html", context)
        else:
            messages.warning(self.request, "You have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get("stripeToken")
            save = form.cleaned_data.get("save")
            use_default = form.cleaned_data.get("use_default")

            if save:
                if (
                    userprofile.stripe_customer_id != ""
                    and userprofile.stripe_customer_id is not None
                ):
                    customer = stripe.Customer.retrieve(userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer["id"]
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id,
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount, currency="usd", source=token  # cents
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge["id"]
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get("error", {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request,
                    "Something went wrong. You were not charged. Please try again.",
                )
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed."
                )
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")


class TagMixin(object):
    def get_context_data(self, **kwargs):
        context = super(TagMixin, self).get_context_data(**kwargs)
        context["tags"] = Item.objects.all()

        return context


class HomeView(ListView):
    model = Item
    paginate_by = 4
    template_name = "home.html"
    ordering = ["price"]


class GuitarsView(ListView):
    model = Item
    paginate_by = 10
    template_name = "guitars.html"
    ordering = ["price"]


class BassView(ListView):
    model = Item
    paginate_by = 10
    template_name = "bass.html"
    ordering = ["price"]


class Account(LoginRequiredMixin, View):

    model = UserProfile

    def get(self, *args, **kwargs):
        try:
            order = list(OrderItem.objects.filter(user=self.request.user))
            print(order)
            context = {"object": order}
            return render(self.request, "account_info.html", context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {"object": order}
            return render(self.request, "order_summary.html", context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class WishlistView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            wish = Wishlist.objects.get(user=self.request.user, wished=False)
            context = {"object": wish}
            return render(self.request, "wishlist.html", context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"
    paginate_by = 4

    # function to  get the related items/reviews of a product
    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)

        context["related_items"] = self.object.tags.similar_objects()
        context["product_reviews"] = self.object.review_set.all().order_by("-pub_date")
        context["tags"] = Item.objects.all()

        return context


class TagIndexView(TagMixin, ListView):
    template_name = "home.html"
    model = Item
    paginate_by = 10
    context_object_name = "items"

    def get_queryset(self):
        return Item.objects.filter(tags__slug=self.kwargs.get("slug"))


# -----------------------WISHLIST------------------------------
@login_required
def add_to_wishlist(request, slug):
    # template = "wishlist.html"
    item = get_object_or_404(Item, slug=slug)
    wish_item, created = WishlistItem.objects.get_or_create(
        item=item, user=request.user, wished=False
    )
    wish_qs = Wishlist.objects.filter(user=request.user, wished=False)
    if wish_qs.exists():
        wish = wish_qs[0]

        if wish.items.filter(item__slug=item.slug).exists():
            wish_item.quantity += 1
            wish_item.save()
            messages.info(request, "This item is already in your wishlist.")
            return redirect("core:wishlist")
        else:
            wish.items.add(wish_item)
            messages.info(request, "This item was added to your wishlist.")
            return redirect("core:wishlist")
    else:
        wished_date = timezone.now()
        wish = Wishlist.objects.create(user=request.user, wish_date=wished_date)
        wish.items.add(wish_item)
        messages.info(request, "This item was added to your wishlist.")
        return redirect("core:wishlist")


@login_required
def remove_from_wishlist(request, slug):
    item = get_object_or_404(Item, slug=slug)
    wish_qs = Wishlist.objects.filter(user=request.user, wished=False)
    if wish_qs.exists():
        wish = wish_qs[0]
        # check if the order item is in the order
        if wish.items.filter(item__slug=item.slug).exists():
            wish_item = WishlistItem.objects.filter(
                item=item, user=request.user, wished=False
            )[0]
            wish.items.remove(wish_item)
            messages.info(request, "This item was removed from your wishlist.")
            return redirect("core:wishlist")
        else:
            messages.info(request, "This item was not in your wishlist")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active wishlist")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_wishlist(request, slug):
    item = get_object_or_404(Item, slug=slug)
    wish_qs = Wishlist.objects.filter(user=request.user, wished=False)
    if wish_qs.exists():
        wish = wish_qs[0]
        # check if the order item is in the order
        if wish.items.filter(item__slug=item.slug).exists():
            wish_item = WishlistItem.objects.filter(
                item=item, user=request.user, wisheed=False
            )[0]
            if wish_item.quantity > 1:
                wish_item.quantity -= 1
                wish_item.save()
            else:
                wish.items.remove(wish_item)
            messages.info(request, "Item removed.")
            return redirect("core:wishlist")
        else:
            messages.info(request, "This item was not in your wishlist")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active wishlist")
        return redirect("core:product", slug=slug)


# -------------CART-------------------------


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


@login_required
def add_to_cart_quantity(request, slug):
    print(request)

    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if request.method == "POST":
        # get the input values from the form
        quantity = int(request.POST.get("quantity"))
        print(quantity)
        submitbutton = request.POST.get("submit")

        if order_qs.exists():
            order = order_qs[0]
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                order_item.quantity += quantity
                order_item.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("http://127.0.0.1:8000/product/" + item.slug)
            else:

                order.items.add(order_item)
                order_item.quantity = quantity
                order_item.save()
                # order_item.quantity += (quantity - 1)
                messages.info(request, "This item was added to your cart.")
                return redirect("http://127.0.0.1:8000/product/" + item.slug)
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)

            order.items.add(order_item)
            order_item.quantity = quantity
            order_item.save()
            messages.info(request, "This item was added to your cart.")
            return redirect("http://127.0.0.1:8000/product/" + item.slug)
    return redirect("http://127.0.0.1:8000/product/" + item.slug)


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get("code")
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {"form": form}
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get("ref_code")
            message = form.cleaned_data.get("message")
            email = form.cleaned_data.get("email")
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")


@login_required
def remove_all_from_cart(request):

    olist = OrderItem.objects.all()
    print(olist)
    for i in olist:
        if i.user == request.user:
            print("same")
            i.delete()

    print(olist)

    # check if the order item is in the order

    messages.info(request, "Thank you for the order!Order again!")
    return redirect("/")
