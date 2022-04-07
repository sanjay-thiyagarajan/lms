from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.loginApp, name='login'),
    path('signup/', views.register_student, name='signup'),
    path('view-profile/', views.view_profile, name='view_profile'),
    path('logout/', views.logoutApp, name='logout'),
    path('books/', views.books, name='books'),
    path('students/', views.students, name='students'),
    path('delete-student/<int:student_id>/', views.student_del_handler),
    path('delete-book/<int:book_id>/', views.book_del_handler),
    path('return-book/<int:borrow_id>/', views.return_book),
    path('add-book/', views.add_book, name='add-book'),
    path('add-student/', views.add_student, name='add-student'),
    path('add-booking/<int:book_id>/', views.add_booking, name='add-booking'),
    path('student-profile/', views.student_profile, name='student_profile'),
    path('wallet/', views.wallet_view, name='wallet_view'),
    path('bookings/', views.bookings, name='bookings'),
    path('reset_password/',
        auth_views.PasswordResetView.as_view(template_name="panel/password_reset.html"),
        name="reset_password"),
    path('reset_password_sent/',
        auth_views.PasswordResetDoneView.as_view(template_name="panel/password_reset_sent.html"),
        name="password_reset_done"),
    path('reset_password/<uidb64>/<token>',
        auth_views.PasswordResetConfirmView.as_view(template_name="panel/password_reset_confirm.html"),
        name="password_reset_confirm"),
    path('reset_password_complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name="panel/password_reset_done.html"),
        name="password_reset_complete")
]