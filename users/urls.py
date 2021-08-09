from django.urls import path
from users.views import RegisterView, LoginView, ImageCodeView, SmsCodeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    # 图片验证码
    path('imagecode/', ImageCodeView.as_view(), name='imagecode'),
    # 短信发送
    path('smscode/', SmsCodeView.as_view(), name='smscode'),

]
