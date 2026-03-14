# home/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url='/accounts/login/')
def home_view(request):
    return render(request, 'home/home.html', {'user': request.user})