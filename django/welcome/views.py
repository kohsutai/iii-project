from django.shortcuts import render

# Create your views here.
def index(request):
  return HttpResponse("Hello, Django. Nice to meet u.")
