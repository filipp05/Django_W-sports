from django import forms
from django.contrib.auth import get_user_model
from .models import Category, Product, Address, ShippingMethod, PaymentMethod, Cart, ProductAttributeValue, \
    ProductAttribute, Rent  # VariantsAttributeValue
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


class InlineProductAttributeValueForm(forms.ModelForm):
    attribute_name = forms.CharField(label="Название атрибута", required=False)
    value = forms.CharField(label="Значение", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attribute_id = self["attribute"].initial
        if not attribute_id:
            return

        attribute = ProductAttribute.objects.get(id=attribute_id)
        attribute_value = kwargs["instance"]
        self["attribute_name"].initial = attribute.name
        self.fields["attribute_name"].widget.attrs["disabled"] = "disabled"
        if attribute.type == ProductAttribute.AttributeType.BOOLEAN:
            self.fields["value"] = forms.BooleanField(required=False)
            self["value"].initial = attribute_value.bool_value
        elif attribute.type == ProductAttribute.AttributeType.INT:
            self.fields["value"] = forms.IntegerField(required=False)
            self["value"].initial = attribute_value.int_value
        elif attribute.type == ProductAttribute.AttributeType.FLOAT:
            self.fields["value"] = forms.FloatField(required=False)
            self["value"].initial = attribute_value.float_value
        elif attribute.type == ProductAttribute.AttributeType.VARIANTS:
            self.fields["value"] = forms.ChoiceField(required=False)
            self.fields["value"].choices = [(item, item) for item in
                                            attribute.choosableattributeoptions_set.values_list("value", flat=True)]
            self["value"].initial = attribute_value.str_value
        elif attribute.type == ProductAttribute.AttributeType.STRING:
            self.fields["value"] = forms.CharField(required=False)
            self["value"].initial = attribute_value.str_value

    def save(self, commit=True):
        attribute_value = super().save(commit=False)
        attribute = self.cleaned_data["attribute"]
        if attribute.type == ProductAttribute.AttributeType.INT:
            attribute_value.int_value = self.cleaned_data["value"]
        elif attribute.type == ProductAttribute.AttributeType.FLOAT:
            attribute_value.float_value = self.cleaned_data["value"]
        elif attribute.type == ProductAttribute.AttributeType.STRING:
            attribute_value.str_value = self.cleaned_data["value"]
        elif attribute.type == ProductAttribute.AttributeType.BOOLEAN:
            attribute_value.bool_value = self.cleaned_data["value"]
        elif attribute.type == ProductAttribute.AttributeType.VARIANTS:
            attribute_value.str_value = self.cleaned_data["value"]

        attribute_value.save()

    class Meta:
        model = ProductAttributeValue
        fields = ("attribute",)
        widgets = {"attribute": forms.HiddenInput(), }


class ProductAttributeForm(forms.ModelForm):
    def _save_m2m(self, *args, **kwargs):
        super()._save_m2m(*args, **kwargs)
        product_list = Product.objects.filter(categories__in=self.instance.categories.all())
        for product in product_list:
            if not ProductAttributeValue.objects.filter(product=product, attribute=self.instance).exists():
                ProductAttributeValue.objects.create(product=product, attribute=self.instance)

    class Meta:
        model = ProductAttribute
        fields = "__all__"


class ProductRentForm(forms.ModelForm):
    class Meta:
        model = Rent
        fields = ("duration", "rules_acception")


class CoordsForm(forms.Form):
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())


# class InlineVariantAttributeValueForm(InlineProductAttributeValueForm):
#     # count = forms.IntegerField(min_value=0)
#
#     class Meta(InlineProductAttributeValueForm.Meta):
#         model = VariantsAttributeValue
#         fields = ("attribute", )


class CityForm(forms.Form):
    city = forms.CharField()


class SearchForm(forms.Form):
    request_string = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control mr-sm-2"}), label="")
