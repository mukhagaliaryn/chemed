from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django_summernote.admin import SummernoteModelAdminMixin
from core.models import UserTask, UserVideo, UserWritten, UserTextGap, UserAnswer, UserMatchingAnswer, UserTableAnswer


# UserTask admin
# ----------------------------------------------------------------------------------------------------------------------
class UserVideoTab(admin.TabularInline):
    model = UserVideo
    extra = 0


class UserWrittenTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = UserWritten
    extra = 0


class UserTextGapTab(admin.TabularInline):
    model = UserTextGap
    extra = 0


class UserAnswerTab(admin.TabularInline):
    model = UserAnswer
    extra = 0


class UserMatchingAnswerTab(admin.TabularInline):
    model = UserMatchingAnswer
    extra = 0


class UserTableAnswerTab(admin.TabularInline):
    model = UserTableAnswer
    extra = 0


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('user_lesson', 'task', 'submitted_at', 'rating', 'is_completed', )
    list_filter = ('user_lesson', 'task', 'is_completed', )
    readonly_fields = ('user_lesson_link', )

    def user_lesson_link(self, obj):
        if obj.user_lesson:
            url = reverse('admin:core_userlesson_change', args=[obj.user_lesson.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.user_lesson)
        return '-'

    user_lesson_link.short_description = 'Қолданушының сабағы'

    def get_inline_instances(self, request, obj=None):
        if obj is None or not obj.task:
            return []

        inlines = []

        match obj.task.task_type:
            case 'video':
                inlines = [UserVideoTab]
            case 'written':
                inlines = [UserWrittenTab]
            case 'text_gap':
                inlines = [UserTextGapTab]
            case 'test':
                inlines = [UserAnswerTab]
            case 'matching':
                inlines = [UserMatchingAnswerTab]
            case 'table':
                inlines = [UserTableAnswerTab]

        return [inline(self.model, self.admin_site) for inline in inlines]
