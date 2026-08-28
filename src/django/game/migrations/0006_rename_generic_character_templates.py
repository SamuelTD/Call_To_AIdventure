from django.db import migrations

SYSTEM_TEMPLATE_USER_ID = -1

RENAMES = [
    ("Dwarf Fighter", "Borin Stoneguard"),
    ("Human Rogue", "Mira Quickstep"),
    ("Elf Wizard", "Elara Moonveil"),
]


def rename_generic_templates(apps, schema_editor):
    CharacterTemplate = apps.get_model("game", "CharacterTemplate")

    for old_name, new_name in RENAMES:
        CharacterTemplate.objects.filter(
            user_id=SYSTEM_TEMPLATE_USER_ID,
            name=old_name,
        ).update(name=new_name)


def restore_generic_template_names(apps, schema_editor):
    CharacterTemplate = apps.get_model("game", "CharacterTemplate")

    for old_name, new_name in RENAMES:
        CharacterTemplate.objects.filter(
            user_id=SYSTEM_TEMPLATE_USER_ID,
            name=new_name,
        ).update(name=old_name)


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0005_seed_generic_character_templates"),
    ]

    operations = [
        migrations.RunPython(rename_generic_templates, restore_generic_template_names),
    ]
