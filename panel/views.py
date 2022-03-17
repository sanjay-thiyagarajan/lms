from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Student, Book, Borrow
from django.utils import timezone
from datetime import datetime
from panel.qSort import qSort
from panel.decorators import unAuthenticated_user
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import LogEntry

@unAuthenticated_user
def loginApp(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(home)
        else:
            return render(request, 'panel/login.html', {'message': 'Invalid credentials'})
    return render(request, 'panel/login.html')

@login_required(login_url='login')
def home(request):
    book_count = Book.objects.count
    borrow_count = Borrow.objects.count

    pending_returns = 0

    borrows = list(Borrow.objects.all())
    for b in borrows:
        if b.due_date < timezone.now().date():
            diff = datetime.now().date() - b.due_date
            fine = diff.days * 0.75
            b.fine_amount = fine
            b.save()
        else:
            borrows.remove(b)
    # Total fine calculation
    borrow_fine = list(Borrow.objects.filter().values_list('fine_amount', flat=True))
    total_fine = sum(borrow_fine)

    #Finding the pending returns
    for s in borrow_fine:
        if s > 0:
            pending_returns += 1
    qSort(borrows, 'fine_amount')
    borrows = borrows[-5:]

    #Books in demand
    books = list(Book.objects.all())
    demand_books = []
    for b in books:
        bk = list(Borrow.objects.filter(book=b).values_list('book', flat=True))
        if len(bk) == b.copies:
            demand_books.append(b)
    data = {'book_count': book_count, 'borrow_count': borrow_count, 'total_fine': total_fine, 'pending_returns':pending_returns}
    if pending_returns != 0:
        data['borrows'] = borrows
    if len(demand_books) != 0:
        data['demand_books'] = demand_books
    return render(request, 'panel/index.html', data)

#Books listing
@login_required(login_url='login')
def books(request):
    books = list(Book.objects.all())
    if request.method == 'POST':
        key = request.POST.get('sort_by')
        qSort(books, key.lower())
    return render(request, 'panel/books.html', {'books': books})

#Students listing
@login_required(login_url='login')
def students(request):
    borrows = list(Borrow.objects.all())
    for b in borrows:
        if b.due_date < timezone.now().date():
            diff = datetime.now().date() - b.due_date
            fine = diff.days * 0.75
            b.fine_amount = fine
            b.save()
    students = list(Student.objects.all())
    stud_db = []
    for s in students:
        students_db = {}
        temp = list(Borrow.objects.filter(borrower=s).values_list('fine_amount', flat=True))
        students_db['fullname'] = s.fullname
        students_db['roll_number'] = s.roll_number
        students_db['academic_year'] = s.academic_year
        students_db['email'] = s.email
        students_db['fine'] = sum(temp)
        stud_db.append(students_db)
    if request.method == 'POST':
        key = request.POST.get('sort_by')
        qSort(students, key.lower())
    return render(request, 'panel/students.html', {'students': stud_db})

#Borrow listing
@login_required(login_url='login')
def borrows(request):
    borrows = list(Borrow.objects.all())
    if request.method == 'POST':
        key = request.POST.get('sort_by')
        qSort(borrows, key.lower())
    for b in borrows:
        if b.due_date < timezone.now().date():
            diff = datetime.now().date() - b.due_date
            fine = diff.days * 0.75
            b.fine_amount = fine
            b.save()
    return render(request, 'panel/borrows.html', {'borrows': borrows})

# Add Books
@login_required(login_url='login')
def add_book(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn_number = request.POST.get('isbn_number')
        copies = request.POST.get('copies')
        book = Book(
            isbn_number=isbn_number,
            title=title,
            author=author,
            copies=copies
            )
        book.save()
        return redirect('books')
    return render(request, 'panel/add-book.html')

# Add Students
@login_required(login_url='login')
def add_student(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        roll_number = request.POST.get('roll_number')
        academic_year = request.POST.get('academic_year')
        email = roll_number.lower() + '@ch.students.amrita.edu'
        student = Student(
            fullname=fullname,
            roll_number=roll_number,
            academic_year=academic_year,
            email=email
        )
        student.save()
        return redirect('students')
    return render(request, 'panel/add-student.html')

@login_required(login_url='login')
def add_borrow(request):
    students = Student.objects.all()
    books = Book.objects.all()
    data = {'students': students, 'books': books}
    if request.method == 'POST':
        borrower = request.POST.get('borrower')
        due_date = request.POST.get('due_date')
        book = request.POST.get('book')
        # Check book availability
        bookobj = Book.objects.get(title=book)
        bk = list(Borrow.objects.filter(book=bookobj).values_list('book', flat=True))
        if len(bk) < bookobj.copies:
            borrow = Borrow(
                borrower=Student.objects.get(fullname=borrower),
                due_date=due_date,
                book=Book.objects.get(title=book)
            )
            borrow.save()
            return redirect('borrows')
        else:
            data['error'] = 'The requested book is not in stock'
    return render(request, 'panel/add-borrow.html', data )

#Returning books
@login_required(login_url='login')
def return_book(request, borrow_id):
    brw = Borrow.objects.get(id = borrow_id)
    if brw.due_date < timezone.now().date():
        color = 'red'
    else:
        color = 'green'
    if request.method == 'POST':
        brw.delete()
        return redirect('borrows')
    return render(request, 'panel/return-book.html', {'borrow': brw, 'color': color})

@login_required(login_url='login')
def activity_log(request):
    logs = list(LogEntry.objects.all())
    return render(request, 'panel/activity-log.html', {'logs':logs})

#Deleting books
@login_required(login_url='login')
def book_del_handler(request, book_id):
    Book.objects.get(id=book_id).delete()
    return redirect('books')

#Deleting students
@login_required(login_url='login')
def student_del_handler(request, student_id):
    Student.objects.get(id=student_id).delete()
    return redirect('students')

def logoutApp(request):
    logout(request)
    return redirect(loginApp)