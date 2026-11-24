"""Generic reviewer prompt correction v2 (NEW condition "v6.3"; v5, v6, v6.1 and v6.2 files untouched).

Why: in the closed-case 011 comparison the Opus 5.5 first read (two samples) turned a reported food trigger into a general property of the meal (a biliary reading), built all four first-follow-up tests and the patient questions on one family of causes,
received "not on record" for almost all of them and never left that family; the Sol 6.2 / Astra 6.2 readers kept the trigger in its specific form, named a second cause of a different nature and asked what separated the two.
The text names no case, diagnosis, food or result; it only changes how the first read states the history, how many mechanism classes it keeps open and what the three patient questions must contain.
Install it only in a new, named arm; changing it after a run makes a new condition.
"""
TEXT=("Method for this review (apply before you write the questions and tests): "
      "(1) Keep every reported trigger, timing and exposure in its specific form (the particular food, drug, product, activity, bite or contact named) and do not replace it by a general property of it unless the history says so. "
      "(2) Name at least two candidate causes from different mechanism classes (for example infectious or parasitic, immune or allergic, drug or toxin, metabolic or endocrine, structural or vascular, neoplastic) and say in the reasoning what would separate them; "
      "do not build all of your tests and questions on one class. "
      "(3) Among your patient questions, include one open question that does not presuppose your leading diagnosis, asking what exactly preceded and followed the episodes (foods, drugs, products, activities, exposures, bites) and how long afterwards, "
      "and one about exposures or past events that the transcript has not covered. "
      "(4) A test that came back as not on record is closed: do not ask for it again under another name, and when most of your tests come back this way, change the mechanism class you are testing instead of testing the same class with other studies.")

def install():
    """Append TEXT to the first-review system prompt of the fast cascade (runtime override; the second review is built from the same constant, the final review prompt is unchanged)."""
    from mira_runner import fast_v4
    if TEXT not in fast_v4.SOL_SYSTEM:fast_v4.SOL_SYSTEM=fast_v4.SOL_SYSTEM+' '+TEXT
    return TEXT
