# Block 3 product quality audit

## Scope

This audit covers the active Django browser pages:

- landing;
- character creation;
- story play;
- combat;
- login/signup through existing Django forms.

Legacy Gradio screens and local debug utilities are not part of the target
production user interface.

## Automated checks added

| Check | Evidence |
|---|---|
| Dynamic pages expose live status regions | `ProductQualityTemplateTests.test_dynamic_pages_expose_live_status_regions` |
| Custom tabs expose ARIA tab semantics and keyboard handlers | `ProductQualityTemplateTests.test_custom_tabs_have_required_aria_and_keyboard_handlers` |
| Story/combat dynamic updates are focusable and announced | `ProductQualityTemplateTests.test_story_and_combat_updates_are_focusable_and_announced` |
| Main pages render accessibility landmarks | `ProductQualityTemplateTests.test_main_pages_render_accessibility_landmarks` |
| Guest browser journey works with fake AI | `BrowserSmokeJourneyTests.test_guest_can_start_play_enter_combat_and_resolve_action_with_fake_ai` |

## Accessibility corrections applied

| Area | Correction |
|---|---|
| Status messages | Added `role="status"`, `aria-live="polite"` and `aria-atomic="true"` to active dynamic pages |
| Story updates | Made story text focusable and announced after load, story turn and current-room refresh |
| Combat updates | Made combat log focusable and announced after combat start/action |
| HP bars | Exposed player/enemy HP bars as ARIA progress bars with current and max values |
| Custom tabs | Added `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"` and keyboard navigation |
| Empty dynamic lists | Added polite live announcements to empty save/template states |

## Security-oriented quality checks already covered

| Check | Evidence |
|---|---|
| Browser JSON POSTs require CSRF when enforced | `SecurityBoundaryTests` |
| Oversized JSON bodies are rejected | `SecurityBoundaryTests` |
| AI-triggering endpoints are rate-limited | `SecurityBoundaryTests` |
| Combat state is isolated per session state | `CombatEngineTests` |

## Eco-design baseline

| Measure | Current state | Next action |
|---|---|---|
| No separate frontend build | Server-rendered templates with small inline scripts | Keep unless UI complexity grows |
| Avoid uncontrolled AI polling | Story/combat calls are user-triggered; only one keepalive metric call per ready turn | Keep token/call counters in monitoring |
| RAG reuse | Retrieval service has cache-oriented tests | Recheck cache hit behavior under Priority 5 metrics |
| Static assets | Monster images are local static files | Add compression/static collection evidence in CI/CD |
| Template duplication | CSS/JS are duplicated across templates | Extract shared assets when Priority 4 introduces artifact build |

## Manual owner/evaluator checks still required

- Run a keyboard-only walkthrough on landing, character creation, play and
  combat pages.
- Check color contrast with a WCAG/RGAA tool.
- Test browser zoom/reflow at 200%.
- Run a screen-reader smoke pass, at least NVDA or VoiceOver.
- Confirm French and English visible text quality.
- Run a dependency/static security scanner once CI tooling is selected.
- Capture before/after screenshots for the final report if required.
