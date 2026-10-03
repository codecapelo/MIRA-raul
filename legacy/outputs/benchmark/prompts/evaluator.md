# Evaluator aid — draft, not safety authority

The automatic evaluator may check schema validity, event counts, timing, pre-approved diagnostic equivalences, and explicit rubric rule matches. For ambiguous clinical decisions, it must emit `requires_physician_review` and cite relevant trace event IDs and rubric item IDs. It must not label a clinical trajectory safe solely from a language model judgment. Physician adjudication is authoritative and stored separately from model outputs.
