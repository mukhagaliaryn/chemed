from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.aggregates import Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from core.models import Subject, UserSubject, Lesson, UserChapter, UserLesson
from core.utils.decorators import role_required


# student dashboard page
# ----------------------------------------------------------------------------------------------------------------------
@login_required
@role_required('student')
def student_view(request):
    user = request.user
    subjects = Subject.objects.all()
    user_subjects_qs = UserSubject.objects.filter(user=user).prefetch_related(
        'user_chapters__chapter',
        'user_lessons__lesson__chapter'
    )
    user_subjects = {us.subject_id: us for us in user_subjects_qs}
    average_percentage = user_subjects_qs.aggregate(avg=Avg('percentage'))['avg'] or 0

    subject_list = []
    for subject in subjects:
        user_subject = user_subjects.get(subject.id)

        first_user_chapter = user_subject.user_chapters.first() if user_subject else None
        first_chapter = first_user_chapter

        first_user_lesson = (
            user_subject.user_lessons.filter(lesson__chapter=first_chapter.chapter).first()
            if user_subject and first_chapter else None
        )
        first_lesson = first_user_lesson

        completed_chapter_count = 0
        completed_lesson_count = 0

        if user_subject:
            completed_chapter_count = user_subject.user_chapters.filter(is_completed=True).count()
            completed_lesson_count = user_subject.user_lessons.filter(is_completed=True).count()

        subject_students = UserSubject.objects.filter(subject=subject).select_related('user')[:3]

        subject_list.append({
            'subject': subject,
            'user_subject': user_subject,
            'first_chapter': first_chapter,
            'first_lesson': first_lesson,
            'completed_chapter_count': completed_chapter_count,
            'completed_lesson_count': completed_lesson_count,
            'students': subject_students,
        })

    context = {
        'statistics': {
            'in_process': user_subjects_qs.filter(is_completed=False).count(),
            'completed': user_subjects_qs.filter(is_completed=True).count(),
            'average_percentage': round(average_percentage),
        },
        'subject_list': subject_list,
    }
    return render(request, 'app/dashboard/student/page.html', context)


# Subject detail page
# ----------------------------------------------------------------------------------------------------------------------
@login_required
@role_required('student')
def subject_detail_view(request, pk):
    user = request.user
    subject = get_object_or_404(Subject, pk=pk)
    user_subject = (
        UserSubject.objects
        .filter(user=user, subject=subject)
        .prefetch_related('user_chapters__chapter', 'user_lessons__lesson__chapter')
        .first()
    )

    first_chapter_id = None
    first_lesson_id = None

    if user_subject:
        first_user_chapter = user_subject.user_chapters.first()
        if first_user_chapter:
            first_chapter_id = first_user_chapter.id

            first_user_lesson = user_subject.user_lessons.filter(
                lesson__chapter=first_user_chapter.chapter
            ).first()
            if first_user_lesson:
                first_lesson_id = first_user_lesson.id

    chapters = []
    for chapter in subject.chapters.all():
        lessons = []
        for lesson in chapter.lessons.all():
            lesson_duration = sum(task.duration for task in lesson.tasks.all())
            lessons.append({
                'lesson': lesson,
                'duration': lesson_duration,
            })

        chapters.append({
            'chapter': chapter,
            'lessons': lessons,
        })

    context = {
        'subject': subject,
        'user_subject': user_subject,
        'first_chapter_id': first_chapter_id,
        'first_lesson_id': first_lesson_id,
        'chapters': chapters,
    }
    return render(request, 'app/dashboard/student/subject/page.html', context)


# Enroll subject handler
# ----------------------------------------------------------------------------------------------------------------------
@login_required
@role_required('student')
def enroll_user_to_subject(request, subject_id):
    user = request.user
    subject = get_object_or_404(Subject, pk=subject_id)

    if not subject.chapters.exists() or not Lesson.objects.filter(chapter__subject=subject).exists():
        messages.warning(request, _('Бұл пәнде бөлімдер мен сабақтар әлі қосылмаған'))
        return redirect('student')

    user_subject, __ = UserSubject.objects.get_or_create(user=user, subject=subject)

    for chapter in subject.chapters.all():
        UserChapter.objects.get_or_create(user_subject=user_subject, user=user, chapter=chapter)

        for lesson in chapter.lessons.all():
            UserLesson.objects.get_or_create(user_subject=user_subject, user=user, lesson=lesson)

    messages.success(request, _('Пән қосылды!'))
    return redirect('student')
