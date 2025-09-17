from django.contrib import messages
from core.models import Option, TableCell


# user_lesson_task_view
# ----------------------------------------------------------------------------------------------------------------------
# get_related_data
def get_related_data(user_task):
    task_type = user_task.task.task_type
    data = {}

    if task_type == 'video':
        data['user_videos'] = user_task.user_videos.all()

    elif task_type == 'written':
        data['user_written'] = user_task.user_written.all()

    elif task_type == 'text_gap':
        data['user_text_gaps'] = user_task.user_text_gaps.all()

    elif task_type == 'test':
        data['user_answers'] = user_task.user_options.select_related('question').prefetch_related('options').order_by('question__order')

    elif task_type == 'matching':
        data['user_matchings'] = user_task.matching_answers.all()

    elif task_type == 'table':
        rows = user_task.task.table_rows.order_by('order')
        columns = user_task.task.table_columns.order_by('order')
        answers = user_task.user_table_answers.select_related('row', 'column')

        # Қолданушы жауаптары
        answer_matrix = {row.id: {} for row in rows}
        for ans in answers:
            answer_matrix[ans.row.id][ans.column.id] = ans

        # Дұрыс жауаптар
        correct_cells = TableCell.objects.filter(
            row__task=user_task.task,
            column__task=user_task.task
        )
        correct_matrix = {row.id: {} for row in rows}
        for cell in correct_cells:
            correct_matrix[cell.row_id][cell.column_id] = cell.correct

        data.update({
            'table_rows': rows,
            'table_columns': columns,
            'answer_matrix': answer_matrix,
            'correct_matrix': correct_matrix,
        })

    return data


# handle_post_request
def handle_post_request(request, user_task):
    handlers = {
        'video': handle_video,
        'written': handle_written,
        'text_gap': handle_text_gap,
        'test': handle_test,
        'matching': handle_matching,
        'table': handle_table,
    }
    handler = handlers.get(user_task.task.task_type)
    if handler:
        return handler(request, user_task)


# ---------------------- VIDEO ----------------------
def handle_video(request, user_task):
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


# ---------------------- WRITTEN ----------------------
def handle_written(request, user_task):
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


# ---------------------- TEST ----------------------
def handle_test(request, user_task):
    questions = [ua.question for ua in user_task.user_options.all()]
    total_questions = len(questions)
    total_score = 0  # барлық сұрақтан жинайтын ұпай

    for user_answer in user_task.user_options.select_related('question').prefetch_related('question__options'):
        question = user_answer.question
        selected_ids = request.POST.getlist(f'question_{question.id}')
        selected_ids = list(map(int, selected_ids)) if selected_ids else []

        # Валидті жауаптарды қалдырамыз
        valid_ids = set(question.options.values_list('id', flat=True))
        selected_ids = [opt_id for opt_id in selected_ids if opt_id in valid_ids]

        # Қолданушы таңдауларын сақтау
        selected_options = Option.objects.filter(id__in=selected_ids)
        user_answer.options.set(selected_options)

        # Дұрыс жауаптар
        correct_ids = set(question.options.filter(is_correct=True).values_list('id', flat=True))
        selected_set = set(selected_ids)

        # -------------------------
        # Бағалау логикасы
        # -------------------------
        if question.question_type == 'simple':
            # Тек 1 дұрыс таңдау болса ғана дұрыс
            if len(selected_set) == 1 and selected_set.pop() in correct_ids:
                total_score += 1

        elif question.question_type == 'multiple':
            if correct_ids:
                correct_selected = len(selected_set & correct_ids)   # дұрыс таңдалғандар
                wrong_selected = len(selected_set - correct_ids)    # артық/қате таңдалғандар

                # Дұрыс үлесті есептеу (қате таңдаулар да әсер етеді)
                partial_score = (correct_selected - wrong_selected) / len(correct_ids)
                if partial_score < 0:
                    partial_score = 0  # минусқа түсіп кетпесін

                total_score += partial_score
            else:
                # Егер дұрыс жауаптар мүлдем болмаса
                total_score += 0

    # Жалпы ұпайды есептеу
    full_rating = user_task.task.rating or 1

    if total_questions == 0:
        score = 0
        messages.error(request, 'Тестте сұрақтар жоқ.')
    else:
        ratio = total_score / total_questions
        score = round(full_rating * ratio)

        if ratio == 1:
            messages.success(request, 'Барлық сұраққа дұрыс жауап бердіңіз!')
        elif ratio == 0:
            messages.error(request, 'Барлық жауап қате.')
        else:
            messages.info(
                request,
                f'Ұпай {score} қойылды ({round(ratio*100)}% дұрыс жауап).'
            )

    # Нәтижені сақтау
    user_task.rating = score
    user_task.is_completed = True
    user_task.save()


# ---------------------- MATCHING ----------------------
def handle_matching(request, user_task):
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


# ---------------------- TEXT GAP ----------------------
def handle_text_gap(request, user_task):
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


# ---------------------- TABLE ----------------------
def handle_table(request, user_task):
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
