from django.shortcuts import render
from django.contrib import messages
from .models import product, Contact, Orders, OrdersUpdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
# Create your views here.
from django.http import HttpResponse
MERCHANT_KEY = ' INTEGR7769XXXXXX9383'

def index(request):
    allProds = []
    catprods = product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)
def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False
def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod)!=0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds, "msg": ""}
    if len (allProds) == 0 or len(query)<4:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', params)


def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        if len(name) <2 or len (email) <3 or len (phone) <10 or len(desc)<4: 
            messages.error(request, "Please fill the form correctly & all fild required")
        else:
            contact = Contact(name=name, email=email, phone=phone, desc=desc)
            contact.save()
            messages.success (request, "Your message has been successfully sent by MyAwesome Cart Helps")
            thank = True
    return render(request, 'shop/contact.html', {'thank': thank})


def tracker(request):
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrdersUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"Status":"success","updates":updates, "itemsJson":order[0].items_json}, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')

    return render(request, 'shop/tracker.html')


def productView(request, myid):
    # Fetch the product using the id
    Product = product.objects.filter(id=myid)
    return render(request, 'shop/productview.html', {'product':Product[0]})

def checkout(request):
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone)
        order.save()
        update = OrdersUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'shop/checkout.html', {'thank':thank, 'id': id})
        # Request paytm to transfer the amount to your account after payment by user
        param_disc = {
             
             'MID':'your-merchant-keys-here',
             'ORDER_ID': str(order.order_id),
             'CUST_ID': email,
             'INDUSTRY_TYPE_ID': 'Retail',
             'WEBSITE': 'WEBSTAGING',
             'CHANNEL_ID': 'WEB',
             'CALLBACK_URL': 'http://127.0.0.1:8000/handlerequest/',
             
         }
        #param_disc['CHECKSUMHASH'].Checksum.generate-Checksum
        (param_disc,MERCHANT_KEY)
        return render(request, 'shop/paytm.html',{'param_disc':
             param_disc})
         
    return render(request, 'shop/checkout.html')

@csrf_exempt
def handlerequest(request):
    form = request.POST
    response_dict={}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]
    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
       if response_dict['RESPCODE'] == '01':
        print('order successful')
        a=response_dict['ORDERID']
        b=response_dict['TXNAMOUNT']
        rid=a.replace("ShopyCart","")
        print(rid)
        filter2= Orders.objects.filter(order_id=rid)
        print(filter2)
        print(a,b)
        for post1 in filter2:
            post1.oid=a
            post1.amountpaid=b
            post1.paymentstatus="PAID"
            post1.save()
        print('order was not successful because' + response_dict
              ['RESPMSG'])
    return render(request, 'shop/paymentstatus.html',{'response':
        response_dict
     })