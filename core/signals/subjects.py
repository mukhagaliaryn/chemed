from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Lesson, UserSubject, UserChapter, UserLesson


@receiver(post_save, sender=Lesson)
def create_user_lessons_on_new_lesson(sender, instance, created, **kwargs):
    if not created:
        return

    lesson = instance
    subject = lesson.subject
    chapter = lesson.chapter

    user_subjects = UserSubject.objects.filter(subject=subject)

    for user_subject in user_subjects:
        user_chapter, _ = UserChapter.objects.get_or_create(
            user=user_subject.user,
            user_subject=user_subject,
            chapter=chapter
        )

        UserLesson.objects.get_or_create(
            user=user_subject.user,
            user_subject=user_subject,
            lesson=lesson
        )
