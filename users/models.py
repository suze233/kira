from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
# 用户信息
class User(AbstractUser):
    # 手机
    # mobile = models.CharField(max_length=11, unique=True, blank=False)
    # 手机
    username = models.CharField(max_length=100, unique=True, blank=False)
    # 邮箱
    email = models.EmailField(blank=False)
    # 头像
    avatar = models.ImageField(upload_to='avatar/%Y/%m/%d', blank=True)
    # 简介
    user_desc = models.CharField(max_length=500, blank=True)
    # 修改认证字段
    # USERNAME_FIELD = 'mobile'
    # 创建超级管理员必须输入的字段（不包括手机、密码）
    # REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'tb_users'  # 修改表名
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name  # admin后台显示

    def __str__(self):
        return self.username
