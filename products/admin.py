from django.contrib import admin
from .models import Category, Product, Review

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
admin.site.register(Category, CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name','content', 'price','amount', 'created_at', 'updated_at']
admin.site.register(Product, ProductAdmin)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['title','content', 'image','star', 'created_at', 'updated_at']
admin.site.register(Review)