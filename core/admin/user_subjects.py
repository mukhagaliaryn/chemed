from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_summernote.admin import SummernoteModelAdminMixin

from core.models import UserSubject, UserLesson, UserChapter, UserTask, Feedback


# UserSubject admin
# ----------------------------------------------------------------------------------------------------------------------
# UserChapter Tab
class UserChapterTab(admin.TabularInline):
    model = UserChapter
    extra = 0


# UserLesson Tab
class UserLessonTab(admin.StackedInline):
    model = UserLesson
    extra = 0
    readonly_fields = ('view_link',)

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_userlesson_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = _('Қолданушының сабағы')


# UserSubject admin
@admin.register(UserSubject)
class UserSubjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'rating', 'percentage', 'created_at', 'is_completed', )
    list_filter = ('user', 'subject', 'is_completed', )
    search_fields = ('user__username', 'subject__title')
    inlines = (UserChapterTab, UserLessonTab, )


# UserLesson admin
# ----------------------------------------------------------------------------------------------------------------------
class UserTaskTab(admin.TabularInline):
    model = UserTask
    extra = 0
    readonly_fields = ('view_link',)

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_usertask_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = _('Қолданушының тапсырмасы')


# Feedback Tab
class FeedbackTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = Feedback
    extra = 0


@admin.register(UserLesson)
class UserLessonAdmin(admin.ModelAdmin):
    list_display = ('user_subject', 'lesson', 'rating', 'percentage', 'is_completed', 'completed_at', )
    list_filter = ('user_subject', 'lesson', 'is_completed', )
    search_fields = ('user__username', 'lesson__title')
    inlines = (UserTaskTab, FeedbackTab, )
    readonly_fields = ('user_subject_link',)

    def user_subject_link(self, obj):
        if obj.user_subject:
            url = reverse('admin:core_usersubject_change', args=[obj.user_subject.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.user_subject)
        return '-'

    user_subject_link.short_description = 'Қолданушының пәні'
