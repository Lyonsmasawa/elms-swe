from django.urls import path
from . import views

urlpatterns = [
    path('quiz/<str:code>', views.quiz, name='quiz'),
    path('addQuestion/<str:code>/<str:quiz_id>', views.addQuestion, name='addQuestion'),
    path('allQuizzes/<str:code>', views.allQuizzes, name='allQuizzes'),
    path('quizSummary/<str:code>/<str:quiz_id>', views.quizSummary, name='quizSummary'),
    path('myQuizzes/<str:code>', views.myQuizzes, name='myQuizzes'),
    path('startQuiz/<str:code>/<str:quiz_id>', views.startQuiz, name='startQuiz'),
    path('studentAnswer/<str:code>/<str:quiz_id>', views.studentAnswer, name='studentAnswer'),
    path('quizResult/<str:code>/<str:quiz_id>', views.quizResult, name='quizResult'),
  
]