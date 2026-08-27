from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Member


@login_required
def business_card(request, pk):
    member = get_object_or_404(Member, pk=pk)
    return render(request, 'members/business_card.html', {'member': member})
