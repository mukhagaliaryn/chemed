from django.shortcuts import render, redirect


def main_view(request):
    if request.user.is_authenticated:
        return redirect('student')

    return render(request, 'app/page.html')