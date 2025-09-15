from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Lesson


# Task model
# ----------------------------------------------------------------------------------------------------------------------
class Task(models.Model):
    TASK_TYPE = (
        ('video', _('Видеосабақ')),
        ('written', _('Жазбаша')),
        ('test', _('Тест')),
        ('matching', _('Сәйкестендіру')),
        # ('text_gap', _('Толықтыру')),
        # ('table', _('Кесте толтыру')),
    )

    PARAMS = (
        ('none', _('Таңдалмаған')),
        (_('Тест'), (
            ('quiz', _('Тест')),
            ('true-false', _('Ақиқат/жалған')),
        )),
        (_('Сәйкестендіру'), (
            ('row', _('Қатар')),
            ('col', _('Баған')),
        )),
        ('lab', _('Виртуалды лаборатория'))
    )

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='tasks', verbose_name=_('Сабақ')
    )
    task_type = models.CharField(_('Тапсырма түрі'), choices=TASK_TYPE, default='video', max_length=32)
    params = models.CharField(_('Параметрлер'), choices=PARAMS, default='none', max_length=32)
    rating = models.PositiveIntegerField(_('Жалпы бағасы'), default=0)
    duration = models.PositiveSmallIntegerField(_('Тапсырма уақыты (мин)'), default=0)
    description = models.TextField(_('Анықтамасы'), blank=True, null=True)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return self.get_task_type_display()

    class Meta:
        verbose_name = _('Тапсырма')
        verbose_name_plural = _('Тапсырмалар')
        ordering = ('order', )


# Task type: Video model
# ----------------------------------------------------------------------------------------------------------------------
class Video(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True,
        verbose_name=_('Контент'), related_name='videos'
    )
    url = models.CharField(_('URL сілтеме'), max_length=255)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'{self.pk} - видеосабақ'

    class Meta:
        verbose_name = _('Видеосабақ')
        verbose_name_plural = _('Видеосабақтар')
        ordering = ('order', )


# Task type: Written model
# ----------------------------------------------------------------------------------------------------------------------
class Written(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='written', verbose_name=_('Тапсырма')
    )
    instruction = models.TextField(_('Тапсырма'), blank=True, null=True)

    def __str__(self):
        return f'{self.pk} - жазбаша'

    class Meta:
        verbose_name = _('Жазбаша')
        verbose_name_plural = _('Жазбашалар')


# Task type: TextGap model
# ----------------------------------------------------------------------------------------------------------------------
class TextGap(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='text_gaps', verbose_name=_('Сабақ')
    )
    prompt = models.TextField(_('Сөйлем (көп нүктемен)'))
    correct_answer = models.CharField(_('Дұрыс жауап'), max_length=255)

    def __str__(self):
        return f'{self.pk} - толықтыру'

    class Meta:
        verbose_name = _('Толықтыру')
        verbose_name_plural = _('Толықтырулар')


# Task type: Test model
# ----------------------------------------------------------------------------------------------------------------------
# Question model
class Question(models.Model):
    QUESTION_TYPE = (
        ('simple', _('Бір жауапты')),
        ('multiple', _('Көп жауапты')),
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True,
        related_name='questions', verbose_name=_('Тапсырма')
    )
    text = models.TextField(_('Сұрақ'))
    question_type = models.CharField(_('Сұрақтың түрі'), choices=QUESTION_TYPE, default='simple', max_length=32)
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'Тест: {self.pk} - сұрақ'

    class Meta:
        verbose_name = _('Тест сұрағы')
        verbose_name_plural = _('Тест сұрақтары')
        ordering = ('order', )


# Option model
class Option(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        related_name='options', verbose_name=_('Сұрақ')
    )
    text = models.TextField(_('Жауап'), blank=True, null=True)
    is_correct = models.BooleanField(_('Дұрыс жауап'), default=False)
    score = models.PositiveIntegerField(_('Балл'), default=0)

    def __str__(self):
        return f'Тест: {self.pk} - жауап'

    class Meta:
        verbose_name = _('Жауап')
        verbose_name_plural = _('Жауаптар')


# Task type: Matching model
# ----------------------------------------------------------------------------------------------------------------------
# MatchingColumn model
class MatchingColumn(models.Model):
    task = models.ForeignKey(
        Task, related_name='columns',
        on_delete=models.CASCADE, verbose_name=_('Тапсырма')
    )
    label = models.TextField(_('Атауы'))
    order = models.PositiveIntegerField(_('Реттілігі'), default=0)

    def __str__(self):
        return f'Сәйкес баған: {self.label} - бағаны'

    class Meta:
        verbose_name = _('Сәйкес баған')
        verbose_name_plural = _('Сәйкес бағандар')


# MatchingItem model
class MatchingItem(models.Model):
    correct_column = models.ForeignKey(
        MatchingColumn, related_name='correct_items',
        on_delete=models.CASCADE, verbose_name=_('Тапсырма')
    )
    text = models.TextField(_('Жауабы'), null=True, blank=True)

    def __str__(self):
        return self.text[:32]

    class Meta:
        verbose_name = _('Сәйкес элемент')
        verbose_name_plural = _('Сәйкес элементтер')


# Task type: Table model
# ----------------------------------------------------------------------------------------------------------------------
# TableColumn
class TableColumn(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='table_columns', verbose_name=_('Тапсырма')
    )
    label = models.TextField(_('Баған атауы'))
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'Баған: {self.label[:32]}'

    class Meta:
        verbose_name = _('Кесте бағаны')
        verbose_name_plural = _('Кесте бағандары')
        ordering = ('order', )


# TableRow
class TableRow(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='table_rows', verbose_name=_('Тапсырма')
    )
    label = models.TextField(_('Қатар атауы'))
    order = models.PositiveIntegerField(_('Реттілік нөмері'), default=0)

    def __str__(self):
        return f'Қатар: {self.label[:32]}'

    class Meta:
        verbose_name = _('Кесте қатары')
        verbose_name_plural = _('Кесте қатарлары')
        ordering = ('order', )

# TableCell
class TableCell(models.Model):
    row = models.ForeignKey(TableRow, on_delete=models.CASCADE, related_name='correct_cells', verbose_name='Қатар')
    column = models.ForeignKey(TableColumn, on_delete=models.CASCADE, related_name='correct_cells', verbose_name='Баған')
    correct = models.BooleanField('Дұрыс жауап', default=False)

    class Meta:
        verbose_name = 'Кесте ұяшығы (дұрыс жауап)'
        verbose_name_plural = 'Кесте ұяшықтары (дұрыс жауаптар)'
