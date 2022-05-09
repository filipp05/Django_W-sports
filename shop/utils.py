from django.db.models import Q, Prefetch, F

from .models import VariantsAttributeValue, ProductVariant, Cart


def get_product_variant(post_data, product_id):
    data = dict(post_data)
    data.pop('csrfmiddlewaretoken', "")  # выкидываем из словаря токен, чтобы остались только значения атрибутов продуктов
    query = Q()

    if not data:
        return ProductVariant.objects.filter(product__id=product_id).first()

    for key in data:
        try:
            int_value = int(data[key][0])
        except:
            int_value = None

        try:
            float_value = float(data[key][0])
        except:
            float_value = None

        query.add(Q(Q(attribute_id=int(key[10:])) & Q(
            Q(int_value=int_value) & Q(float_value=float_value) & Q(str_value=data[key][0]))), Q.OR)

    variants_values = VariantsAttributeValue.objects.filter(query,
                                                    Q(product_variant__product__id=product_id))

    variants = variants_values.values("product_variant").distinct()
    if len(variants) != 1 or variants_values.count() != len(data.keys()):
        return None

    return ProductVariant.objects.prefetch_related(Prefetch("variant_values", VariantsAttributeValue.objects.
                                                            filter(product_variant=F("product_variant"))\
        .annotate(value=F("str_value")))).get(id=variants[0]["product_variant"])





