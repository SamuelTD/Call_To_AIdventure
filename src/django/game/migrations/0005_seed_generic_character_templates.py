from django.conf import settings
from django.db import migrations

SYSTEM_TEMPLATE_USER_ID = -1

GENERIC_TEMPLATES = [
    {
        "name": "Borin Stoneguard",
        "race": "Dwarf",
        "character_class": "fighter",
        "gender": "Male",
    },
    {
        "name": "Mira Quickstep",
        "race": "Human",
        "character_class": "rogue",
        "gender": "Female",
    },
    {
        "name": "Elara Moonveil",
        "race": "Elf",
        "character_class": "wizard",
        "gender": "Female",
    },
]


def seed_generic_templates(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    CharacterTemplate = apps.get_model("game", "CharacterTemplate")

    User.objects.update_or_create(
        id=SYSTEM_TEMPLATE_USER_ID,
        defaults={
            "username": "generic_character_templates",
            "password": "",
            "is_active": False,
            "is_staff": False,
            "is_superuser": False,
        },
    )

    for template in GENERIC_TEMPLATES:
        CharacterTemplate.objects.update_or_create(
            user_id=SYSTEM_TEMPLATE_USER_ID,
            name=template["name"],
            defaults={
                "race": template["race"],
                "character_class": template["character_class"],
                "gender": template["gender"],
            },
        )


def remove_generic_templates(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    CharacterTemplate = apps.get_model("game", "CharacterTemplate")

    CharacterTemplate.objects.filter(user_id=SYSTEM_TEMPLATE_USER_ID).delete()
    User.objects.filter(id=SYSTEM_TEMPLATE_USER_ID).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0004_charactertemplate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(seed_generic_templates, remove_generic_templates),
    ]
