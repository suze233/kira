from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from home.models import ArticleCategory, Article
from django.http.response import HttpResponseBadRequest
from django.core.paginator import Paginator, EmptyPage
from home.models import Comment


# Create your views here.
class IndexView(View):

    def get(self, request):
        """
        1. 获取所有分类标签
        2. 接收用户点击的分类标签
        3. 根据分类标签id进行查询
        4. 获取分页参数
        5. 根据分类信息查询文章信息
        6. 创建分页器
        7. 进行分页处理
        8. 组织数据传递给模板
        """
        # 1. 获取所有分类标签
        categories = ArticleCategory.objects.all()
        # 2. 接收用户点击的分类标签
        cat_id = request.GET.get('cat_id', 1)
        # 3. 根据分类标签id进行查询
        try:
            category = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有这个分类标签呀')
        # 4. 获取分页参数
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 10)
        # 5. 根据分类信息查询文章信息
        articles = Article.objects.filter(category=category)
        # 6. 创建分页器
        paginator = Paginator(articles, per_page=page_size)
        # 7. 进行分页处理
        try:
            page_article = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseBadRequest('empty page')
        # 总页数
        total_page = paginator.num_pages
        # 8. 组织数据传递给模板
        context = {
            'categories': categories,
            'category': category,
            'articles': page_article,
            'total_page': total_page,
            'page_num': page_num
        }
        return render(request, 'index.html', context=context)


class DetailView(View):

    def get(self, request):
        """
        1. 接收文章id
        2. 根据id查询文章数据
        3. 查询分类数据
        4. 获取分页参数
        5. 根据文章信息查询评论数据
        6. 创建分页器
        7. 进行分页
        8. 组织模板数据
        """
        # 1. 接收文章id
        id = request.GET.get('id')
        # 2. 根据id查询文章数据
        try:
            article = Article.objects.get(id=id)
        except Article.DoesNotExist:
            return render(request, '404.html')
        else:
            # 浏览量加一
            article.total_views += 1
            article.save()
        # 3. 查询分类数据
        categories = ArticleCategory.objects.all()
        # 查询浏览量前10的文章
        hot_articles = Article.objects.order_by('-total_views')[:9]
        # 4. 获取分页参数
        page_size = request.GET.get('page_size', 7)
        page_num = request.GET.get('page_num', 1)
        # 5. 根据文章信息查询评论数据
        comments = Comment.objects.filter(article=article).order_by('-created')
        # 获取评论总数
        comments_count = comments.count()
        # 6. 创建分页器
        paginator = Paginator(comments, page_size)
        # 7. 进行分页
        try:
            page_comments = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseBadRequest('empty page')
        # 总页数
        total_page = paginator.num_pages
        # 8. 组织模板数据
        context = {
            'categories': categories,
            'category': article.category,
            'article': article,
            'hot_articles': hot_articles,
            'comments_count': comments_count,
            'comments': page_comments,
            'total_page': total_page,
            'page_num': page_num
        }
        return render(request, 'detail.html', context=context)

    def post(self, request):
        """
        1. 接收用户信息
        2. 判断用户是否登录
        3. 登录用户可评论 接收数据
            3.1 接收评论数据
            3.2 验证文章是否存在
            3.3 保存评论数据
            3.4 修改文章评论
        4. 未登录跳转的到登录页
        """
        # 1. 接收用户信息
        user = request.user
        # 2. 判断用户是否登录
        if user and user.is_authenticated:
            # 3. 登录用户可评论 接收数据
            #     3.1 接收评论数据
            id = request.POST.get('id')
            content = request.POST.get('content')
            #     3.2 验证文章是否存在
            try:
                article = Article.objects.get(id=id)
            except Article.DoexNotExist:
                return HttpResponseBadRequest('没有此文章')
            #     3.3 保存评论数据
            Comment.objects.create(
                content=content,
                article=article,
                user=user
            )
            #     3.4 修改文章评论
            article.comments += 1
            article.save()
            # 刷新页面
            path = reverse('home:detail') + '?id={}'.format(article.id)
            return redirect(path)
        else:
            # 4. 未登录跳转的到登录页
            return redirect(reverse('users:login'))

