from django import forms
from django.contrib.auth import get_user_model
from .models import Category, Product, Address, ShippingMethod, PaymentMethod, Cart
from django.forms.utils import ErrorList

Customer = get_user_model()


class ProductForm(forms.Form):
    name = forms.CharField(label='Название')
    price = forms.FloatField(label='Цена')
    photo = forms.ImageField(label='Фото')
    category = forms.ModelChoiceField(queryset=None, label='Категория')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()


# class PurchaseModelForm(forms.ModelForm):
#     class Meta:
#         model = Purchase
#         exclude = ['customer', 'date']


class CustomerForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput())

    def is_valid(self, *args, **kwargs):
        super(CustomerForm, self).is_valid(*args, **kwargs)

        if self.cleaned_data['password'] != self.cleaned_data['password1']:
            self.errors['password'] = ErrorList(['введенные пароли не одинаковы'])
            return False
        return True

    class Meta:
        model = Customer
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password', 'password1']
        widgets = {'phone': forms.TextInput(attrs={'pattern': '\+?\d{11}', 'placeholder': '+79650000000'})}


class AddressForm(forms.ModelForm):
    street = forms.CharField(required=False)
    city = forms.CharField(required=False)
    house = forms.CharField(required=False)
    flat = forms.CharField(required=False)
    contact = forms.CharField(required=False)
    extra_phone = forms.CharField(required=False)

    class Meta:
        model = Address
        fields = ["street", 'city', 'house', 'flat', 'contact', 'extra_phone', ]
        widgets = {'extra_phone': forms.TextInput(attrs={'pattern': '\+?\d{11}', 'placeholder': '+79650000000'})}


# class ShippingMethodForm(forms.ModelForm):
#     class Meta:
#         model = ShippingMethod
#         fields = '__all__'
# #        widgets = {'name': forms.RadioSelect()}
#
#
# class PaymentMethodForm(forms.ModelForm):
#     class Meta:
#         model = PaymentMethod
#         fields = '__all__'


class CheckoutForm(forms.ModelForm):
    shipping_method = forms.ModelChoiceField(queryset=ShippingMethod.objects.all(), widget=forms.RadioSelect(),
                                             empty_label=None)
    payment_method = forms.ModelChoiceField(queryset=PaymentMethod.objects.all(), widget=forms.RadioSelect(),
                                            empty_label=None)

    class Meta:
        model = Cart
        fields = ['shipping_method', 'payment_method']






















