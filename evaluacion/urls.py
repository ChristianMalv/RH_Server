from django.urls import path
from .views import *

urls_evaluacion = [
    path('crear/', CreateEvaluacionView.as_view()),
    path('lista/', ListaEvaluacionView.as_view()),
    path('', AnswerView.as_view()),
]
