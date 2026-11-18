"""Generic reviewer prompt correction v3 (condition "v6.3"; v5, v6, v6.1, v6.2 and reviewer_fix2 untouched): v2 merged with what Opus 5.5 itself proposed when asked, without being told the answer, to reflect on its own first read
(scripts/diag_opus_interview.py, 4 interviews, 2 stored inputs of the closed case it got wrong). The themes that repeated in all or most interviews are the ones kept: at least several cause families with one supporting finding each,
two readings of every key history item (one not infectious and not exposure-related), "name what a trigger contains and ask which other items with the same component do or do not provoke it and how long after", non-infectious causes for every abnormal value,
and "switch family after two empty test results in a row". The text names no case, disease, food or result. Install it only in a new, named arm; changing it after a run makes a new condition.
"""
TEXT=("Method for this review (apply before you write the questions and tests): "
      "(1) Describe the episodes on their own terms (timing, trigger, duration, what relieves them) and list the cause families that pattern fits, at least four and including non-infectious ones "
      "(for example infectious or parasitic, immune or allergic, drug or toxin, functional or motility, structural or vascular, metabolic or endocrine, neoplastic), with one finding that would support each; "
      "do not build all of your tests and questions on one family. "
      "(2) For each key history item (every trigger, exposure, medication, food, activity, trip) give at least two readings, one of them not infectious and not related to travel or exposure. "
      "Keep each reported trigger in its specific form and do not replace it by a general property. For a reported trigger, name everything it contains, and ask which other items with the same component do or do not provoke symptoms and how long after exposure. "
      "Treat a patient's general statement about habits as unverified and ask about the specific items. "
      "(3) For every abnormal laboratory value list non-infectious as well as infectious causes. "
      "(4) Your patient questions must include one open question that does not presuppose your leading diagnosis (what exactly preceded and followed the episodes, and how long afterwards) and one about exposures or past events the transcript has not covered. "
      "(5) A test that came back as not on record is closed: do not ask for it again under another name. If two requests in a row come back empty, change the cause family you are testing instead of ordering more tests of the same family, and question your frame before settling on a cause.")

def install():
    """Append TEXT to the first-review system prompt of the fast cascade (runtime override; the second review is built from the same constant, the final review prompt is unchanged)."""
    from mira_runner import fast_v4
    if TEXT not in fast_v4.SOL_SYSTEM:fast_v4.SOL_SYSTEM=fast_v4.SOL_SYSTEM+' '+TEXT
    return TEXT
