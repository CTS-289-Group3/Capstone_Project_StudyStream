from django.db import models


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    class_name = models.CharField(max_length=100)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title