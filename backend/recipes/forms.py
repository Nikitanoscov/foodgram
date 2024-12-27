from django import forms


class RecipeIngredientsInLineFormSet(forms.BaseInlineFormSet):

    def clean(self):
        ingredients = []
        for data in self.cleaned_data:
            if data:
                ingredients.append(data.get('ingredient'))
        if not ingredients:
            raise forms.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.'
            )
        if len(ingredients) > len(set(ingredients)):
            raise forms.ValidationError(
                'Ингредиенты должны быть разными.'
            )
        return super().clean()


class RecipeTagsInLineFormSet(forms.BaseInlineFormSet):

    def clean(self):
        tags = []
        for data in self.cleaned_data:
            if data:
                tags.append(data.get('tag'))
        if not tags:
            raise forms.ValidationError(
                'Рецепт должен содержать хотя бы один тег.'
            )
        if len(tags) > len(set(tags)):
            raise forms.ValidationError(
                'Рецепт не может содержать одинаковые теги.'
            )
        return super().clean()
