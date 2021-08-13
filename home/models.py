from django.db import models
from django.utils import timezone
from users.models import User


# Create your models here.


class ArticleCategory(models.Model):
    # 文章分类
    # 分类标签
    title = models.CharField(max_length=100, blank=True)
    # 标签创建时间
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    # admin站点显示，调试查看对象方便
    class Meta:
        db_table = 'tb_category'  # 修改标签
        verbose_name = '类别标签'
        verbose_name_plural = verbose_name


class Article(models.Model):
    """
    作者
    标题图
    标题
    分类
    标签
    摘要信息
    文章正文
    浏览量
    评论量
    文章发表时间
    文章修改时间
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='article/%Y/%m/%d', blank=True)
    title = models.CharField(max_length=30, blank=True)
    category = models.ForeignKey(ArticleCategory, null=True, on_delete=models.CASCADE, related_name='article')
    tags = models.CharField(max_length=20, blank=True)
    sumary = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField()
    total_views = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    # 修改表名以及后台展示信息
    class Meta:
        db_table = 'tb_article'
        ordering = ('-created',)
        verbose_name = '文章管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Comment(models.Model):
    # 评论内容
    content = models.TextField()
    # 评论的文章
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True)
    # 评论的用户名
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    # 评论时间
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.article.title

    class Meta:
        db_table = 'tb_comment'
        verbose_name = '评论管理'
        verbose_name_plural = verbose_name
