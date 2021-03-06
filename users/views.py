import re
import logging

from django.shortcuts import render
from django.views import View
from django.http.response import HttpResponseBadRequest, JsonResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse
from utils.response_code import RETCODE
from random import randint
from libs.yuntongxun.sms import CCP
from users.models import User
from django.db import DatabaseError
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from home.models import ArticleCategory, Article

# Create your views here.

logger = logging.getLogger('django')


class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """
        1. 接收数据
        2. 验证数据(数据是否齐全、手机号格式、密码格式、密码和确认密码是否一致、短信验证码是否和redis中的一致)
        3. 保存注册信息
        4. 返回响应并跳转到登录页
        """
        # 1. 接收数据
        # mobile = request.POST.get('mobile')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        # smscode = request.POST.get('sms_code')
        # 2. 验证数据
        #     2.1 数据是否齐全
        if not all([username, email, password, password2]):
            return HttpResponseBadRequest('缺少必要的参数')
        #     2.2 手机号格式
        # if not re.match(r'^1[3-9]\d{9}$', mobile):
        #     return HttpResponseBadRequest('手机号输入错误')
        #     2.3 密码格式
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码格式错误，请输入8-20位数字+字母')
        if not re.match(r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
            return HttpResponseBadRequest('邮箱格式错误')
        #     2.4 密码和确认密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次输入密码不一致')
        #     2.5 短信验证码是否和redis中的一致
        # redis_conn = get_redis_connection('default')
        # redis_sms_code = redis_conn.get('sms:%s' % mobile)
        # if redis_sms_code is None:
        #     return HttpResponseBadRequest('短信验证码已过期')
        # if smscode != redis_sms_code.decode():
        #     return HttpResponseBadRequest('短信验证码错误')
        # 3. 保存注册信息
        # create_user 可以对密码进行加密
        try:
            user = User.objects.create_user(username=username, password=password, email=email)
        except DatabaseError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')

        login(request, user)
        # 4. 返回响应并跳转到登录页
        # 暂时返回注册成功
        # return HttpResponse('注册成功')
        response = redirect(reverse('home:index'))
        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username, max_age=7 * 24 * 3600)
        return response


class LoginView(View):

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        """
        1. 接收参数
        2. 验证参数
            2.1 手机号
            2.2 密码
        3. 用户认证登录
        4. 状态保持
        5. 判断用户是否选择记住登陆状态
        6. 为首页展示设置一些cookie
        7. 返回响应
        """
        # 1. 接收参数
        # mobile = request.POST.get('mobile')
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        # 2. 验证参数
        #     2.1 手机号
        # if not re.match(r'^1[3-9]\d{9}$', mobile):
        #     return HttpResponseBadRequest('手机号错误')
        #     2.2 密码
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码格式错误')
        # 3. 用户认证登录
        # 如果用户名和密码匹配,返回user  如果用户名和密码不匹配,返回None
        # 默认的认证方法是用username来继续判断，而当前判断信息为mobile，所以需要修改默认的认证方式
        # 需要到User模型中修改
        user = authenticate(username=username, password=password)
        if user is None:
            return HttpResponseBadRequest('用户名或密码错误')
        # 4. 状态保持
        login(request, user)
        # 5. 判断用户是否选择记住登陆状态

        # 根据链接中的next参数进行页面跳转
        next_page = request.GET.get('next')
        if next_page:
            response = redirect(next_page)
        else:
            response = redirect(reverse('home:index'))

        if remember != 'on':  # 没有记住
            # 6. 为首页展示设置一些cookie
            request.session.set_expiry(0)
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, max_age=14 * 24 * 2600)
        else:
            request.session.set_expiry(None)  # 默认记住两周
            response.set_cookie('is_login', True, max_age=14 * 24 * 2600)
            response.set_cookie('username', user.username, max_age=14 * 24 * 2600)
        # 7. 返回响应
        return response


class ImageCodeView(View):

    def get(self, request):
        """
        1. 接收前端的uuid
        2. 判断是否获取到uuid
        3. 通过调用captcha来生成图片验证码(图片二进制、图片内容)
        4. uuid为key 图片内容为value 保存到redis中 同时设置一个时效
        5. 返回图片二进制
        """

        # 1. 接收前端的uuid
        uuid = request.GET.get('uuid')
        image_code = request.GET.get('image_code')
        # 2. 判断是否获取到uuid
        if uuid is None:
            return HttpResponseBadRequest('没有传递uuid')
        # 3. 通过调用captcha来生成图片验证码(图片二进制、图片内容)
        text, image = captcha.generate_captcha()
        # 4. uuid为key 图片内容为value 保存到redis中 同时设置一个时效
        redis_conn = get_redis_connection('default')
        redis_conn.setex('img:%s' % uuid, 300, text)

        #   返回图片二进制
        return HttpResponse(image, content_type="image/jpeg")


class CheckImageView(View):

    def get(self, request):

        username = request.GET.get('username')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        #   参数是否完整
        if not all([username, image_code, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少参数'})
        #   图片验证码的验证
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s' % uuid)
        #   链接redis，获取redis中的验证码，并判断验证码是否存在或过期
        if redis_image_code is None:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码不存在或已过期'})
        #   如果未过期，获取后删除验证码
        try:
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        #   验证图片验证码(注意大小写、redis的数据类型为bytes)
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码错误'})
        return JsonResponse({'code': RETCODE.OK})


# class SmsCodeView(View):
#
#     def get(self, request):
#         """
#         1. 接收参数
#         2. 参数的验证
#            2.1 参数是否完整
#            2.2 图片验证码的验证
#                 链接redis，获取redis中的验证码，并判断验证码是否存在或过期
#                 如果未过期，获取后删除验证码
#                 验证图片验证码(注意大小写、redis的数据类型为bytes)
#         3. 生成短信验证码(为了后期方便可以将短信验证码存放到日志中）
#         4. 保存短信验证码到redis
#         5. 发送短信
#         6. 返回响应
#         """
#
#         # 1. 接收参数
#         mobile = request.GET.get('mobile')
#         image_code = request.GET.get('image_code')
#         uuid = request.GET.get('uuid')
#         # 2. 参数的验证
#         #    2.1 参数是否完整
#         if not all([mobile, image_code, uuid]):
#             return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少参数'})
#         #    2.2 图片验证码的验证
#         redis_conn = get_redis_connection('default')
#         redis_image_code = redis_conn.get('img:%s' % uuid)
#         #         链接redis，获取redis中的验证码，并判断验证码是否存在或过期
#         if redis_image_code is None:
#             return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码不存在或已过期'})
#         #         如果未过期，获取后删除验证码
#         try:
#             redis_conn.delete('img:%s' % uuid)
#         except Exception as e:
#             logger.error(e)
#         #         验证图片验证码(注意大小写、redis的数据类型为bytes)
#         if redis_image_code.decode().lower() != image_code.lower():
#             return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码错误'})
#         # 3. 生成短信验证码(为了后期方便可以将短信验证码存放到日志中）
#         sms_code = '%06d' % randint(0, 999999)
#         logger.info(sms_code)
#         # 4. 保存短信验证码到redis
#         redis_conn.setex('sms:%s' % mobile, 300, sms_code)
#         # 5. 发送短信
#         CCP().send_template_sms(mobile, [sms_code, 5], 1)
#         # 6. 返回响应
#         return JsonResponse({'code': RETCODE.OK})


class LogoutView(View):

    def get(self, request):
        # 1. session数据清除
        logout(request)
        # 2. 删除部分cookie数据
        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')
        # 3. 跳转到首页
        return response


class ForgetPassword(View):

    def get(self, request):
        return render(request, 'forget_password.html')

    def post(self, request):
        """
        1. 接收数据
        2. 验证数据(数据是否齐全、手机号格式、密码格式、密码和确认密码是否一致、短信验证码是否正确)
        3. 查询手机号
        4. 如果手机号存在进行修改密码，如果手机号不存在，进行新用户创建
        5. 进行页面跳转(登录页)
        6. 返回响应
        """
        # 1.接收数据
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        # smscode = request.POST.get('sms_code')
        # 2. 验证数据
        #   2.1 数据是否齐全
        if not all([email, password, password2]):
            return HttpResponseBadRequest('缺少参数')
        #   2.2 手机号格式
        if not re.match(r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
            return HttpResponseBadRequest('请输入正确的邮箱')
        #   2.3 密码格式
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码格式错误，请输入8-20位数字+字母')
        #   2.4 密码和确认密码是否一致
        if password != password2:
            return HttpResponseBadRequest('两次输入密码不一致')
        #   2.5 短信验证码是否正确)
        # redis_conn = get_redis_connection('default')
        # redis_sms_code = redis_conn.get('sms:%s' % mobile)
        # if redis_sms_code is None:
        #     return HttpResponseBadRequest('短信验证码已过期')
        # if smscode != redis_sms_code.decode():
        #     return HttpResponseBadRequest('短信验证码错误')
        # 3. 查询手机号
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 4.1 如果手机号不存在，进行新用户创建
            # try:
            #     User.objects.create_user(username=mobile, mobile=mobile, password=password)
            # except Exception:
            return HttpResponseBadRequest('该用户不存在')
        else:
            # 4.2 如果手机号存在进行修改密码
            user.set_password(password)
            user.save()
        # 5. 进行页面跳转(登录页)
        response = redirect(reverse('users:login'))
        # 6. 返回响应
        return response


# LoginRequiredMixin
# 如果用户未登录，则会进行默认跳转  /accounts/login/?next=/center/
# 我们需要在setting中修改默认跳转链接  /login/?next=/center/
class UserCenterView(LoginRequiredMixin, View):

    def get(self, request):
        # 获取用户登录信息
        user = request.user
        # 组织获取用户信息
        context = {
            'username': user.username,
            'email': user.email,
            'avatar': user.avatar.url if user.avatar else None,
            'user_desc': user.user_desc
        }
        return render(request, 'center.html', context=context)

    def post(self, request):
        """
        1. 接收参数
        2. 将参数保存
        3. 更新cookie中的信息
        4. 刷新页面（重定向）
        5. 返回响应
        """
        user = request.user
        # 1. 接收参数
        username = request.POST.get('username')
        email = request.POST.get('email')
        user_desc = request.POST.get('desc', user.user_desc)
        avatar = request.FILES.get('avatar')

        if not re.match(r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
            return HttpResponseBadRequest('请输入正确的邮箱')
        # 2. 将参数保存
        try:
            user.email = email
            user.username = username
            user.user_desc = user_desc
            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改失败，请稍后再试')
        # 3. 更新cookie中的信息
        # 4. 刷新页面（重定向）
        response = redirect(reverse('users:center'))
        response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        # 5. 返回响应
        return response


class WriteBlogView(LoginRequiredMixin, View):

    def get(self, request):
        # 查询所以标签
        categories = ArticleCategory.objects.all()
        context = {
            'categories': categories
        }
        return render(request, 'write_blog.html', context=context)

    def post(self, request):
        """
        1. 接收数据
        2. 验证数据
        3. 数据入库
        4. 跳转到指定页面
        """
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        sumary = request.POST.get('sumary')
        content = request.POST.get('content')
        user = request.user

        if not all([avatar, title, category_id, tags, sumary, content, user]):
            return HttpResponseBadRequest('参数输入不全')
        try:
            category = ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有这个分类标签哦')

        try:
            article = Article.objects.create(
                author=user,
                title=title,
                avatar=avatar,
                category=category,
                tags=tags,
                sumary=sumary,
                content=content
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败，请稍后再试')

        response = redirect(reverse('home:index'))
        return response
