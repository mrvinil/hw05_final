from django import forms
from django.core.exceptions import ValidationError
from pytils.translit import slugify

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма создания нового поста"""

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        # Магия Джанго: через '__all__' создаётся форма из всех полей модели
        # labels и help_texts берутся из verbose_name и help_text
        # fields = '__all__'

    # Валидация поля slug
    def clean_slug(self):
        """Обрабатывает случай, если slug не уникален."""
        cleaned_data = super(PostForm, self).clean()
        slug = cleaned_data.get('slug')
        if not slug:
            title = cleaned_data.get('title')
            slug = slugify(title)[:100]
        if Post.objects.filter(slug=slug).exists():
            raise ValidationError(f'Адрес "{slug}" уже существует, '
                                  'придумайте уникальное значение')
        return slug


class CommentForm(forms.ModelForm):
    """Форма создания комментария к посту"""

    class Meta:
        model = Comment
        fields = ('text',)
