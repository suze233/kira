from django.urls import path
from users.views import RegisterView, LoginView, ImageCodeView, LogoutView
from users.views import ForgetPassword, UserCenterView, WriteBlogView, CheckImageView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    # 图片验证码
    path('imagecode/', ImageCodeView.as_view(), name='imagecode'),
    path('checkimg/', CheckImageView.as_view(), name='checkimg'),
    # 短信发送
    # path('smscode/', SmsCodeView.as_view(), name='smscode'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forget/', ForgetPassword.as_view(), name='forget'),
    path('center/', UserCenterView.as_view(), name='center'),
    path('write/', WriteBlogView.as_view(), name='write'),
]
