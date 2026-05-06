from django.db import models
from django.contrib.auth.models import User

class SaveGame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    adventure_id = models.CharField(max_length=100)
    adventure_name = models.CharField(max_length=200)
    state = models.JSONField(default=dict)  # serialized GameState
    is_finished = models.BooleanField(default=False, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.adventure_name}"
