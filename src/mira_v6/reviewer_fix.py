"""Generic correction for the reviewer's choice of missing tests (candidate; NOT part of the frozen v5 or v6 condition).

Why: in the case-001 comparison the first review of Qwen4 Max sometimes wrote a syndrome as the diagnosis (pericarditis with tamponade), spent three of the four test slots on the same specimen and on tests already returned
as "not on record", and never asked for the test that examines an implanted device or prior intervention. Opus 5.5 given the same stored input named the structural source and asked for the vascular study first (3 of 3 replays).
The text below is case-agnostic: it names no diagnosis, test result or case; it only changes how the four slots are chosen. Install it only in a new, named arm; changing it after a run makes a new condition.
"""
TEXT=("Choosing the investigations (apply before you write missing_tests): "
      "(1) A syndrome such as an effusion, shock or tamponade is not a cause. Name the two or three most plausible CAUSES of the syndrome and choose investigations that discriminate between them; "
      "do not let the first diagnosis you wrote decide which tests you ask for. "
      "(2) Treat every implanted device or prosthetic material, every prior intervention and every recently placed line, stent or graft as a possible source of the complication, "
      "and include the investigation that would examine that structure when the history supports it. "
      "(3) Use at most one of the four slots to confirm the syndrome or to sample one specimen (a stain and a culture of the same fluid count as one). "
      "(4) A test that already came back as not on record is closed: do not ask for it again under another wording, a combined name or a different tool; choose a different modality or site instead. "
      "(5) Prefer one investigation for each mechanism you are trying to separate.")

def install():
    """Append TEXT to the first-review system prompt of the v4 fast cascade (runtime override; the module file stays untouched)."""
    from mira_runner import fast_v4
    if TEXT not in fast_v4.SOL_SYSTEM:fast_v4.SOL_SYSTEM=fast_v4.SOL_SYSTEM+' '+TEXT
    return TEXT
