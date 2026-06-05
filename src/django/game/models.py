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

class CharacterTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="character_templates")
    name = models.CharField(max_length=60)
    race = models.CharField(max_length=40)
    character_class = models.CharField(max_length=40)
    gender = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_character_template_name_per_user",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.user.username} - {self.name}"
