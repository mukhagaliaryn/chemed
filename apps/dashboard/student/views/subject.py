from django.db.models.aggregates import Avg
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from core.models import UserSubject, UserChapter, UserLesson, UserTask, UserVideo, UserWritten, UserTextGap, \
    UserAnswer, Option, Task, UserMatchingAnswer, Lesson, UserTableAnswer, Feedback, TableCell
from core.utils.decorators import role_required


# user_lesson page
# ----------------------------------------------------------------------------------------------------------------------
@login_required
@role_required('student')
def user_lesson_view(request, subject_id, chapter_id, lesson_id):
    user = request.user
    user_subject = get_object_or_404(UserSubject, user=user, pk=subject_id)
    user_lesson = get_object_or_404(UserLesson, user_subject=user_subject, pk=lesson_id)
    user_chapter = get_object_or_404(UserChapter, user_subject=user_subject, chapter=user_lesson.lesson.chapter)
    tasks = user_lesson.lesson.tasks.exclude(task_type='video')
    user_lessons_qs = UserLesson.objects.filter(user_subject=user_subject).order_by('lesson__order')

    # ------------------ link for user tasks ------------------
    first_task = (
        UserTask.objects
        .filter(user_lesson=user_lesson)
        .select_related('task')
        .order_by('task__order')
        .first()
    )

    # ------------------ prev, next links ------------------
    previous_lesson = None
    next_lesson = None

    lesson_list = list(user_lessons_qs)
    try:
        current_index = lesson_list.index(user_lesson)
        if current_index > 0:
            previous_lesson = lesson_list[current_index - 1]
        if current_index < len(lesson_list) - 1:
            next_lesson = lesson_list[current_index + 1]
    except ValueError:
        pass

    # ------------------ for navbar ------------------
    user_chapters = UserChapter.objects.filter(user_subject=user_subject).order_by('chapter__order')
    user_lessons_by_chapter = {}
    for ul in user_lessons_qs:
        chapter_id = ul.lesson.chapter_id
        lesson_tasks = ul.lesson.tasks.all()
        total_duration = sum(task.duration for task in lesson_tasks)
        ul.total_duration = total_duration
        user_lessons_by_chapter.setdefault(chapter_id, []).append(ul)

    context = {
        'user_subject': user_subject,
        'user_chapter': user_chapter,
        'user_lesson': user_lesson,
        'tasks': tasks,
        'first_task': first_task,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'total_duration': sum(task.duration for task in user_lesson.lesson.tasks.all()),
        'user_chapters': user_chapters,
        'user_lessons_by_chapter': user_lessons_by_chapter,
        'active_chapter_id': user_chapter.pk,
    }

    return render(request, 'app/dashboard/student/user/subject/chapter/lesson/page.html', context)


# actions
# ----------------------------------------------------------------------------------------------------------------------
# start lesson
@login_required
@role_required('student')
def lesson_start_handler(request, subject_id, chapter_id, lesson_id):
    user = request.user
    user_subject = get_object_or_404(UserSubject, user=user, pk=subject_id)
    user_chapter = get_object_or_404(UserChapter, user_subject=user_subject, pk=chapter_id)
    user_lesson = get_object_or_404(UserLesson, user_subject=user_subject, pk=lesson_id)

    if request.method != 'POST':
        return redirect('user_lesson', subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id)

    if not user_lesson.lesson.tasks.exists():
        messages.warning(request, 'Бұл сабақта ешқандай тапсырма жоқ!')
        return redirect('user_lesson', subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id)

    for task in user_lesson.lesson.tasks.all():
        user_task, created = UserTask.objects.get_or_create(
            user_lesson=user_lesson,
            task=task
        )

        if task.task_type == 'video':
            for video in task.videos.all():
                UserVideo.objects.get_or_create(
                    user_task=user_task,
                    video=video
                )

        elif task.task_type == 'written':
            for written in task.written.all():
                UserWritten.objects.get_or_create(
                    user_task=user_task,
                    written=written,
                )

        elif task.task_type == 'text_gap':
            for text_gap in task.text_gaps.all():
                UserTextGap.objects.get_or_create(
                    user_task=user_task,
                    text_gap=text_gap,
                )

        elif task.task_type == 'test':
            for question in task.questions.all():
                ua, created = UserAnswer.objects.get_or_create(
                    user_task=user_task,
                    question=question
                )
                ua.options.set([])

        elif task.task_type == 'matching':
            for column in task.columns.all():
                for item in column.correct_items.all():
                    UserMatchingAnswer.objects.get_or_create(
                        user_task=user_task,
                        item=item,
                    )

        elif task.task_type == 'table':
            rows = task.table_rows.all()
            columns = task.table_columns.all()
            for row in rows:
                for column in columns:
                    UserTableAnswer.objects.get_or_create(
                        user_task=user_task,
                        row=row,
                        column=column,
                    )

    user_lesson.status = 'in-progress'
    user_lesson.started_at = timezone.now()
    user_lesson.save()

    first_user_task = user_lesson.user_tasks.select_related('task').order_by('task__order').first()

    if first_user_task:
        messages.success(request, 'Сабақ басталды!')
        return redirect(
            'user_lesson_task',
            subject_id=subject_id,
            chapter_id=chapter_id,
            lesson_id=lesson_id,
            task_id=first_user_task.id
        )

    return redirect('user_lesson', subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id)


# finish lesson
@login_required
@role_required('student')
@require_POST
def lesson_finish_handler(request, subject_id, chapter_id, lesson_id):
    user = request.user

    user_subject = get_object_or_404(UserSubject, user=user, pk=subject_id)
    user_chapter = get_object_or_404(UserChapter, user_subject=user_subject, pk=chapter_id)
    user_lesson = get_object_or_404(UserLesson, user_subject=user_subject, pk=lesson_id)
    lesson = user_lesson.lesson
    user_tasks = UserTask.objects.filter(user_lesson=user_lesson)

    if user_lesson.is_completed:
        return redirect('user_lesson', subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id)

    # ---------------- Lesson type: lesson ----------------
    if lesson.lesson_type == 'lesson':
        total_rating = user_tasks.aggregate(total=Sum('rating')).get('total', 0)
        user_lesson.rating = total_rating
        user_lesson.percentage = int(round(user_lesson.rating))

    # ---------------- Lesson type: chapter ----------------
    elif lesson.lesson_type == 'chapter':
        section_rating = user_tasks.aggregate(total=Sum('rating')).get('total', 0)
        user_lesson.rating = section_rating
        user_lesson.percentage = int(round(user_lesson.rating))

        user_chapter.rating = section_rating
        user_chapter.save()

    # ---------------- Lesson type: quarter ----------------
    elif lesson.lesson_type == 'quarter':
        quarter_rating = user_tasks.aggregate(total=Sum('rating')).get('total', 0)
        user_lesson.rating = quarter_rating
        user_lesson.percentage = int(round(user_lesson.rating))

        completed_lessons = UserLesson.objects.filter(
            user_subject=user_subject,
            lesson__lesson_type='lesson',
            is_completed=True
        )
        avg_lesson_rating = completed_lessons.aggregate(avg=Avg('rating')).get('avg', 0) or 0
        completed_chapters = UserLesson.objects.filter(
            user_subject=user_subject,
            lesson__lesson_type='chapter',
            is_completed=True
        )
        avg_chapter_rating = completed_chapters.aggregate(avg=Avg('rating')).get('avg', 0) or 0

        completed_quarters = UserLesson.objects.filter(
            user_subject=user_subject,
            lesson__lesson_type='quarter',
            is_completed=True
        )
        avg_quarter_rating = completed_quarters.aggregate(avg=Avg('rating')).get('avg', 0) or 0
        total_subject_rating = (
                round(avg_lesson_rating * 0.25) +
                round(avg_chapter_rating * 0.25) +
                round(avg_quarter_rating * 0.5)
        )
        user_subject.rating = int(round(total_subject_rating))

    user_lesson.is_completed = True
    user_lesson.completed_at = timezone.now()
    user_lesson.status = 'finished'
    user_lesson.save()

    # ---------------- user_chapter percentages ----------------
    chapter_lessons = Lesson.objects.filter(chapter=lesson.chapter)
    user_chapter_lessons = UserLesson.objects.filter(user_subject=user_subject, lesson__in=chapter_lessons)
    chapter_total = user_chapter_lessons.count()
    chapter_completed = user_chapter_lessons.filter(is_completed=True).count()

    user_chapter.percentage = round((chapter_completed / chapter_total) * 100, 2) if chapter_total else 0
    user_chapter.is_completed = chapter_total > 0 and chapter_total == chapter_completed
    user_chapter.save()

    # ---------------- user_subject percentages ----------------
    subject_lessons = UserLesson.objects.filter(user_subject=user_subject)
    subject_total = subject_lessons.count()
    subject_completed = subject_lessons.filter(is_completed=True).count()

    user_subject.percentage = round((subject_completed / subject_total) * 100, 2) if subject_total else 0
    user_subject.is_completed = subject_total > 0 and subject_total == subject_completed
    if user_subject.is_completed:
        user_subject.completed_at = timezone.now()
    user_subject.save()

    messages.success(request, 'Сабақ сәтті аяқталды!')
    return redirect('user_lesson', subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id)

# Feedback handler
# ----------------------------------------------------------------------------------------------------------------------
@require_POST
@login_required
def feedback_handler(request, subject_id, chapter_id, lesson_id):
    user_lesson = get_object_or_404(UserLesson, id=lesson_id, user=request.user)

    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '')

    if not rating:
        return redirect('user_lesson', subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id)

    feedback, created = Feedback.objects.get_or_create(
        user_lesson=user_lesson,
        defaults={
            'rating': rating,
            'comment': comment,
        }
    )

    if not created:
        feedback.rating = rating
        feedback.comment = comment
        feedback.save()

    return redirect('user_lesson', subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id)


# user_lesson_task page
# ----------------------------------------------------------------------------------------------------------------------
@login_required
@role_required('student')
def user_lesson_task_view(request, subject_id, chapter_id, lesson_id, task_id):
    user = request.user
    user_subject = get_object_or_404(UserSubject, user=user, pk=subject_id)
    user_chapter = get_object_or_404(UserChapter, user_subject=user_subject, pk=chapter_id)
    user_lesson = get_object_or_404(UserLesson, user_subject=user_subject, pk=lesson_id)
    user_task = get_object_or_404(UserTask, pk=task_id)
    user_tasks = UserTask.objects.filter(user_lesson=user_lesson).order_by('task__order')

    # ---------------------- prev, next links ----------------------
    next_user_task = None
    prev_user_task = None

    task_list = list(user_tasks)
    try:
        current_index = task_list.index(user_task)
        if current_index > 0:
            prev_user_task = task_list[current_index - 1]
        if current_index < len(task_list) - 1:
            next_user_task = task_list[current_index + 1]
    except ValueError:
        pass

    # user tasks...
    related_data = {}
    task_type = user_task.task.task_type

    if task_type == 'video':
        related_data['user_videos'] = user_task.user_videos.all()

    elif task_type == 'written':
        related_data['user_written'] = user_task.user_written.all()

    elif task_type == 'text_gap':
        related_data['user_text_gaps'] = user_task.user_text_gaps.all()

    elif task_type == 'test':
        related_data['user_answers'] = user_task.user_options.select_related('question').prefetch_related('options')

    elif task_type == 'matching':
        related_data['user_matchings'] = user_task.matching_answers.all()

    elif task_type == 'table':
        rows = user_task.task.table_rows.order_by('order')
        columns = user_task.task.table_columns.order_by('order')
        answers = user_task.user_table_answers.select_related('row', 'column')

        # 1. Қолданушы жауаптары
        answer_matrix = {row.id: {} for row in rows}
        for answer in answers:
            answer_matrix[answer.row.id][answer.column.id] = answer

        # 2. Дұрыс жауаптар
        correct_cells = TableCell.objects.filter(
            row__task=user_task.task,
            column__task=user_task.task
        )

        correct_matrix = {row.id: {} for row in rows}
        for cell in correct_cells:
            correct_matrix[cell.row_id][cell.column_id] = cell.correct

        # 3. Контекстке жіберу
        related_data['table_rows'] = rows
        related_data['table_columns'] = columns
        related_data['answer_matrix'] = answer_matrix
        related_data['correct_matrix'] = correct_matrix

    all_tasks_completed = not user_tasks.exclude(is_completed=True).exists()

    # POST requests...
    if request.method == 'POST':
        # -------------- video --------------
        if task_type == 'video':
            videos = user_task.user_videos.all()
            for uv in videos:
                uv.watched_seconds = int(request.POST.get(f'watched_{uv.id}', 0))
                uv.is_completed = True
                uv.save()

            if all(uv.is_completed for uv in videos):
                user_task.is_completed = True
                user_task.rating = user_task.task.rating
                user_task.save()
                messages.success(request, 'Видеосабақ аяқталды')

        # -------------- written --------------
        elif task_type == 'written':
            for uw in user_task.user_written.all():
                answer = request.POST.get(f'answer_{uw.id}', '').strip()
                uploaded_file = request.FILES.get(f'file_{uw.id}')
                if answer or uploaded_file:
                    if answer:
                        uw.answer = answer
                    if uploaded_file:
                        uw.file = uploaded_file
                    uw.is_submitted = True
                    uw.save()

            messages.success(request, 'Барлық жауаптар жіберілді')

        # -------------- text_gap --------------
        elif task_type == 'text_gap':
            total = user_task.user_text_gaps.count()
            correct = 0

            for user_text_gap in user_task.user_text_gaps.all():
                user_answer = request.POST.get(f'answer_{user_text_gap.id}', '').strip()
                correct_answer = user_text_gap.text_gap.correct_answer.strip()

                is_correct = user_answer.lower() == correct_answer.lower()

                user_text_gap.answer = user_answer
                user_text_gap.is_correct = is_correct
                user_text_gap.save()

                if is_correct:
                    correct += 1

            incorrect = total - correct
            full_rating = user_task.task.rating

            if correct == total:
                user_task.rating = full_rating
                messages.success(request, 'Барлық жауап дұрыс')
            elif incorrect == 1:
                if full_rating == 1:
                    user_task.rating = 0
                    messages.warning(request,
                                     'Бір қате жібердіңіз. Бұл тапсырма тек 1 баллдық болғандықтан, ұпай берілмейді')
                else:
                    user_task.rating = int(full_rating / 2)
                    messages.info(request, 'Бір қате бар. Жарты ұпай алдыңыз')
            elif incorrect >= (total / 2):
                user_task.rating = 0
                messages.error(request, 'Қателер жартысынан көп. Ұпай берілмейді')
            else:
                if full_rating == 1:
                    user_task.rating = 0
                    messages.warning(request,
                                     'Кем дегенде бір дұрыс бар, бірақ тапсырма 1 баллдық болғандықтан ұпай берілмейді')
                else:
                    user_task.rating = int(full_rating / 2)
                    messages.warning(request, 'Бірнеше қате бар. Жарты ұпай алдыңыз')

            user_task.is_completed = True
            user_task.save()

        # -------------- test --------------
        elif task_type == 'test':
            total = user_task.user_options.count()
            correct = 0
            answered = 0
            has_incorrect_simple = False
            has_multiple_incorrect_count = 0

            for user_answer in user_task.user_options.select_related('question').prefetch_related('question__options'):
                question = user_answer.question
                selected_ids = request.POST.getlist(f'question_{question.id}')
                selected_ids = list(map(int, selected_ids)) if selected_ids else []

                if selected_ids:
                    answered += 1

                valid_ids = set(question.options.values_list('id', flat=True))
                selected_ids = [opt_id for opt_id in selected_ids if opt_id in valid_ids]

                selected_options = Option.objects.filter(id__in=selected_ids)
                user_answer.options.set(selected_options)

                correct_ids = set(question.options.filter(is_correct=True).values_list('id', flat=True))
                selected_set = set(selected_ids)

                if question.question_type == 'simple':
                    if len(selected_set) == 1 and selected_set.pop() in correct_ids:
                        correct += 1
                    else:
                        has_incorrect_simple = True

                elif question.question_type == 'multiple':
                    if selected_set == correct_ids:
                        correct += 1
                    else:
                        incorrect_count = len(selected_set - correct_ids)
                        if incorrect_count >= 1:
                            has_multiple_incorrect_count += incorrect_count

            full_rating = user_task.task.rating

            if answered == 0:
                messages.error(request, 'Сіз ешбір сұраққа жауап бермедіңіз.')
                return redirect(
                    'user_lesson_task',
                    subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id, task_id=task_id
                )

            if has_incorrect_simple:
                score = 0
                messages.error(request, 'Бір жауапты сұрақта қате бар — ұпай берілмейді.')
            elif has_multiple_incorrect_count == 1:
                score = full_rating / 2 if full_rating > 1 else 0
                messages.info(request, 'Көп жауапты сұрақта 1 қате бар. Жарты ұпай.')
            elif has_multiple_incorrect_count > 1:
                score = 0
                messages.error(request, 'Көп жауапты сұрақта бірнеше қате бар. Ұпай берілмейді.')
            elif correct == total:
                score = full_rating
                messages.success(request, 'Барлық жауап дұрыс!')
            else:
                score = full_rating / 2 if full_rating > 1 else 0
                messages.warning(request, 'Бірнеше қате бар. Жарты ұпай.')

            user_task.rating = round(score, 2)
            user_task.is_completed = True
            user_task.save()

        # -------------- matching --------------
        elif user_task.task.task_type == 'matching':
            for answer in user_task.matching_answers.all():
                selected_column_id = request.POST.get(f'column_{answer.item.id}')
                if selected_column_id:
                    answer.selected_column_id = int(selected_column_id)
                    answer.check_answer()

            answers = user_task.matching_answers.all()
            total = answers.count()
            correct = answers.filter(is_correct=True).count()
            wrong = total - correct

            full_rating = user_task.task.rating
            score = 0

            if wrong == 0:
                score = full_rating
            elif wrong == 1:
                score = full_rating / 2 if full_rating > 1 else 0
            elif wrong > total / 2:
                score = 0
            else:
                score = full_rating / 2 if full_rating > 1 else 0

            user_task.rating = round(score, 2)
            user_task.is_completed = True
            user_task.save()

            messages.success(request, 'Сәйкестендіру тапсырмасы аяқталды')

        # -------------- table --------------
        elif task_type == 'table':
            total = 0
            correct = 0

            # 1. Дұрыс жауаптар картасы
            correct_map = {
                (c.row_id, c.column_id): c.correct
                for c in TableCell.objects.filter(
                    row__task=user_task.task,
                    column__task=user_task.task
                )
            }

            # 2. Қолданушы жауаптарын қабылдау және сақтау
            for answer in user_task.user_table_answers.all():
                field_name = f'cell_{answer.row_id}_{answer.column_id}'
                is_checked = request.POST.get(field_name) == 'on'

                answer.checked = is_checked
                answer.is_submitted = True
                answer.save()

                # 3. Бағалау үшін салыстыру
                expected = correct_map.get((answer.row_id, answer.column_id), False)
                if expected == is_checked:
                    correct += 1
                total += 1

            # 4. Ұпай есептеу
            rating = user_task.task.rating or 1
            if correct == total:
                score = rating
            elif correct >= total * 0.5:
                score = int(rating / 2)
            else:
                score = 0

            user_task.rating = score
            user_task.is_completed = True
            user_task.save(update_fields=['rating', 'is_completed'])

            messages.success(request, 'Кесте толтыру тапсырмасы аяқталды')

        return redirect(
            'user_lesson_task',
            subject_id=subject_id, chapter_id=chapter_id, lesson_id=lesson_id, task_id=task_id
        )

    context = {
        'user_subject': user_subject,
        'user_chapter': user_chapter,
        'user_lesson': user_lesson,
        'user_task': user_task,
        'user_tasks': user_tasks,
        'task_type': task_type,

        'all_tasks_completed': all_tasks_completed,
        'next_user_task': next_user_task,
        'prev_user_task': prev_user_task,
        **related_data
    }

    return render(request, 'app/dashboard/student/user/subject/chapter/lesson/task/page.html', context)
