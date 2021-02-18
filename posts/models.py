from django.contrib.auth import get_user_model
from django.db import models
from pytils.translit import slugify

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Текст',
                            help_text='Напишите ваше сообщение')
    pub_date = models.DateTimeField("date Published",
                                    auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор',
                               help_text='Укажите автора')
    group = models.ForeignKey('Group',
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              verbose_name='Сообщество',
                              help_text='Укажите сообщество',
                              blank=True,
                              null=True)
    image = models.ImageField(upload_to='posts/',
                              blank=True,
                              null=True,
                              verbose_name='Картинка',
                              help_text='Загрузите картинку')

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return str(self.text[:15])


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Название сообщества',
                             help_text='Придумайте название сообщества')
    slug = models.SlugField(unique=True,
                            verbose_name='Метка',
                            help_text='Метка вашего сообщества')
    description = models.TextField(verbose_name='Описание сообщества',
                                   help_text='Опишите для кого или для чего '
                                             'ваше сообщество')

    def __str__(self):
        return self.title[:100]

    # Расширение встроенного метода save(): если поле slug не заполнено -
    # транслитерировать в латиницу содержимое поля title и
    # обрезать до ста знаков
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
        super().save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             verbose_name='Пост',
                             on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User,
                               verbose_name='Автор комментария',
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(verbose_name='Комментарий',
                            help_text='Напишите ваш комментарий')
    created = models.DateTimeField(verbose_name='Дата создания',
                                   auto_now_add=True)

    class Meta:
        ordering = ['-created']
