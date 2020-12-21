from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import F, ExpressionWrapper, FloatField, Sum


# Полиморфизм гарантирует, что объект может вести себя по-разному в разных условиях


# git init  git status  git add (. / Названия файлов и папок)  git commit -m "сообщение"
# git checkout (первые 5 цифр коммита / название ветки)  git log - посмотреть историю коммитов
# git checkout -b название_ветки — создать новую ветку
# git merge название_ветки — слить текущую ветку и указанную


class Product(models.Model):
    """Модель товара"""
    name = models.CharField(verbose_name="Название", max_length=150, db_index=True)
    description = models.TextField(verbose_name="Описание", null=True, blank=True)
    price = models.FloatField(verbose_name="Цена", help_text="Цену указывать в рублях", db_index=True)
    count = models.SmallIntegerField(verbose_name="Количество на скалде", null=True, blank=True)
    photo = models.ImageField(upload_to="product_photos", verbose_name="Главное фото товара", default='/xtra/noimage.jpg')
    published = models.DateTimeField(auto_now_add=True, verbose_name='Опубликовано')
    category = models.ForeignKey("Category", on_delete=models.CASCADE, verbose_name="Категория товара", null=True,
                                 blank=True, db_index=True)
    tags = models.ManyToManyField('Tag', verbose_name='Тэг')
    brand = models.ForeignKey('Brand', on_delete=models.PROTECT, verbose_name='Бренд', null=True, blank=True)
    attributes = models.ManyToManyField("ProductAttribute", through='ProductAttributeValue')
    recommendations = models.ManyToManyField('Product', verbose_name='рекомендации к товару')

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        super(Product, self).save(*args, **kwargs)
        attribute_list = ProductAttribute.objects.filter(category=self.category)
        for attribute in attribute_list:
            ProductAttributeValue.objects.create(product=self, attribute=attribute)
        return self

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["-published"]


class ProductAttribute(models.Model):
    """Модель свойств (аттрибутов) продуктов """
    class AttributeType(models.TextChoices):
        INT = 'INT', 'Целое число'
        FLOAT = 'FLT', 'Дробное число'
        STRING = 'STR', 'Строковое значение'
        BOOLEAN = 'BLN', 'Да/Нет'
        VARIANTS = 'VRT', 'Набор вариантов'

    name = models.CharField(verbose_name='Название', max_length=150)
    category = models.ForeignKey('Category', verbose_name='Категория', on_delete=models.PROTECT)
    type = models.CharField(choices=AttributeType.choices, max_length=3)

    def __str__(self):
        return str(self.name)


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
    visited_categories = models.ManyToManyField(Category, verbose_name='Посещенные категории', null=True, blank=True)

    #    purchases = models.ManyToManyField("Product", through="Purchase", verbose_name="Товары")

    def get_recommendations(self):
        return self.visited_categories[3]

    class Meta:
        verbose_name = "покупатель"
        verbose_name_plural = "покупатели"


# TODO: зашить внутрь системы список городов России
class Address(models.Model):
    """Модель адреса"""
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
    photo = models.ImageField(verbose_name='Фото', upload_to='brand_photos', null=True, blank=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'бренд'
        verbose_name_plural = 'бренды'
        ordering = ['name']


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, verbose_name='продукт', on_delete=models.CASCADE)
    attribute = models.ForeignKey(ProductAttribute, verbose_name='аттрибут', on_delete=models.CASCADE)
    int_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    str_value = models.CharField(max_length=150, null=True, blank=True)
    bool_value = models.BooleanField(null=True, blank=True)


class ProductCart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE)
    count = models.SmallIntegerField(default=1)


class Cart(models.Model):
    """Модель корзины продуктов"""
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cart_list')
    products = models.ManyToManyField(Product, through='ProductCart')
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
        total_amount = self.products.annotate(amount=ExpressionWrapper(F('price') * F('productcart__count'), FloatField())).aggregate(value=Sum(F("amount")))
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



