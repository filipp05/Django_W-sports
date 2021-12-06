import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, ExpressionWrapper, FloatField, Sum, Count, Prefetch, Q
from django.db import connection
from django.shortcuts import render, redirect, reverse
from django.views import View

from .models import Product, Category, Brand, Customer, Cart, Order, Address, ShippingMethod, PaymentMethod, \
    ProductAttribute, ProductVariant, AttributeValue, VariantsAttributeValue, Rent
from .forms import ProductForm, CustomerForm, AddressForm, CheckoutForm, ProductRentForm, CityForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.forms import formset_factory, modelformset_factory
from hashlib import md5
import requests
from django.http import HttpResponse
from django.http.response import Http404

from .utils import get_product_variant


class IndexView(View):
    def get(self, request):
        latest_product_list = Product.objects.only('name', 'description', 'price').order_by('-published')[:3]
        category_list = Category.objects.all()
        brand_list = Brand.objects.only('name', 'description').all()
        print(brand_list.query, latest_product_list.query)
        form = CityForm()
        return render(request, 'index.html',
                      {'category_list': category_list, 'brand_list': brand_list, 'product_list': latest_product_list,
                       "city_form": form})


class BrandProductsView(View):
    def get(self, request, brand_name):
        current_brand = Brand.objects.prefetch_related("product_set").get(name=brand_name)
        # brand_product_list = Product.objects.filter(brand=current_brand)
        brand_categories = Category.objects.filter(product__brand=current_brand).distinct()
        print(brand_categories)
        return render(request, 'branded.html', {'current_brand': current_brand,
                                                "category_list": brand_categories})


class CategoryProductsView(View):
    def get(self, request, category_name):
        current_category = Category.objects.get(name=category_name)
        category_product_list = Product.objects.filter(categories=current_category)
        return render(request, 'categorical.html', {'product_list': category_product_list,
                                                    'current_category': current_category})


class ProductDetailView(View):
    def get(self, request, product_name):
        product = Product.objects.only('description', 'price', 'name', 'photo', 'brand', 'categories') \
            .select_related('brand') \
            .prefetch_related('recommendations', 'attribute_values', "productvariant_set", "categories") \
            .annotate(count=Sum("productvariant__count")) \
            .get(name=product_name)
        return render(request, 'product_detail.html', {'product': product, })


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


class RegisterView(View):
    def get(self, request):
        form = CustomerForm()
        return render(request, 'registration/register.html', {'form': form})

    def post(self, request):
        form = CustomerForm(request.POST)

        if form.is_valid():
            customer = form.save(commit=False)
            customer.set_password(form.cleaned_data['password'])
            customer.save()
            user = authenticate(username=customer.username, password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
            return redirect('/')


class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        current_cart = Cart.get_current_cart(request.user)

        variant = get_product_variant(request.POST, product_id)
        print(request.POST, product_id)
        if not variant:
            return redirect(
                reverse("Wsports:product_url", kwargs={"product_name": Product.objects.get(id=product_id).name}))

        try:
            product_cart = Order.objects.get(cart=current_cart, product_variant=variant)
            product_cart.count += 1
            product_cart.save()
        except Order.DoesNotExist:
            product_cart = Order.objects.create(cart=current_cart, product_variant=variant)

        return redirect(reverse('Wsports:cart_url'))


class CartView(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart.get_current_cart(request.user)
        order_set = Order.objects.filter(cart=cart) \
            .annotate(amount=ExpressionWrapper(F('product_variant__product__price') * F('count'), FloatField())) \
            .prefetch_related(Prefetch("product_variant", ProductVariant.objects.prefetch_related(
            Prefetch("variant_values", VariantsAttributeValue.objects.filter(product_variant=F("product_variant")) \
                     .annotate(value=F("str_value"))))))
        return render(request, 'cart.html', {'cart': cart, 'order_set': order_set})
        # aggregate вычисляет на основе значений запроса конкретные результаты и возвращает только их
        # annotate добавляет вычисленного значения в обЪекту модели при выполнении запроса
        # ExpressionWrapper и его атрибут output_field созданы для корректного вывода и явного преобразования(таких куча)


class ShippingAndPaymentView(LoginRequiredMixin, View):

    def get(self, request, address_form=None, checkout_form=None):
        cart = Cart.get_current_cart(request.user)

        if not address_form and not checkout_form:
            address_form = AddressForm()
            checkout_form = CheckoutForm()

        address_list = request.user.address_set.all()
        return render(request, 'shipping_and_payment.html',
                      {
                          'address_form': address_form,
                          'products': cart.products_variants.all(),
                          'address_list': address_list,
                          'checkout_form': checkout_form,
                      })

    def post(self, request):
        cart = Cart.get_current_cart(request.user)
        checkout_form = CheckoutForm(data=request.POST, instance=cart)
        address_form = AddressForm(request.POST)
        if checkout_form.is_valid():
            address = None
            if 'existing_address' in request.POST and request.POST['existing_address'] \
                    and checkout_form.cleaned_data['shipping_method'] != ShippingMethod.objects.get(name='Самовывоз'):
                address = Address.objects.get(id=request.POST['existing_address'])
            elif checkout_form.cleaned_data['shipping_method'] != ShippingMethod.objects.get(name='Самовывоз'):
                if address_form.is_valid():
                    address = address_form.save(commit=False)
                    address.customer = request.user
                    address.save()
                else:
                    return self.get(request, address_form=address_form, checkout_form=checkout_form)

            if address:
                cart = checkout_form.save(commit=False)
                cart.address = address
                cart.save()
            else:
                checkout_form.save()
            return redirect(reverse('Wsports:checkout_url'))
        return self.get(request, address_form=address_form, checkout_form=checkout_form)


# как тут написать класс оптимально, чтобы вызов корзины не повторялся и тд???????


class DeleteFromCartView(LoginRequiredMixin, View):
    def get(self, request, product_variant_id):
        cart = Cart.get_current_cart(request.user)
        current_product_variant = cart.products_variants.get(id=product_variant_id)
        cart.products_variants.remove(current_product_variant)
        # remove для поля ManyToMany удаляет из списка связанных объектов переданный объект ((add или remove))
        return redirect(reverse('Wsports:cart_url'))


class ChangeCountView(LoginRequiredMixin, View):
    def get(self, request, product_variant_id, count):
        cart = Cart.get_current_cart(request.user)
        order = Order.objects.get(cart=cart, product_variant__id=product_variant_id)

        if order.count == 1 and int(count) == -1:
            return redirect(reverse('Wsports:product_delete_url', kwargs={'product_variant_id': product_variant_id}))

        order.count = F('count') + int(count)
        order.save()
        return redirect(reverse('Wsports:cart_url'))


class CheckoutView(View, LoginRequiredMixin):
    def get(self, request):
        cart = Cart.get_current_cart(request.user)
        url = 'https://auth.robokassa.ru/Merchant/Index.aspx'
        login = 'Wsports.ru'
        summ = cart.get_total_amount()
        order_num = cart.id
        description = 'Оплата покупки в магазине Wsports'
        pass_1 = '7997119email'
        controll_summ = md5(bytes("{0}:{1}:{2}:{3}".format(login, str(summ), str(order_num), pass_1), 'UTF-8'))

        if not cart.payment_method.is_online:
            payment_url = reverse("Wsports:order_finish_url")
        else:
            payment_url = f"{url}?MerchantLogin={login}&OutSum={summ}&InvoiceID={order_num}&Description={description}&SignatureValue={controll_summ.hexdigest()}&IsTest=1"

        product_variant_set = cart.products_variants.annotate(ordered_count=F('order__count'), amount=ExpressionWrapper(
            F('product__price') * F('order__count'),
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
                          'product_variant_set': product_variant_set,
                          'payment_url': payment_url,
                      })


class PurchaseView(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart.get_current_cart(user=request.user)
        cart.is_checkouted = True
        cart.save()
        return render(request, 'purchase.html',
                      {
                          'cart': cart,
                      })


class PaymentSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        pass1 = '7997119email'
        summ = request.GET['OutSum']
        order_num = request.GET['InvId']
        control_summ = request.GET['SignatureValue']
        rb_control_summ = md5("{0}:{1}:{2}".format(summ, order_num, pass1).encode('UTF-8')).hexdigest()

        if control_summ != rb_control_summ:
            return render(request, 'success.html', {'error': 'Что-то пошло не по плану с оплатой'})

        cart = Cart.get_current_cart(user=request.user)
        cart.is_paid = True
        cart.save()

        return redirect(reverse("Wsports:order_finish_url"))


class PaymentSuccessView(LoginRequiredMixin, View):
    def post(self, request):
        return render(request, 'success.html', {'error': 'Что-то пошло не по плану с оплатой'})

    # pass1 = '7997119email'
    # summ = request.GET['OutSum']
    # order_num = request.GET['InvId']
    # control_summ = request.GET['SignatureValue']
    # rb_control_summ = md5("{0}:{1}:{2}".format(summ, order_num, pass1).encode('UTF-8')).hexdigest()
    #
    # if control_summ != rb_control_summ:
    #     return render(request, 'success.html', {'error': 'Что-то пошло не по плану с оплатой'})
    #
    # cart = get_cart(user=request.user)
    # cart.is_paid = True
    # cart.save()
    #
    # return redirect(reverse("Wsports:order_finish_url"))


class OrderFinishView(View):
    def get(self, request):
        cart = Cart.get_current_cart(user=request.user)
        cart.is_checkouted = True
        cart.save()
        return render(request, 'success.html', {'cart': cart})


# def order_finish(request):
#     cart = get_cart(user=request.user)
#     cart.is_checkouted = True
#     cart.save()
#     return render(request, 'success.html', {'cart': cart})


class PaymentFailureView(LoginRequiredMixin, View):
    def get(self, request):
        inv_order_num = request.GET["InvId"]
        return render(request, 'payment_failure.html', {'order': inv_order_num})


class PaymentFailure(LoginRequiredMixin, View):
    def post(self, request):
        return render(request, 'success.html', {'error': 'Что-то пошло не по плану с оплатой'})

    def get(self, request):
        inv_order_num = request.GET["InvId"]
        return render(request, 'payment_failure.html', {'order': inv_order_num})


class PaymentResultView(View):
    def get(self, request):
        pass2 = '7997119ymail'
        summ = request.GET['OutSum']
        order_num = request.GET['InvId']
        control_summ = request.GET['SignatureValue']
        rb_control_summ = md5("{0}:{1}:{2}".format(summ, order_num, pass2).encode('UTF-8')).hexdigest()

        if control_summ != rb_control_summ:
            return HttpResponse(content="", status=400)

        cart = Cart.get_current_cart(user=request.user)
        cart.is_paid = True
        cart.save()
        products_to_update = []

        for product in cart.products.all():
            product.count -= Order.objects.get(product=product, cart=cart).count
            products_to_update.append(product)
        Product.objects.bulk_update(products_to_update, fields=('count',))

        return HttpResponse(content="", status=200)


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        carts = Cart.objects.filter(owner=request.user, is_checkouted=True) \
            .prefetch_related(
            Prefetch("order_set", Order.objects.prefetch_related(Prefetch("product_variant", ProductVariant.objects \
                                                                          .prefetch_related(
                Prefetch("variant_values", VariantsAttributeValue.objects.filter(product_variant=F("product_variant")) \
                         .annotate(value=F("str_value")))))))) \
            .order_by("-created_at")
        rent_set = Rent.objects.filter(customer=request.user).exclude(status=Rent.RentStatus.returned).order_by(
            "-begin_date")
        return render(request, 'profile.html', {'carts': carts, 'rent_set': rent_set})


class GetAttributeFormatView(View):
    def get(self, request):
        if request.is_ajax and "id" in request.GET:
            attribute = ProductAttribute.objects.get(id=request.GET["id"])
            return HttpResponse(attribute.type)
        return Http404("Not found...")


class RentProductView(View):
    def get(self, request, product_id):
        variant = get_product_variant(request.POST, product_id)
        form = ProductRentForm()

        # Rent.objects.create(customer=request.user, product_variant=variant, durations)

        return render(request, "rent.html", {"variant": variant, "form": form})


class AcceptProductRentView(View):
    def post(self, request, product_variant_id):
        form = ProductRentForm(request.POST)
        if form.is_valid():
            rent = form.save(commit=False)
            rent.customer = request.user
            rent.product_variant = ProductVariant.objects.get(id=product_variant_id)
            rent.save()
            return redirect(reverse("Wsports:profile"))
        else:
            print(form.errors)

        raise Http404("<h1>Упс, этой страницы не существует. <a href='/'>Перейти на главную</a></h1>")


# def accept_product_rent(request, product_variant_id):
#     if request.method == "POST":
#         form = ProductRentForm(request.POST)
#         if form.is_valid():
#             rent = form.save(commit=False)
#             rent.customer = request.user
#             rent.product_variant = ProductVariant.objects.get(id=product_variant_id)
#             rent.save()
#             return redirect(reverse("Wsports:profile"))
#         else:
#             print(form.errors)
#     raise Http404("<h1>Упс, этой страницы не существует. <a href='/'>Перейти на главную</a></h1>")

class Handler404View(View):
    def get(self, request, exception):
        raise Http404("<h1>Упс, этой страницы не существует. <a href='/'>Перейти на главную</a></h1>")


# def handler404(request, exception):
#     raise Http404("<h1>Упс, этой страницы не существует. <a href='/'>Перейти на главную</a></h1>")


class DeleteAddressView(View):
    def get(self, request, address_id):
        Address.objects.get(id=address_id).delete()
        return redirect(reverse("Wsports:profile"))


class FindWeatherForecastView(View):
    def post(self, request):
        form = CityForm(request.POST)

        if form.is_valid():
            headers = {"X-Gismeteo-Token": "60ec4d1a90ce50.75601666"}
            response = requests.get(f'https://api.gismeteo.net/v2/search/cities/?query={form.cleaned_data["city"]}',
                                    headers=headers)
            city_data = response.json()

            if city_data["meta"]["code"] == "200":
                city_id = city_data["response"]["items"][0]["id"]
                weather_response = requests.get(
                    f'https://api.gismeteo.net/v2/weather/forecast/aggregate/{city_id}/?days={10}',
                    headers=headers)
                weather_data = weather_response.json()

                if weather_data['meta']['code'] == "200":
                    sum_temperature = 0
                    sum_humidity = 0  # влажность
                    sum_cloudiness = 0
                    sum_precipitation = 0  # осадки
                    sum_wind = 0

                    for data in weather_data["response"]:
                        sum_temperature += data["temperature"]["air"]["avg"]["C"]
                        sum_humidity += data["humidity"]["percent"]["avg"]
                        sum_cloudiness += data["cloudiness"]["percent"]
                        sum_precipitation += data["precipitation"]["amount"]
                        sum_wind += (data["wind"]["speed"]["min"]["m_s"] + data["wind"]["speed"]["max"]["m_s"]) / 2
                        print(data["cloudiness"]["percent"])  # ???????

                    avg_temperature_for_ten_days = sum_temperature / len(weather_data["response"])
                    avg_humidity_percent_for_ten_days = sum_humidity / len(weather_data["response"])
                    avg_cloudiness_percent_for_ten_days = sum_cloudiness / len(weather_data["response"])
                    avg_precipitation_mm_for_ten_days = sum_precipitation / len(weather_data["response"])
                    avg_wind_m_s_for_ten_days = sum_wind / len(weather_data["response"])  # Для средних значений выдается null

        return redirect('/')
# def delete_address(request, address_id):
#     Address.objects.get(id=address_id).delete()
#     return redirect(reverse("Wsports:profile"))
# TODO: взять сторонний сервис с погодой для рекомендаций продуктов
