from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django_summernote.admin import SummernoteModelAdmin, SummernoteModelAdminMixin
from core.models import Task, Question, Option, Written, TextGap, Video, MatchingColumn, MatchingItem, TableColumn, \
    TableRow, TableCell


# Task admin
# ----------------------------------------------------------------------------------------------------------------------
# Video Tab
class VideoTab(admin.TabularInline):
    model = Video
    extra = 0


# Written Tab
class WrittenTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = Written
    extra = 0


# TextGap Tab
class TextGapTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = TextGap
    extra = 0


# Question Tab
class QuestionTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = Question
    fields = ('order', 'text', 'question_type', 'view_link', )
    extra = 0
    readonly_fields = ('view_link', )

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_question_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = 'Сұраққа сілтеме'


# Matching Tab
class MatchingColumnTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = MatchingColumn
    extra = 0
    readonly_fields = ('view_link', )

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_matchingcolumn_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = 'Сәйкес бағанға сілтеме'


# TableColumnTab
class TableColumnTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = TableColumn
    extra = 0
    readonly_fields = ('view_link', )

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_tablecolumn_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = 'Бағанға сілтеме'


# TableRowTab
class TableRowTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = TableRow
    extra = 0
    readonly_fields = ('view_link', )

    def view_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_tablerow_change', args=[obj.pk])
            return format_html('<a href="{}" class="view-link">Толығырақ</a>', url)
        return '-'

    view_link.short_description = 'Қатарға сілтеме'


# ----------------------- Task admin -----------------------
@admin.register(Task)
class TaskAdmin(SummernoteModelAdmin):
    list_display = ('lesson', 'rating', 'duration', 'order', )
    readonly_fields = ('lesson_link', )

    def lesson_link(self, obj):
        if obj.lesson:
            url = reverse('admin:core_lesson_change', args=[obj.lesson.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.lesson.title)
        return '-'

    lesson_link.short_description = 'Сабаққа сілтеме'

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []

        inline_instances = []

        if obj.task_type == 'video':
            inline_instances = [VideoTab(self.model, self.admin_site)]
        elif obj.task_type == 'written':
            inline_instances = [WrittenTab(self.model, self.admin_site)]
        elif obj.task_type == 'text_gap':
            inline_instances = [TextGapTab(self.model, self.admin_site)]
        elif obj.task_type == 'test':
            inline_instances = [QuestionTab(self.model, self.admin_site)]
        elif obj.task_type == 'matching':
            inline_instances = [MatchingColumnTab(self.model, self.admin_site)]
        elif obj.task_type == 'table':
            inline_instances = [
                TableColumnTab(self.model, self.admin_site),
                TableRowTab(self.model, self.admin_site),
            ]

        return inline_instances


# Task type:Test admin
# ----------------------------------------------------------------------------------------------------------------------
# Option Tab
class OptionTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = Option
    fields = ('text', 'is_correct', )
    extra = 0


# Question Admin
@admin.register(Question)
class QuestionAdmin(SummernoteModelAdmin):
    readonly_fields = ('task_link', )
    inlines = (OptionTab, )

    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:core_task_change', args=[obj.task.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.task)
        return '—'

    task_link.short_description = 'Сұраққа сілтеме'


# Task type:TextGap admin
# ----------------------------------------------------------------------------------------------------------------------
@admin.register(TextGap)
class TextGapAdmin(SummernoteModelAdmin):
    readonly_fields = ('task_link',)

    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:core_task_change', args=[obj.task.id])
            return format_html('<a href="{}" class="view-link">🔗 {} тапсырмасына өту</a>', url, obj.task.get_task_type_display())
        return '— тапсырмамен байланыспаған'

    task_link.short_description = 'Тапсырмаға сілтеме'


# Task type:MatchingColumn admin
# ----------------------------------------------------------------------------------------------------------------------
# MatchingItemTab
class MatchingItemTab(SummernoteModelAdminMixin, admin.TabularInline):
    model = MatchingItem
    extra = 0


# MatchingColumnAdmin
@admin.register(MatchingColumn)
class MatchingColumnAdmin(SummernoteModelAdmin):
    list_display = ('label', 'task', )
    inlines = (MatchingItemTab, )
    readonly_fields = ('task_link',)

    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:core_task_change', args=[obj.task.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.task.get_task_type_display())
        return '—'

    task_link.short_description = 'Тапсырмаға сілтеме'


# Task type:Table admin
# ----------------------------------------------------------------------------------------------------------------------
class TableCellTab(admin.TabularInline):
    model = TableCell
    extra = 0

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        obj = getattr(self, 'parent_object', None)

        if obj:
            if db_field.name == 'row':
                field.queryset = TableRow.objects.filter(task=obj.task)
            elif db_field.name == 'column':
                field.queryset = TableColumn.objects.filter(task=obj.task)

        return field

    def get_formset(self, request, obj=None, **kwargs):
        # parent_object-ті formfield үшін сақтап қоямыз
        self.parent_object = obj
        return super().get_formset(request, obj, **kwargs)


# TableColumnAdmin
@admin.register(TableColumn)
class TableColumnAdmin(SummernoteModelAdmin):
    list_display = ('label', 'task', )
    readonly_fields = ('task_link', )
    inlines = (TableCellTab, )

    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:core_task_change', args=[obj.task.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.task)
        return '-'

    task_link.short_description = 'Тапсырмаға сілтеме'


# TableRowAdmin
@admin.register(TableRow)
class TableRowAdmin(SummernoteModelAdmin):
    list_display = ('label', 'task', )
    readonly_fields = ('task_link', )
    inlines = (TableCellTab, )

    def task_link(self, obj):
        if obj.task:
            url = reverse('admin:core_task_change', args=[obj.task.id])
            return format_html('<a href="{}" class="view-link">🔗 {}</a>', url, obj.task)
        return '-'

    task_link.short_description = 'Тапсырмаға сілтеме'
