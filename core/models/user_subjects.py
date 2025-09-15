from django.db import models
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from core.models import User, Subject, Lesson, Chapter


# UserSubject model
# ----------------------------------------------------------------------------------------------------------------------
class UserSubject(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name=_('Қолданушы'), related_name='user_subjects')
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        verbose_name=_('Пән'), related_name='user_subjects'
    )
    rating = models.PositiveSmallIntegerField(_('Жалпы бағасы'), default=0)
    percentage = models.DecimalField(_('Пайыздық мөлшері'), default=0, max_digits=5, decimal_places=2)
    is_completed = models.BooleanField(_('Орындалды'), default=False)
    created_at = models.DateTimeField(_('Басталған уақыты'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Орындалған уақыты'), blank=True, null=True)

    class Meta:
        verbose_name = _('Қолданушының пәні')
        verbose_name_plural = _('Қолданушының пәндері')

    def __str__(self):
        return f'{self.user} | {self.subject}'


# UserSubject model
# ----------------------------------------------------------------------------------------------------------------------
class UserChapter(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='user_chapters', verbose_name=_('Қолданушы')
    )
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE,
        related_name='user_chapters', verbose_name=_('Бөлім')
    )
    user_subject = models.ForeignKey(
        UserSubject, on_delete=models.CASCADE,
        related_name='user_chapters', verbose_name=_('Қолданушының пәндері')
    )
    rating = models.PositiveSmallIntegerField(_('Жалпы бағасы'), default=0)
    percentage = models.DecimalField(_('Пайыздық мөлшері'), default=0, max_digits=5, decimal_places=2)
    is_completed = models.BooleanField(_('Орындалды'), default=False)

    def __str__(self):
        return f'{self.user} | {self.chapter}'

    class Meta:
        verbose_name = _('Қолданушының пән бөлімі')
        verbose_name_plural = _('Қолданушының пән бөлімдері')


# UserLesson model
# ----------------------------------------------------------------------------------------------------------------------
class UserLesson(models.Model):
    LESSON_STATUS = (
        ('no-started', _('Сабақ басталмады')),
        ('in-progress', _('Сабақ өтілуде')),
        ('finished', _('Сабақ аяқталды')),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='user_lessons', verbose_name=_('Қолданушы')
    )
    user_subject = models.ForeignKey(
        UserSubject, on_delete=models.CASCADE,
        related_name='user_lessons',  verbose_name=_('Қолданушының пәні'))
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='user_lessons', verbose_name=_('Сабақ')
    )
    rating = models.PositiveSmallIntegerField(_('Жалпы бағасы'), default=0)
    percentage = models.DecimalField(_('Пайыздық мөлшері'), default=0, max_digits=5, decimal_places=2)
    status = models.CharField(_('Статус'), choices=LESSON_STATUS, max_length=64, default='no-started')
    started_at = models.DateTimeField(_('Басталған уақыты'), blank=True, null=True)
    completed_at = models.DateTimeField(_('Орындалған уақыты'), blank=True, null=True)
    is_completed = models.BooleanField(_('Орындалды'), default=False)

    class Meta:
        verbose_name = _('Қолданушының сабағы')
        verbose_name_plural = _('Қолданушының сабақтары')

    def __str__(self):
        return f'{self.user} | {self.lesson}'


    @property
    def time_spent(self) -> timedelta:
        from django.utils.timezone import now

        if not self.started_at:
            return timedelta(0)
        end_time = self.completed_at or now()
        return end_time - self.started_at

    @property
    def time_spent_hms(self) -> dict:
        total_seconds = int(self.time_spent.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return {
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
        }


# Feedback model
# ----------------------------------------------------------------------------------------------------------------------
class Feedback(models.Model):
    user_lesson = models.ForeignKey(
        UserLesson, on_delete=models.CASCADE,
        related_name='feedbacks', verbose_name=_('Қолданушының сабағы')
    )
    rating = models.IntegerField(_('Бағасы'), choices=[(1, 'Өте нашар'), (2, 'Нашар'), (3, 'Орташа'), (4, 'Жақсы'), (5, 'Тамаша')])
    comment = models.TextField(_('Пікір'), blank=True)
    created_at = models.DateTimeField(_('Жазылған уақыты'), auto_now_add=True)

    def __str__(self):
        return f'{self.user_lesson.user} - {self.user_lesson.lesson} - {self.rating}'

    class Meta:
        verbose_name = _('Кері байланыс')
        verbose_name_plural = _('Кері байланыстар')
