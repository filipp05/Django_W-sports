from django import forms
from django.contrib import admin

from .forms import InlineProductAttributeValueForm, ProductAttributeForm
from .models import Category, Product, ProductPhoto, Tag, Customer, Brand, ProductAttribute, Cart, Address, \
    ProductAttributeValue, ShippingMethod, PaymentMethod, VariantsAttributeValue


class InlineProductPhoto(admin.TabularInline):
    model = ProductPhoto


class InlineProduct(admin.TabularInline):
    model = Product
    extra = 0


class InlineCartProducts(admin.TabularInline):
    model = Cart.products.through
    extra = 0


class InlineTag(admin.TabularInline):
    model = Tag.product_set.through
    extra = 0


class InlineProductAttributeValue(admin.TabularInline):
    model = ProductAttributeValue
    extra = 0
    form = InlineProductAttributeValueForm


class InlineProductRecommendations(admin.TabularInline):
    model = Product.recommendations.through
    extra = 0
    fk_name = 'to_product'


class ProductAdmin(admin.ModelAdmin):
    exclude = ('tags', 'recommendations')
    inlines = (InlineProductPhoto, InlineTag, InlineProductAttributeValue, InlineProductRecommendations)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        product = Product.objects.get(id=object_id)
        attributes = product.attributes.all()
        extra_context = extra_context or {}
        extra_context['attributes_values'] = attributes
        return super(ProductAdmin, self).change_view(request, object_id, form_url, extra_context)

    def get_inline_formsets(self, request, formsets, inline_instances, obj=None):
        formset_list = super(ProductAdmin, self).get_inline_formsets(request, formsets, inline_instances, obj)

        if not obj:
            return formset_list

        for formset in formset_list:
            if formset.opts.model.__name__ == InlineProductRecommendations.model.__name__:
                for inline_form in formset:
                    inline_form.form.fields['from_product'].queryset = Product.objects.exclude(id=obj.id)
                break
            # elif formset.opts.model.__name__ == InlineProductAttributeValue.model.__name__:
            #     for attribute_form in formset:
            #         # for field in attribute_form.fieldsets:
            #         attribute_id = attribute_form.form["attribute"].initial
            #         # attribute_form.form.fields["attribute"].widget = forms.HiddenInput()
            #         # attribute_form.form.fields["attribute_name"] = forms.CharField(max_length=255)
            #         # attribute_form.form.fields["attribute_name"].widget = forms.TextInput()
            #         #(attribute_form.form.fields["attribute_name"].widget)
            #         if not attribute_id:
            #             continue
            #         type = ProductAttribute.objects.get(id=attribute_id).type
            #         for field in attribute_form.form:
            #             attribute_form.form.fields[field.name].widget.attrs["class"] = "value_input"
            #             print(field.name, type)
            #             if type == ProductAttribute.AttributeType.FLOAT and field.name == "float_value"\
            #                     or type == ProductAttribute.AttributeType.INT and field.name == "int_value"\
            #                     or type == ProductAttribute.AttributeType.STRING and field.name == "str_value"\
            #                     or type == ProductAttribute.AttributeType.BOOLEAN and field.name == "bool_value"\
            #                     or type == ProductAttribute.AttributeType.VARIANTS and field.name == "str_value":
            #                 if field.name == "bool_value":
            #                     print("check_box")
            #                     attribute_form.form.fields[field.name].widget = forms.CheckboxInput()
            #                 elif field.name == "str_value" and type == ProductAttribute.AttributeType.VARIANTS:
            #                     print("ok")
            #                     attribute_form.form.fields[field.name].widget = forms.Select()
            #                     attribute_form.form.fields[field.name].choices = [("ьужской", "мужской")("женский", "жегкский")]
            #                 continue
            #
            #             #attribute_form.form.fields[field.name].widget.attrs["style"] = "display: none"
            #         #print(attribute_form.form.fields)

        return formset_list


class InlineAddress(admin.TabularInline):
    model = Address
    extra = 1


class CustomerAdmin(admin.ModelAdmin):
    inlines = (InlineAddress, )


class CategoryAttributeInline(admin.TabularInline):
    model = ProductAttribute.categories.through
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = (CategoryAttributeInline, )

# InlineProduct


class CartAdmin(admin.ModelAdmin):
    inlines = (InlineCartProducts, )


class InlineAttributeVariantValues(admin.TabularInline):
    model = VariantsAttributeValue
    extra = 0


class InlineProductAttributeAdmin(admin.ModelAdmin):
    inlines = (InlineAttributeVariantValues, )
    form = ProductAttributeForm


admin.site.register(Cart, CartAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Category, CategoryAdmin)
# admin.site.register(Purchase)
admin.site.register(Product, ProductAdmin)
# admin.site.register(ProductPhoto)
# admin.site.register(Tag)
admin.site.register(Brand)
admin.site.register(ShippingMethod)
admin.site.register(PaymentMethod)
admin.site.site_title = 'Winter sports'
admin.site.site_header = 'Winter sports'
admin.site.register(ProductAttribute, InlineProductAttributeAdmin)

#TODO: усовершенствовать проверку паролей при регистрации пользователя на амдинской панели
