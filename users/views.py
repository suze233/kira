from django.shortcuts import render
from django.views import View
from django.http.response import HttpResponseBadRequest
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse
from django.http.response import JsonResponse
from utils.response_code import RETCODE
from random import randint
from libs.yuntongxun.sms import CCP
import logging
logger = logging.getLogger('django')

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


class SmsCodeView(View):

    def get(self, request):
        """
        1. 接收参数
        2. 参数的验证
           2.1 参数是否完整
           2.2 图片验证码的验证
                链接redis，获取redis中的验证码，并判断验证码是否存在或过期
                如果未过期，获取后删除验证码
                验证图片验证码(注意大小写、redis的数据类型为bytes)
        3. 生成短信验证码(为了后期方便可以将短信验证码存放到日志中）
        4. 保存短信验证码到redis
        5. 发送短信
        6. 返回响应
        """
        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        if not all([mobile, image_code, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少参数'})
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s' % uuid)
        if redis_image_code is None:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码不存在或已过期'})
        try:
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码错误'})

        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        redis_conn.setex('sms:%s' % mobile, 300, sms_code)

        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        return JsonResponse({'code': RETCODE.OK})





