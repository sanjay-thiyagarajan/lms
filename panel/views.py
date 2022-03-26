import re
from django.forms import ValidationError
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
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

def updateFine():
    borrows = list(Borrow.objects.all())
    for b in borrows:
        if b.due_date < timezone.now().date():
            diff = datetime.now().date() - b.due_date
            fine = diff.days * 0.75
            b.fine_amount = fine
            b.save()

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
    updateFine()
    stud = Student.objects.get(user = User.objects.get(id = request.user.id))
    book_count = Book.objects.count
    borrow_count = Borrow.objects.count
    pending_returns = 0
    borrows = list(Borrow.objects.filter(borrower = stud))
    # Total fine calculation
    borrow_fine = list(Borrow.objects.filter(borrower = stud).values_list('fine_amount', flat=True))
    total_fine = sum(borrow_fine)

    #Finding the pending returns
    for s in borrow_fine:
        if s > 0:
            pending_returns += 1
    qSort(borrows, 'fine_amount')
    borrows = borrows[-5:]

    #Books in demand
    demand_books = list(Borrow.objects.filter(borrower = stud).values_list('book', flat=True))
    data = {'book_count': book_count, 'borrow_count': borrow_count, 'total_fine': total_fine, 'pending_returns':pending_returns, 'fullname':stud.fullname}
    if pending_returns != 0:
        data['borrows'] = borrows
    if len(demand_books) != 0:
        data['demand_books'] = demand_books
    data['fullname'] = stud.fullname
    return render(request, 'panel/index.html', data)

#Books listing
@login_required(login_url='login')
def books(request):
    stud = Student.objects.get(user = User.objects.get(id = request.user.id))
    books = list(Book.objects.all())
    if request.method == 'POST':
        key = request.POST.get('sort_by')
        qSort(books, key.lower())
    return render(request, 'panel/books.html', {'books': books, 'fullname': stud.fullname})

#Students listing
@login_required(login_url='login')
def students(request):
    updateFine()
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
        students_db['id'] = s.id
        stud_db.append(students_db)
    if request.method == 'POST':
        key = request.POST.get('sort_by')
        qSort(students, key.lower())
    return render(request, 'panel/students.html', {'students': stud_db})

#Borrow listing
@login_required(login_url='login')
def bookings(request):
    updateFine()
    stud = Student.objects.get(user = User.objects.get(id = request.user.id))
    borrows = list(Borrow.objects.filter(borrower = stud))
    if request.method ==  'POST':
        key = request.POST.get('sort_by')
        qSort(borrows, key.lower())
    return render(request, 'panel/bookings.html', {'borrows': borrows, 'fullname': stud.fullname})

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
def add_booking(request, book_id):
    stud = Student.objects.get(user = User.objects.get(id = request.user.id))
    students = Student.objects.all()
    book = Book.objects.get(id = book_id)
    data = {'students': students, 'book': book, 'fullname': stud.fullname}
    if request.method == 'POST':
        borrower = request.POST.get('borrower')
        due_date = request.POST.get('due_date')
        # Check book availability
        bk = list(Borrow.objects.filter(book=book).values_list('book', flat=True))
        if len(bk) < book.copies:
            borrow = Borrow(
                borrower=Student.objects.get(fullname=borrower),
                due_date=due_date,
                book=Book.objects.get(title=book)
            )
            borrow.save()
            return redirect('bookings')
        else:
            data['error'] = 'The requested book is not in stock'
    return render(request, 'panel/add-booking.html', data )

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
        return redirect('bookings')
    return render(request, 'panel/return-book.html', {'borrow': brw, 'color': color})

@login_required(login_url='login')
def student_profile(request):
    stud = Student.objects.get(user = User.objects.get(id = request.user.id))
    data = {}
    data['fullname'] = stud.fullname
    data['email'] = stud.email
    data['roll_number'] = stud.roll_number
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        rollnumber = request.POST.get('roll_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        conf_pass = request.POST.get('password_cnfrm')
        if fullname != '':
            stud.fullname = fullname
        else:
            data['error'] = 'Empty field (fullname) not permitted'
        if rollnumber != '':
            stud.roll_number = rollnumber
        else:
            data['error'] = 'Empty field (roll number) not permitted'
        if email != '':
            stud.email = email
        else:
            data['error'] = 'Empty field (email) not permitted'
        if 'error' in  data.keys():
            return render(request, 'panel/student-profile.html', data)
        stud.save()
        # Change password
        if password != '' and conf_pass != '' and password == conf_pass:
            try:
                val = validate_password(password)
                if val == None:
                    user = User.objects.get(id = request.user.id)
                    user.set_password(password)
                    user.save()
                    return redirect('home')
            except ValidationError as v:
                data['error'] = '\n'.join(v)
                return render(request, 'panel/student-profile.html', data)

    return render(request, 'panel/student-profile.html', data)

@unAuthenticated_user
def register_student(request):
    data = {}
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        rollnumber = request.POST.get('roll_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        conf_pass = request.POST.get('password_cnfrm')
        if fullname == '':
            data['error'] = 'Empty field (fullname) not permitted'
        if rollnumber == '':
            data['error'] = 'Empty field (roll number) not permitted'
        if email == '':
            data['error'] = 'Empty field (email) not permitted'
        if 'error' in  data.keys():
            return render(request, 'panel/student-profile.html', data)
        # Set password
        if password != '' and conf_pass != '' and password == conf_pass:
            try:
                val = validate_password(password)
                if val == None:
                    fullnamearr = fullname.split(' ')
                    firstname, lastname = fullnamearr[0], ''.join(fullnamearr[1:])
                    user = User.objects.create_user(firstname[:10].lower(), email, password)
                    user.first_name = firstname
                    user.last_name = lastname
                    user.save()
                    st = Student.objects.create(
                        fullname = fullname,
                        roll_number = rollnumber,
                        email = email,
                        user = user
                    )
                    st.save()
                    return redirect('home')
            except ValidationError as v:
                data['error'] = '\n'.join(v)
                return render(request, 'panel/register-student.html', data)

    return render(request, 'panel/register-student.html', data)

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