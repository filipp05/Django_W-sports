from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views

app_name = 'Wsports'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index_url'),
    path('brands/<slug:brand_name>/', views.BrandProductsView.as_view(), name='brand_url'),
    path('categories/<str:category_name>/', views.CategoryProductsView.as_view(), name='category_url'),
    path('product/<str:product_name>/', views.ProductDetailView.as_view(), name='product_url'),
    path('test_form/', views.test_model_form, name='form_url'),
    path('accounts/profile/', views.ProfileView.as_view(), name='profile'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('add_to_cart/<int:product_id>', views.AddToCartView.as_view(), name='add_to_cart_url'),
    path('cart/delete/<int:product_variant_id>/', views.DeleteAddressView.as_view(), name='product_delete_url'),
    path('cart/', views.CartView.as_view(), name='cart_url'),
    path('shipping_and_payment/', views.ShippingAndPaymentView.as_view(), name='shipping_and_payment_url'),
    path('change_count/<int:product_variant_id>/<str:count>/', views.ChangeCountView.as_view(), name='change_count_url'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout_url'),
    path('purchase/<int:id>', views.PurchaseView.as_view(), name='purchase_url'),
    path('success/', views.PaymentSuccessView.as_view(), name='payment_success_url'),
    path('failure/', views.PaymentFailureView.as_view(), name='payment_failure_url'),
    path('result/', views.PaymentResultView.as_view(), name="payment_result_url"),
    path('get_attribute_format/', views.GetAttributeFormatView.as_view(), name="get_attribute_format_url"),
    path('rent_product/<int:product_id>/', views.RentProductView.as_view(), name="rent_product"),
    path('rent/<int:product_variant_id>/', views.AcceptProductRentView.as_view(), name="rent_acception_url"),
    path('order_finish/', views.OrderFinishView.as_view(), name="order_finish_url"),
    path('delete_address/<int:address_id>/', views.DeleteAddressView.as_view(), name="delete_address_url"),
    path('find_weather_forecast/', views.FindWeatherForecastView.as_view(), name="find_weather_forecast_url")

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
