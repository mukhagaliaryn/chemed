from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.aggregates import Avg
from django.http import HttpResponse
from django.shortcuts import render

from core.models import Subject, UserSubject, UserChapter, UserLesson, User
from core.utils.decorators import role_required


@login_required
@role_required('teacher')
def teacher_view(request):
    user = request.user
    subjects_data = []

    for subject in Subject.objects.all():
        user_subjects = UserSubject.objects.filter(subject=subject)

        student_count = user_subjects.count()
        subject_avg = user_subjects.aggregate(
            avg_rating=Avg('rating'),
            avg_percentage=Avg('percentage')
        )
        chapter_stats = UserChapter.objects.filter(user_subject__subject=subject).aggregate(
            avg_rating=Avg('rating'),
            avg_percentage=Avg('percentage')
        )
        lesson_stats = UserLesson.objects.filter(user_subject__subject=subject).aggregate(
            avg_rating=Avg('rating'),
            avg_percentage=Avg('percentage')
        )

        def safe_round(value, digits=0):
            return round(value, digits) if value is not None else 0

        subjects_data.append({
            'subject': subject,
            'student_count': student_count,

            # UserSubject
            'subject_avg_rating': safe_round(subject_avg['avg_rating']),
            'subject_avg_percentage': safe_round(subject_avg['avg_percentage'], 2),

            'chapter_avg_rating': safe_round(chapter_stats['avg_rating']),
            'chapter_avg_percentage': safe_round(chapter_stats['avg_percentage'], 2),

            'lesson_avg_rating': safe_round(lesson_stats['avg_rating']),
            'lesson_avg_percentage': safe_round(lesson_stats['avg_percentage'], 2),
        })

    # Барлық оқушылар
    q = request.GET.get('q', '').strip()
    classroom = request.GET.get('user_class', '').strip()

    # Бастапқы users queryset
    users = User.objects.filter(user_subjects__isnull=False).distinct()

    if q:
        users = users.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(username__icontains=q)
        )

    if classroom:
        users = users.filter(user_class=classroom)

    students_data = []
    for user in users:
        user_subject_qs = user.user_subjects.all()
        subject_stats = user_subject_qs.aggregate(
            avg_rating=Avg('rating'),
            avg_percentage=Avg('percentage')
        )
        chapter_stats = user.user_chapters.all().aggregate(
            avg_rating=Avg('rating'),
            avg_percentage=Avg('percentage')
        )
        lesson_stats = user.user_lessons.all().aggregate(
            avg_rating=Avg('rating'),
            avg_percentage=Avg('percentage')
        )

        students_data.append({
            'user': user,
            'subject_avg_rating': round(subject_stats['avg_rating']) or 0,
            'subject_avg_percentage': round(subject_stats['avg_percentage'], 2) or 0,

            'chapter_avg_rating': round(chapter_stats['avg_rating']) or 0,
            'chapter_avg_percentage': round(chapter_stats['avg_percentage'], 2) or 0,

            'lesson_avg_rating': round(lesson_stats['avg_rating']) or 0,
            'lesson_avg_percentage': round(lesson_stats['avg_percentage'], 2) or 0,
        })

    context = {
        'generics': {
            'classes_count': 2,
            'subjects_count': Subject.objects.all().count(),
            'students_count': UserSubject.objects.all().count()
        },
        'subjects_data': subjects_data,
        'students_data': students_data,
    }
    return render(request, 'app/dashboard/teacher/page.html', context)
