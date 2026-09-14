"""Reconstruct a deterministic interleaving on historical and current combat code.

Read-only Git access; no checkout, provider request or application DB mutation.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from combat.core import restore_combat_session, resolve_player_action
from utils.enums import PlayerAction

FIX = '8a3cf39702a0920582862904c28ce65f74a545cf'
historical_source = subprocess.check_output(
    ['git', 'show', f'{FIX}^:src/combat/core.py'], cwd=ROOT, text=True, encoding='utf-8'
)
old = ModuleType('historical_combat_e5')
exec(compile(historical_source, 'historical_combat_e5', 'exec'), old.__dict__)

def fixtures():
    def player():
        return SimpleNamespace(hp=20, strength=0, weapon=SimpleNamespace(min_dmg=3, max_dmg=3, name='test sword'))
    return player(), SimpleNamespace(HP=8, name='Monster A'), player(), SimpleNamespace(HP=8, name='Monster B')

pa, ma, pb, mb = fixtures()
# Deterministically simulate A restoring its state, then B interrupting before A attacks.
old.restore_combat(pa, ma)
old.restore_combat(pb, mb)
with patch.object(old.r, 'randint', return_value=3):
    old.player_action(PlayerAction.ATTACK)
before = {'monster_A_hp': ma.HP, 'monster_B_hp': mb.HP}
assert before == {'monster_A_hp': 8, 'monster_B_hp': 5}

pa, ma, pb, mb = fixtures()
session_a = restore_combat_session(pa, ma)
session_b = restore_combat_session(pb, mb)
with patch('combat.core.r.randint', return_value=3):
    resolve_player_action(session_a, PlayerAction.ATTACK)
after = {'monster_A_hp': ma.HP, 'monster_B_hp': mb.HP}
assert after == {'monster_A_hp': 5, 'monster_B_hp': 8}

report = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'historical_fix_commit': FIX,
    'current_revision': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'scenario': 'Restore A; restore B; resume the attack initiated for A with fixed damage 3.',
    'initial_hp': {'monster_A_hp':8,'monster_B_hp':8},
    'historical_result': before,
    'current_result': after,
    'historical_bug_reproduced': True,
    'current_isolation_verified': True,
    'limits': 'Deterministic interleaving of core functions, not a threaded HTTP load test or evidence of a production incident.'
}
output=Path(__file__).resolve().parent/'preuves'/'incident-combat.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(report,indent=2,ensure_ascii=False))
