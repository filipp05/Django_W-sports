from django.test import TestCase, Client
from .models import Customer, Cart, ProductVariant, Product, Category, ProductAttribute, \
    ProductAttributeValue, VariantsAttributeValue, Order
import random


class CartTest(TestCase):
    def setUp(self) -> None:
        username = "test"
        password = "test"

        self.client = Client()
        self.owner = Customer.objects.create_user(username=username, password=password)
        self.user = self.client.login(username=username, password=password)

        categories = []
        for i in range(5):
            categories.append(Category.objects.create(name=f"{i}_test_category"))

        self.products = []
        attributes = []
        for i in range(20):
            attributes.append(ProductAttribute.objects.create(name=f"test_attribute_{i}",
                                                              type=ProductAttribute.AttributeType.INT))

            attribute_categories = random.sample(categories, random.randint(1, 3))
            attributes[i].categories.add(*attribute_categories)

        variant_attributes = []

        for i in range(20):
            variant_attributes.append(ProductAttribute.objects.create(name=f"test_attribute_{i}",
                                                                      type=ProductAttribute.AttributeType.INT))

            attribute_categories = random.sample(categories, random.randint(1, 3))
            variant_attributes[i].categories.add(*attribute_categories)

        for i in range(10):
            self.products.append(Product.objects.create(name=f"test_product_{i}", price=random.randint(100, 10000)))
            product_categories = random.sample(categories, random.randint(1, 3))
            self.products[i].categories.add(*product_categories)
            product_attributes = Category.objects.filter(
                id__in=[category.id for category in product_categories]).filter(
                productattribute__id__in=[attr.id for attr in attributes]).values_list("productattribute", flat=True)
            product_attribute_values = []
            for attr in ProductAttribute.objects.filter(id__in=product_attributes):
                product_attribute_values.append(
                    ProductAttributeValue(product=self.products[i], attribute=attr, int_value=random.randint(1, 10)))
            ProductAttributeValue.objects.bulk_create(product_attribute_values)

            variant_attribute_values = []
            variant = ProductVariant.objects.create(product=self.products[i], count=random.randint(1, 40))
            product_variant_attributes = Category.objects.filter(
                id__in=[category.id for category in product_categories])\
                .filter(productattribute__id__in=[attr.id for attr in variant_attributes])\
                .values_list("productattribute", flat=True)

            for attr in ProductAttribute.objects.filter(id__in=product_variant_attributes):
                variant_attribute_values.append(
                    VariantsAttributeValue(product_variant=variant, attribute=attr, int_value=random.randint(1, 20)))
            VariantsAttributeValue.objects.bulk_create(variant_attribute_values)

    def test_cart_total_amount_single_product(self):
        cart = Cart.objects.create(owner=self.owner)
        variant = random.choice(self.products).productvariant_set.order_by("?").first()
        count = random.randint(1, 50)
        Order.objects.create(cart=cart, product_variant=variant, count=count)

        self.assertEqual(cart.get_total_amount(), variant.product.price * count)

    def test_cart_total_amount_all_products(self):
        cart = Cart.objects.create(owner=self.owner)
        products = random.sample(self.products, random.randint(1, 5))
        summ = 0
        orders = []

        for product in products:
            variant = product.productvariant_set.order_by("?").first()
            count = random.randint(1, 60)
            orders.append(Order(cart=cart, product_variant=variant, count=count))
            summ += variant.product.price * count

        Order.objects.bulk_create(orders)

        self.assertEqual(cart.get_total_amount(), summ)

    def test_check_total_amount_on_cart_page(self):
        cart = Cart.objects.create(owner=self.owner)
        products = random.sample(self.products, random.randint(1, 5))
        summ = 0
        orders = []

        for product in products:
            variant = product.productvariant_set.order_by("?").first()
            count = random.randint(1, 60)
            orders.append(Order(cart=cart, product_variant=variant, count=count))
            summ += variant.product.price * count

        Order.objects.bulk_create(orders)

        response = self.client.get("/cart/")

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, f"К оплате: {summ}".replace(".", ","))
        self.assertContains(response, f"К оплате: {cart.get_total_amount()}".replace(".", ","))

    def test_check_add_product(self):
        product = random.choice(self.products)
        product_variant = product.productvariant_set.order_by("?").first()
        variant_attributes = product_variant.attribute_values.all()
        data = {}
        # cart = Cart.objects.get(owner=self.owner)
        print(variant_attributes)
        for attr in variant_attributes:
            print(attr)
            data[f"attribute-{attr.id}"] = attr.variantsattributevalue_set.order_by("?").first().int_value
        response = self.client.post(f"/add_to_cart/{product.id}", data)
        print(response)
