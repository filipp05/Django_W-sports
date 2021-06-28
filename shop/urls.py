from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views

app_name = 'Wsports'

urlpatterns = [
    path('', views.index, name='index_url'),
    path('brands/<slug:brand_name>/', views.brand_products, name='brand_url'),
    path('categories/<str:category_name>/', views.category_products, name='category_url'),
    path('product/<str:product_name>/', views.product_detail, name='product_url'),
    path('test_form/', views.test_model_form, name='form_url'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/register/', views.register, name='register'),
    path('add_to_cart/<int:product_id>', views.add_to_cart, name='add_to_cart_url'),
    path('cart/delete/<int:product_id>/', views.delete_from_cart, name='product_delete_url'),
    path('cart/', views.cart, name='cart_url'),
    path('shipping_and_payment/', views.shipping_and_payment, name='shipping_and_payment_url'),
    path('change_count/<int:product_variant_id>/<str:count>/', views.change_count, name='change_count_url'),
    path('checkout/', views.checkout, name='checkout_url'),
    path('purchase/<int:id>', views.purchase, name='purchase_url'),
    path('success/', views.payment_success, name='payment_success_url'),
    path('failure/', views.payment_failure, name='payment_failure_url'),
    path('result/', views.payment_result, name="payment_result_url"),
    path('get_attribute_format/', views.get_attribute_format, name="get_attribute_format_url")


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# accounts/login/ [name='login']
# accounts/logout/ [name='logout']
# accounts/password_change/ [name='password_change']
# accounts/password_change/done/ [name='password_change_done']
# accounts/password_reset/ [name='password_reset']
# accounts/password_reset/done/ [name='password_reset_done']
# accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
# accounts/reset/done/ [name='password_reset_complete']
