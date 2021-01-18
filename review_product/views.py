from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, render, redirect
from django.forms import ModelForm, Textarea
from .models import Review
from core.models import Item
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import numpy as np
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages


import datetime


class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {"comment": Textarea(attrs={"cols": 40, "rows": 5})}


@login_required
def review_list(request):

    context = {"latest_review_list": latest_review_list}
    return render(request, "review_list.html", context)


def review_detail(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    return render(request, "review_detail.html", {"review": review})


def item_list(request):
    item_list = Item.objects.order_by("-name")
    context = {"item_list": item_list}
    return render(request, "item_list.html", context)


def item_detail(request, item_id):

    item = get_object_or_404(Item, pk=item_id)
    tags = item.tags.slugs()

    lookups = Q(tags__slug__icontains=tags)
    results = Item.objects.filter(lookups).distinct()
    print(results)
    print(item.slug)
    return render(
        request, "product.html", {"item": item, "tags": tags, "tapanta": results}
    )


@login_required
def add_review(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    slug = item.slug
    form = ReviewForm(request.POST)
    if form.is_valid():
        rating = form.cleaned_data["rating"]
        comment = form.cleaned_data["comment"]
        # user_name = form.cleaned_data['user_name']
        review = Review()
        review.item = item
        # review.url = item.url
        review.user_name = request.user
        review.rating = rating
        review.comment = comment
        review.pub_date = datetime.datetime.now()
        review.save()
        messages.info(request, "Your review posted succesfully ")
        return redirect("/product/" + slug)

    return render(request, "product.html", {"item": item, "form": form})
