from django.shortcuts import render
from django.views import View
from django.http.response import HttpResponseBadRequest
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse

# Create your views here.


class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')


class LoginView(View):

    def get(self, request):
        return render(request, 'login.html')


class ImageCodeView(View):

    def get(self, request):
        """
        1. 接收前端的uuid
        2. 判断是否获取到uuid
        3. 通过调用captcha来生成图片验证码(图片二进制、图片内容)
        4. uuid为key 图片内容为value 保存到redis中 同时设置一个时效
        5. 返回图片二进制
        """
        uuid = request.GET.get('uuid')
        if uuid is None:
            return HttpResponseBadRequest('没有传递uuid')
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('default')
        redis_conn.setex('img:%s' % uuid, 300, text)
        return HttpResponse(image, content_type="image/jpeg")
