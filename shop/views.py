from django.db.models import F, ExpressionWrapper, FloatField, Sum, Count
from django.db import connection
from django.shortcuts import render, redirect, reverse
from .models import Product, Category, Brand, Customer, Cart, ProductCart, Address, ShippingMethod, PaymentMethod, \
    ProductAttribute
from .forms import ProductForm, CustomerForm, AddressForm, CheckoutForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.forms import formset_factory, modelformset_factory
from hashlib import md5
import requests
from django.http import HttpResponse
from django.http.response import Http404


def index(request):
    latest_product_list = Product.objects.only('name', 'description', 'price').order_by('-published')[:3]
    category_list = Category.objects.all()
    brand_list = Brand.objects.only('name', 'description').all()
    print(brand_list.query, latest_product_list.query)
    return render(request, 'index.html', {'category_list': category_list, 'brand_list': brand_list, 'product_list': latest_product_list})


def brand_products(request, brand_name):
    current_brand = Brand.objects.get(name=brand_name)
    brand_product_list = Product.objects.filter(brand=current_brand)
    return render(request, 'branded.html', {'product_list': brand_product_list, 'current_brand': current_brand})


def category_products(request, category_name):
    current_category = Category.objects.get(name=category_name)
    category_product_list = Product.objects.filter(category=current_category)
    return render(request, 'categorical.html', {'product_list': category_product_list,
                                                'current_category': current_category})


def product_detail(request, product_name, ):
    #    if not request.user.is_authenticated:
    #        return redirect("/accounts/login/?next=/product/" + product_name + "/")
    product = Product.objects.only('description', 'price', 'count', 'name', 'photo', 'brand', 'category')\
                            .select_related('brand', 'category')\
                            .prefetch_related('recommendations', 'attribute_values')\
                            .get(name=product_name)
    return render(request, 'product_detail.html', {'product': product,})


# def test_form(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             Product.objects.create(name=form.cleaned_data['name'], price=form.cleaned_data['price'],
#                                    photo=form.cleaned_data['photo'], category=form.cleaned_data['category'])
#             return redirect(reverse('Wsports:index_url'))
#     else:
#         form = ProductForm()
#     return render(request, 'test_form.html', {'form': form})


def test_model_form(request):
    ProductFormSet = formset_factory(ProductForm, extra=3)
    form_set = ProductFormSet()
    #     if request.method == 'POST':
    #         form = PurchaseModelForm(request.POST)
    #         if form.is_valid():
    #             purchase = form.save(commit=False)
    #             purchase.customer = request.user
    #             purchase.save()
    #         else:
    #             print(form.errors)
    #     else:
    #         form = PurchaseModelForm()
    return render(request, 'test_form.html', {'form_set': form_set})


def register(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.set_password(form.cleaned_data['password'])
            customer.save()
            user = authenticate(username=customer.username, password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
            return redirect('/')
        else:
            print(form.errors)
    else:
        form = CustomerForm()
    return render(request, 'registration/register.html', {'form': form})


def get_cart(user):
    current_user_carts = user.cart_list.filter(is_paid=False).order_by('-created_at')
    if current_user_carts:
        current_cart = current_user_carts[0]
    else:
        current_cart = Cart.objects.create(owner=user)
    return current_cart


@login_required
def add_to_cart(request, product_id):
    current_cart = get_cart(request.user)
    product = Product.objects.get(id=product_id)
    try:
        product_cart = ProductCart.objects.get(cart=current_cart, product=product)
        product_cart.count += 1
        product_cart.save()
    except ProductCart.DoesNotExist:
        product_cart = ProductCart.objects.create(cart=current_cart, product=product)
    return redirect(reverse('Wsports:cart_url'))

    # reverse вычисляет по названию урла адрес


@login_required
def cart(request):
    cart = get_cart(request.user)
    product_set = cart.products.annotate(ordered_count=F('productcart__count'), amount=ExpressionWrapper(F('price') * F('ordered_count'),
                                                                                            FloatField())).all()
    return render(request, 'cart.html', {'cart': cart, 'product_set': product_set})
    # aggregate вычисляет на основе значений запроса конкретные результаты и возвращает только их
    # annotate добавляет вычисленного значения в обЪекту модели при выполнении запроса
    # ExpressionWrapper и его атрибут output_field созданы для корректного вывода и явного преобразования(таких куча)


@login_required
def shipping_and_payment(request):
    cart = get_cart(request.user)

    address = None
    if request.method == 'POST':
        checkout_form = CheckoutForm(data=request.POST, instance=cart)
        if checkout_form.is_valid():
            if 'existing_address' in request.POST and request.POST['existing_address']\
                    and checkout_form.cleaned_data['shipping_method'] != ShippingMethod.objects.get(name='Самовывоз'):
                address = Address.objects.get(id=request.POST['existing_address'])
            elif checkout_form.cleaned_data['shipping_method'] != ShippingMethod.objects.get(name='Самовывоз'):
                address_form = AddressForm(request.POST)
                if address_form.is_valid():
                    address = address_form.save(commit=False)
                    address.customer = request.user
                    address.save()

            if address:
                cart = checkout_form.save(commit=False)
                cart.address = address
                cart.save()
            else:
                checkout_form.save()
            return redirect(reverse('Wsports:checkout_url'))
    else:
        address_form = AddressForm()

#        payment_form = PaymentMethodForm()
#        shipping_form = ShippingMethodForm()
#        shipping_formset = modelformset_factory(model=ShippingMethod, form=ShippingMethodForm, extra=0)
        checkout_form = CheckoutForm()

    # Address.objects.filter(customer=request.user)
    address_list = request.user.address_set.all()
    return render(request, 'shipping_and_payment.html',
                  {
                      'address_form': address_form,
                      'products': cart.products.all(),
                      'address_list': address_list,
                      'checkout_form': checkout_form,
                  })


@login_required
def delete_from_cart(request, product_id):
    cart = get_cart(request.user)
    current_product = cart.products.get(id=product_id)
    cart.products.remove(current_product)
# remove для поля ManyToMany удаляет из списка связанных объектов переданный объект
    return redirect(reverse('Wsports:cart_url'))


@login_required
def change_count(request, product_id, count):
    cart = get_cart(request.user)
    current_product = cart.products.get(id=product_id)
    product_cart = ProductCart.objects.get(cart=cart, product=current_product)

    if product_cart.count == 1 and int(count) == -1:
        return redirect(reverse('Wsports:product_delete_url', kwargs={'product_id': product_id}))

    product_cart.count = F('count') + int(count)
    product_cart.save()
    return redirect(reverse('Wsports:cart_url'))


@login_required
def checkout(request):
    cart = get_cart(request.user)
    url = 'https://auth.robokassa.ru/Merchant/Index.aspx'
    login = 'Wsports.ru'
    summ = cart.get_total_amount()
    order_num = cart.id
    description = 'Оплата покупки в магазине Wsports'
    pass_1 = '7997119email'
    controll_summ = md5(bytes("{0}:{1}:{2}:{3}".format(login, str(summ), str(order_num), pass_1), 'UTF-8'))

    # response = requests.post(url, data={
    #     'MerchantLogin': login,
    #     'OutSum': summ,
    #     'InvoiceId': order_num,
    #     'Description': description,
    #     'SignatureValue': controll_summ.hexdigest(),
    #     'lsTest': 1,
    # })
    payment_url = f"{url}?MerchantLogin={login}&OutSum={summ}&InvoiceID={order_num}&Description={description}&SignatureValue={controll_summ.hexdigest()}&IsTest=1"

    product_set = cart.products.annotate(ordered_count=F('productcart__count'), amount=ExpressionWrapper(F('price') * F('count'),
                                                                                            FloatField())).all()
    shipping_method = cart.shipping_method
    payment_method = cart.payment_method
    address = cart.address
    return render(request, 'checkout.html',
                  {
                      'cart': cart,
                      'shipping_method': shipping_method,
                      'payment_method': payment_method,
                      'address': address,
                      'product_set': product_set,
                      'payment_url': payment_url,
                  })


@login_required
def purchase(request):
    cart = get_cart(user=request.user)
    cart.is_checkouted = True
    cart.save()
    return render(request, 'purchase.html',
                {
                        'cart': cart,
                })


@login_required
def payment_success(request):

    if request.method != 'GET':
        return render(request, 'success.html', {'error': 'Что-то пошло не по плану с оплатой'})

    pass1 = '7997119email'
    summ = request.GET['OutSum']
    order_num = request.GET['InvId']
    control_summ = request.GET['SignatureValue']
    rb_control_summ = md5("{0}:{1}:{2}".format(summ, order_num, pass1).encode('UTF-8')).hexdigest()

    if control_summ != rb_control_summ:
        return render(request, 'success.html', {'error': 'Что-то пошло не по плану с оплатой'})

    return render(request, 'success.html', {'cart': cart})


@login_required
def payment_failure(request):
    if request.method != 'GET':
        return render(request, 'success.html', {'error': 'Что-то пошло не по плану с оплатой'})

    inv_order_num = request.GET["InvId"]
    return render(request, 'payment_failure.html', {'order': inv_order_num})


def payment_result(request):
    pass2 = '7997119ymail'
    summ = request.GET['OutSum']
    order_num = request.GET['InvId']
    control_summ = request.GET['SignatureValue']
    rb_control_summ = md5("{0}:{1}:{2}".format(summ, order_num, pass2).encode('UTF-8')).hexdigest()

    if control_summ != rb_control_summ:
        return HttpResponse(content="", status=400)

    cart = get_cart(user=request.user)
    cart.is_paid = True
    cart.save()
    products_to_update = []

    for product in cart.products.all():
        product.count -= ProductCart.objects.get(product=product, cart=cart).count
        products_to_update.append(product)
    Product.objects.bulk_update(products_to_update, fields=('count',))

    return HttpResponse(content="", status=200)


@login_required
def profile(request):
    cart = get_cart(user=request.user)
    return render(request, 'profile.html', {'cart': cart})


def get_attribute_format(request):
    if request.is_ajax and "id" in request.GET:
        attribute = ProductAttribute.objects.get(id=request.GET["id"])
        return HttpResponse(attribute.type)
    return Http404("Not found...")

# TODO: в шаблоне чекаута переделать вывод заказанного количества товаров - все остальное работает корректно
# TODO: на странице продукта выводить атрибуты со значениями для данного продукта
# TODO: взять сторонний сервис с погодой для рекомендаций продуктов


