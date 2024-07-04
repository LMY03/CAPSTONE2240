from django.shortcuts import render

# Create your views here.
def renders(request):
    return render(request, 'data.html')