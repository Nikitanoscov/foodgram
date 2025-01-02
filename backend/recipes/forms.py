from django import forms
from django.forms import ValidationError


class RecipeIngredientsInLineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        ingredients = []
        for form in self.forms:
            if form.is_valid():
                clean_data = form.cleaned_data
                print(clean_data)
                if (
                    clean_data.get('DELETE', '') is not True
                    and clean_data.get('ingredient')
                ):
                    ingredients.append(clean_data.get('ingredient'))
        if not ingredients:
            raise ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент'
            )
        return super().clean()


class RecipeTagsInLineFormSet(forms.BaseInlineFormSet):

    def clean(self):
        tags = []
        for form in self.forms:
            if form.is_valid():
                clean_data = form.cleaned_data
                if (
                    clean_data.get('DELETE', '') is not True
                    and clean_data.get('tag')
                ):
                    tags.append(clean_data.get('tag'))
        if not tags:
            raise forms.ValidationError(
                'Рецепт должен содержать хотя бы один тег.'
            )
        return super().clean()
