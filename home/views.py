from django.shortcuts import render
from django.views import View
from home.models import ArticleCategory, Article
from django.http.response import HttpResponseBadRequest
from django.core.paginator import Paginator, EmptyPage


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
        4. 组织模板数据
        """
        # 1. 接收文章id
        id = request.GET.get('id')
        # 2. 根据id查询文章数据
        try:
            article = Article.objects.get(id=id)
        except Article.DoesNotExist:
            return render(request, '404.html')
        # 3. 查询分类数据
        categories = ArticleCategory.objects.all()
        # 4. 组织模板数据
        context = {
            'categories': categories,
            'category': article.category,
            'article': article
        }
        return render(request, 'detail.html', context=context)

