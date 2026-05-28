"""
URL mappings for the recipe app
"""


from django.urls import (
    include,
    path,
)
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register('recipe', views.RecipeViewSet)
router.register('tag', views.TagViewset)
router.register('ingredient',views.IngredientViewset)


app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]