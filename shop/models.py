from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import F, ExpressionWrapper, FloatField, Sum
#TODO: Модель пользователя: рост, вес, размер ноги, навыки катания и тп... Мази по температуре, фильтры масок по освещенности

# Полиморфизм гарантирует, что объект может вести себя по-разному в разных условиях


# git init  git status  git add (. / Названия файлов и папок)  git commit -m "сообщение"
# git checkout (первые 5 цифр коммита / название ветки)  git log - посмотреть историю коммитов
# git checkout -b название_ветки — создать новую ветку
# git merge название_ветки — слить текущую ветку и указанную
# git pull — вытащить изменения с сервера
# git push — залить изменения на сервер
# git remote add origin адрес_сервера — добавления удаленного репозитория для обмена кодом
# git remote — просмотр списка удаленных репозиториев
# git remote -v — простотр адресов удаленных репозиториев для загрузки и выгрузки кода
# git clone адрес_репозитория — клонирование чужого репозитория


class Product(models.Model):
    """Модель товара"""
    name = models.CharField(verbose_name="Название", max_length=150, db_index=True)
    description = models.TextField(verbose_name="Описание", null=True, blank=True)
    price = models.FloatField(verbose_name="Цена", help_text="Цену указывать в рублях", db_index=True)

    photo = models.ImageField(upload_to="product_photos", verbose_name="Главное фото товара", default='/xtra/noimage.jpg')
    published = models.DateTimeField(auto_now_add=True, verbose_name='Опубликовано')
    category = models.ForeignKey("Category", on_delete=models.CASCADE, verbose_name="Категория товара", null=True,
                                 blank=True, db_index=True)
    tags = models.ManyToManyField('Tag', verbose_name='Тэг')
    brand = models.ForeignKey('Brand', on_delete=models.PROTECT, verbose_name='Бренд', null=True, blank=True)
    attributes = models.ManyToManyField("ProductAttribute", through='ProductAttributeValue')
    recommendations = models.ManyToManyField('Product', verbose_name='рекомендации к товару')
    # variants = models.ManyToManyField("ProductAttributeValue", verbose_name="Варианты продукта",
    #                                  through="ProductVariant", related_name="products")

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        created = not self.pk
        super(Product, self).save(*args, **kwargs)
        attribute_list = ProductAttribute.objects.filter(categories=self.category)
        if created:
            for attribute in attribute_list:
                if not attribute.is_choosable:
                    ProductAttributeValue.objects.create(product=self, attribute=attribute)
        return self # TODO: неправильно добавляются выбираемые атрибуты для товаров

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["-published"]


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
    count = models.PositiveSmallIntegerField(verbose_name="Количество", default=0)
    attribute_values = models.ManyToManyField("ProductAttribute", verbose_name="Значения параметров", through="VariantsAttributeValue")

    def __str__(self):
        return f"{self.product}: {', '.join([ str(attr_val.get_value()) for attr_val in self.variant_values.all()])}" #TODO: доделать метод и вывести выбираемые атрибуты на странице продукта на сайте

    def save(self, *args, **kwargs):
        created = not self.pk
        super(ProductVariant, self).save(*args, **kwargs)
        attribute_list = ProductAttribute.objects.filter(categories=self.product.category)
        if created:
            for attribute in attribute_list:
                if attribute.is_choosable:
                    VariantsAttributeValue.objects.create(product_variant=self, attribute=attribute)
        return self


class ProductAttribute(models.Model):
    """Модель свойств (аттрибутов) продуктов """
    class AttributeType(models.TextChoices):
        INT = 'INT', 'Целое число'
        FLOAT = 'FLT', 'Дробное число'
        STRING = 'STR', 'Строковое значение'
        BOOLEAN = 'BLN', 'Да/Нет'
        VARIANTS = 'VRT', 'Набор вариантов'

    name = models.CharField(verbose_name='Название', max_length=150)
    categories = models.ManyToManyField('Category', verbose_name='Категория')
    type = models.CharField(choices=AttributeType.choices, max_length=3)
    is_choosable = models.BooleanField(verbose_name="Выбираемый пользователем?", default=False)

    def __str__(self):
        return str(self.name)


class ChoosableAttributeOptions(models.Model):
    value = models.CharField(verbose_name="Значение", max_length=255)
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, verbose_name="Атрибут")

    class Meta:
        verbose_name = "Значение выбираемого атрибута"
        verbose_name_plural = "Значения выбираемых атрибутов"


    # def save(self, *args, **kwargs):
    #     print(args, kwargs)
    #     created = not self.pk
    #     super(ProductAttribute, self).save(*args, **kwargs)
    #     # super(ProductAttribute, self).save_related(*args, **kwargs)
    #     product_list = Product.objects.filter(category__in=self.categories.all())
    #     print(product_list, self.categories.all())
    #     if created:
    #         for product in product_list:
    #             ProductAttributeValue.objects.create(product=product, attribute=self)
    #     return self


class Category(models.Model):
    """Категория товара"""
    name = models.CharField(verbose_name="Название", max_length=150)
    description = models.TextField(verbose_name="Описание", null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ['name']


class Tag(models.Model):
    """Тэг товара"""
    name = models.CharField(max_length=150, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "тэг"
        verbose_name_plural = "тэги"
        ordering = ['name']


class ProductPhoto(models.Model):
    """Детальное фото товара"""
    description = models.CharField(max_length=255, verbose_name='Описание', null=True, blank=True)
    product = models.ForeignKey("Product", on_delete=models.CASCADE, verbose_name="товар", related_name='images')
    photo = models.ImageField(verbose_name='Фотография', upload_to='photos')

    def __str__(self):
        return str(self.description)

    class Meta:
        verbose_name = "детальное фото"
        verbose_name_plural = "детальные фото"
        ordering = ['product']


class Customer(AbstractUser):
    """Новая модел пользователя"""
    phone = models.CharField(verbose_name="Телефон",
                             blank=True, max_length=12, null=True, )
    email = models.EmailField(verbose_name='email', unique=True)
    # visited_categories = models.ManyToManyField(Category, verbose_name='Посещенные категории', null=True, blank=True)

    #    purchases = models.ManyToManyField("Product", through="Purchase", verbose_name="Товары")

    def get_recommendations(self):
        return self.visited_categories[3]

    class Meta:
        verbose_name = "покупатель"
        verbose_name_plural = "покупатели"


# TODO: зашить внутрь системы список городов России
class Address(models.Model):
    """Модель адреса для оформления заказа"""
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(verbose_name='Улица', max_length=100)
    house = models.CharField(max_length=100, verbose_name='Дом')
    flat = models.PositiveSmallIntegerField(verbose_name='Квартира/Офис')
    contact = models.CharField(max_length=100, verbose_name='Контактное лицо')
    extra_phone = models.CharField(verbose_name='Доп телефон', max_length=12)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Клиент')

    def __str__(self):
        return f"г. {self.city}, {self.street}, д. {self.house}, кв/оф {self.flat}, получатель: {self.customer}"


class Brand(models.Model):
    """Бренд"""
    name = models.CharField(max_length=150, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    photo = models.ImageField(verbose_name='Фото', upload_to='brand_photos', null=True, blank=True, default="xtra/noimage.jpg")

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'бренд'
        verbose_name_plural = 'бренды'
        ordering = ['name']


class AttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, verbose_name='аттрибут', on_delete=models.CASCADE)
    int_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    str_value = models.CharField(max_length=150, null=True, blank=True)
    bool_value = models.BooleanField(null=True, blank=True)

    def __str__(self):
        if self.attribute.type == ProductAttribute.AttributeType.INT:
             value = self.int_value
        elif self.attribute.type == ProductAttribute.AttributeType.FLOAT:
             value = self.float_value
        elif self.attribute.type == ProductAttribute.AttributeType.STRING:
             value = self.str_value
        elif self.attribute.type == ProductAttribute.AttributeType.BOOLEAN:
             value = self.bool_value
        if self.attribute.type == ProductAttribute.AttributeType.VARIANTS:
             value = " "
        return f"{ self.attribute.name } { value }"

    def get_value(self):
        return self.int_value or self.float_value or self.str_value or self.bool_value

    class Meta:
        abstract = True


class ProductAttributeValue(AttributeValue):
    product = models.ForeignKey(Product, verbose_name='продукт', on_delete=models.CASCADE,
                                related_name="attribute_values")

    class Meta:
        verbose_name = "Параметры продукта"
        verbose_name_plural = "Параметры продуктов"


class VariantsAttributeValue(AttributeValue):
    """Варинант продукта"""
    product_variant = models.ForeignKey(ProductVariant, verbose_name='Вариант продукта', on_delete=models.CASCADE,
                                related_name="variant_values")

    class Meta:
        verbose_name = "Вариант продукта"
        verbose_name_plural = "Варианты продуктов"


class ProductCart(models.Model):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE)
    count = models.SmallIntegerField(default=1)


class Cart(models.Model):
    """Модель корзины продуктов"""
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cart_list')
    products_variants = models.ManyToManyField(ProductVariant, through='ProductCart')
    created_at = models.DateTimeField(auto_now=True)
    is_shipped = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_checkouted = models.BooleanField(default=False)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, verbose_name='Адрес', null=True, blank=True)
    shipping_method = models.ForeignKey('ShippingMethod', on_delete=models.PROTECT, null=True, blank=True,
                                        verbose_name='Способ доставки')
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.PROTECT, null=True, blank=True,
                                       verbose_name='Способ оплаты')

    def get_total_amount(self):
        total_amount = ProductCart.objects.filter(cart=self).annotate(amount=ExpressionWrapper(F('product_variant__product__price') * F('count'), FloatField())).aggregate(value=Sum(F("amount")))

        # total_amount = self.products_variants.annotate(amount=ExpressionWrapper(F('product__price') * F('count'), FloatField())).aggregate(value=Sum(F("amount")))
        return total_amount['value']

    def __str__(self):
        return 'корзина ' + str(self.owner)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class ShippingMethod(models.Model):
    name = models.CharField(max_length=30, verbose_name='Название')

    def __str__(self):
        return self.name


class PaymentMethod(models.Model):
    name = models.CharField(max_length=30, verbose_name='Название')

    def __str__(self):
        return self.name


# class WareHouse(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
#     count = models.PositiveSmallIntegerField(verbose_name="Количество")




