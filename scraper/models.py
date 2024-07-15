from django.db import models

class Hackathon(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    website = models.URLField()

    def __str__(self):
        return self.title

