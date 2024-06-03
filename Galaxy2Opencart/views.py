from django.http import JsonResponse
from . import products
from . import orders
from . import categories
from . import image
from . import balance
from . import init
from .models import UserAnswer
from .forms import UserAnswerForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import ConsoleMessage
from django.views.decorators.csrf import csrf_exempt
import os
import json
from django.http import HttpResponseRedirect
from django.urls import reverse



def main_page(request):
    return render(request, 'Galaxy2Opencart/main.html')

# Products View
def products_view(request):
    products.run_import()
    return render(request, 'Galaxy2Opencart/products_view.html')


# Orders View
def orders_view(request):
    if request.method == "POST":
        orders.run_import()
    return render(request, 'Galaxy2Opencart/orders_view.html')

# Categories View

def categories_view(request):
    if request.method == "POST":
#        user_answers = {
#            "store_domain": request.POST.get("store_domain"),
#            "store_path": request.POST.get("store_path"),
 #           "erp_server_ip": request.POST.get("erp_server_ip"),
#            "erp_server_port": request.POST.get("erp_server_port"),
 #           "erp_username": request.POST.get("erp_username"),
 #           "erp_password": request.POST.get("erp_password"),
 #           "woo_consumer_key": request.POST.get("woo_consumer_key"),
 #           "woo_consumer_secret": request.POST.get("woo_consumer_secret"),
  #      }
        results = categories.run_import()
        if results:
            messages.success(request, 'Categories imported successfully!')
        else:
            messages.error(request, 'There was an error importing categories.')
    return render(request, 'Galaxy2Opencart/categories_view.html')

def image_view(request):
    if request.method == "POST":
        results = image.run_import()
        if results:
            messages.success(request, 'Images imported successfully!')
        else:
            messages.error(request, 'There was an error importing images.')
    return render(request, 'Galaxy2Opencart/image_view.html')

def balance_view(request):
    if request.method == "POST":
        balance.run_import()
    return render(request, 'Galaxy2Opencart/balance_view.html')

#def init_view(request):
#    if request.method == "POST":
#        user_answers = {
#            "store_domain": request.POST.get("store_domain"),
#            "store_path": request.POST.get("store_path"),
#            "erp_server_ip": request.POST.get("erp_server_ip"),
#            "erp_server_port": request.POST.get("erp_server_port"),
#            "erp_username": request.POST.get("erp_username"),
#            "erp_password": request.POST.get("erp_password"),
#            "woo_consumer_key": request.POST.get("woo_consumer_key"),
#            "woo_consumer_secret": request.POST.get("woo_consumer_secret"),
#        }
#        results = init.run_import(user_answers)
#        if results:
#            messages.success(request, 'Initialized ERP Company Data successfully!')
#        else:
#            messages.error(request, 'There was an error initializing Company Data.')
#    return render(request, 'Galaxy2Opencart/orders_form.html')

def answer_form_view(request):
    if request.method == 'POST':
        form = UserAnswerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_page')
    else:
        user_answer = UserAnswer.objects.latest('id')
        form = UserAnswerForm(instance=user_answer)

    return render(request, 'Galaxy2Opencart/answer_form.html', {'form': form})

def get_latest_messages(request):
    with open('logs.json', 'r') as f:
        log_entries = [json.loads(line) for line in f.readlines()]
    # Optionally filter, paginate, or limit the number of entries you send
    return JsonResponse(log_entries, safe=False)

def clear_logs(request):
    log_file = "logs.json"
    if os.path.exists(log_file):
        os.remove(log_file)
    return HttpResponseRedirect(reverse('main_page'))



def main_page(request):
    return render(request, 'Galaxy2Opencart/main.html')