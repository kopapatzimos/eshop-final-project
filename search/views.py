from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.db.models import Q
from core.models import Item


def searchposts(request):
    template_name = "home.html"
    if request.method == "GET":
        query = request.GET.get("q")

        submitbutton = request.GET.get("submit")

        if query is not None:
            lookups = (
                Q(title__icontains=query)
                | Q(category__icontains=query)
                | Q(tags__slug__icontains=query)
            )
            results = Item.objects.filter(lookups).distinct().order_by("price")

            context = {"results": results, "submitbutton": submitbutton}

            return render(request, template_name, context)

        else:
            return render(request, template_name)

    else:
        return render(request, template_name)
