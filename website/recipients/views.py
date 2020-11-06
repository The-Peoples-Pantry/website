from django.shortcuts import render


def index(request):
    return render(request, 'recipients/index.html')


def new(request):
    return render(request, 'recipients/new.html')
