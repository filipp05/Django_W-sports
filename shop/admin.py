from django.contrib import admin
from .models import Category, Product, ProductPhoto, Tag, Customer, Brand, ProductAttribute, Cart, Address, \
    ProductAttributeValue, ShippingMethod, PaymentMethod


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


class InlineProductAttributeValue(admin.TabularInline):
    model = ProductAttributeValue


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

        return formset_list


class InlineAddress(admin.TabularInline):
    model = Address
    extra = 1


class CustomerAdmin(admin.ModelAdmin):
    inlines = (InlineAddress, )


class CategoryAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = (CategoryAttributeInline, )
    
# InlineProduct


class CartAdmin(admin.ModelAdmin):
    inlines = (InlineCartProducts, )


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

