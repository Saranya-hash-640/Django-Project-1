from django import forms
from .models import Product, Category

# ---------------- CATEGORY FORM ----------------
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'subcategory']  # use actual field names

# ---------------- PRODUCT FORM ----------------
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock', 'image']
