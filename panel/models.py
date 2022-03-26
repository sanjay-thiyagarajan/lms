from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Student(models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE, null=True)
    fullname = models.CharField(max_length=200, null=True)
    roll_number = models.CharField(max_length=20, null=True)
    email = models.EmailField(null=True)
    academic_year = models.CharField(max_length=200,
        choices= (
            ('I year', 'I year'),
            ('II year', 'II year'),
            ('III year', 'III year'),
            ('IV year', 'IV year')
        )
    )

    def __str__(self):
        return self.fullname

class Book(models.Model):
    isbn_number = models.CharField(max_length=20, null=True)
    title = models.CharField(max_length=200, null=True)
    author = models.CharField(max_length=200, null=True)
    copies = models.IntegerField(null=True)

    def __str__(self):
        return self.title

class Borrow(models.Model):
    borrower = models.ForeignKey(Student, on_delete=models.CASCADE)
    borrowed_on = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True)
    fine_amount = models.FloatField(null=True, default=0.0)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return str(self.borrower)+"-"+str(self.book)

@receiver(post_save, sender=Student)
def createUser(sender, instance, **kwargs):
    if instance.user == None:
        fullname = instance.fullname.split(' ')
        firstname, lastname = fullname[0], ''.join(fullname[1:])
        user = User.objects.create_user(''.join(fullname[:10]).lower(), instance.email, 'Pass@2019')
        user.first_name = firstname
        user.last_name = lastname
        user.save()
        stud = Student.objects.get(id = instance.id)
        stud.user = user
        stud.save()
