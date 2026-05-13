# PII — Future Needs & Considerations

This file captures planning discussions, architectural ideas, and longer-term considerations
that are not yet ready for implementation. Each entry records the date, the context that
prompted it, and enough detail to reconstruct the reasoning in a future session.

---

## User Memory & Informed Co-Orientation
**Date:** 2026-05-12
**Prompted by:** Observation that the PII's co-orientation is "blind" — it derives user
intent from the current thread only, with no knowledge of the user's role, ongoing projects,
or prior sessions. A topic-pivot mid-thread (e.g., asking about AACSB accreditation after
a focused exchange about an HRM-805 assignment) forces the user to re-establish context
they already carry in their head.

### The Core Problem
Co-orientation works from scratch each session. The system cannot distinguish between:
- A pivot that is genuinely unrelated to the current thread
- A pivot that connects to a larger project the user has been working on across multiple sessions

A user who has been building an AACSB assurance-of-learning portfolio for three sessions
should not have to re-explain that context every time they enter a new thread.

### Proposed Architecture

**Memory is just another retrieval source.** The PII already injects context from SQLite
(PLOs, CLOs, competency catalogs). User memory is the same mechanism applied to a different
table: instead of retrieving what the program contains, retrieve what you know about this user.

**Three memory layers:**

1. **Fixed profile** (set once by the user or admin)
   - Role: Program Director / Dean / Instructional Designer / Assessment Director
   - Programs in scope: which program(s) they own or advise
   - Current institutional priorities (e.g., "AACSB review preparation", "SHRM competency mapping")

2. **Episodic session memory** (derived automatically after each session)
   - Topics covered, apparent goals, open threads
   - Example: *"2026-05-10: Explored SHRM competency alignment for HRM-805 and HRM-810.
     Appears to be building an assurance-of-learning portfolio. AACSB mentioned in passing."*

3. **Preference signals** (accumulated over time)
   - Preferred response format, detail level, frameworks most engaged with

**What changes about co-orientation:**
Without memory, the pivot question is open: "Help me capture the connection between X and Y."
With memory, the system can surface a working hypothesis: "Given the AACSB documentation
work you've been doing — are you looking at this HRM-805 assignment as assurance-of-learning
evidence?" That is a materially better question.

### Implementation Path

1. **User identity** — Simple "Who are you?" selector at startup (dropdown, not full auth).
   Small known user base (~10–20 institutional staff) makes this practical.

2. **New tables in program.db:**
   - `users` — user_id, name, role, primary_programs, current_priorities
   - `user_memory` — user_id, session_date, summary_text, topics_json, programs_in_scope, open_threads

3. **Memory injection at Tier 1** — "User Context" block in the system prompt alongside
   PLOs and CLOs. Always-on, lightweight. Shapes co-orientation decisions automatically.

4. **Memory writing** — Tie to the email-session button (user is already signaling "I'm done").
   A lightweight Haiku call synthesizes the session into 3–5 structured observations and
   appends them to `user_memory`. No added user effort.

5. **Memory-aware co-orientation** — Update pivot detection to check user memory before
   asking a clarifying question. If recent memory contains a plausible connection to the
   pivot topic, surface it as a hypothesis rather than asking open-endedly.

### Constraints / Non-Issues
- RAG architecture unchanged — memory is additive, not a replacement
- No vector database required at this scale
- Everything stays local (SQLite) — FERPA compliance preserved
- User base is small enough that basic profiles deliver value on day one

### When to Implement
After SHRM item links and ITM competency framework decisions are resolved. Memory is a
quality-of-service improvement; the competency gaps are functional gaps. Prioritize
functional completeness first.

---

---

## Evidence Basis / Attribution Pattern (Gap #3 — Next Session)
**Date logged:** 2026-05-12
**Status:** Ready to implement — queued for next session
**Prompted by:** Co-orientation research review identifying a gap between the PII's definitive-answer rule and transparent evidence grounding.

### The Problem
The PII's anti-hedging rules correctly suppress uncertainty language ("this may be true," "it appears that"). But they also suppress attribution ("this is based on X"), which is a different thing. A definitive answer and a transparent evidence basis are not in conflict — one describes confidence level, the other describes scope.

Currently, a coverage or alignment response gives no signal about what the answer rests on: how many assignments were in scope, whether formal links or semantic matching was used, which framework was applied, or how many courses contributed. If the scope was wrong, the user has no foothold for correction without re-asking.

### The Proposed Pattern
Add a non-hedging attribution rule for coverage and alignment responses. The attribution is a scope declaration, not a confidence qualifier:

- Correct: "Based on the four assignments in LD-820 and LD-823 with formal LD competency links..."
- Correct: "Across the nine required courses in the Project Management program..."
- Incorrect: "This may be based on..." / "It appears that the following assignments..."

The rule should fire for: competency alignment responses, PLO/CLO coverage analyses, cross-program comparisons, any response where the answer depends meaningfully on which items were in scope.

It should NOT fire for: simple direct lookups, responses where scope was explicit in the query.

### User Model Note
PII users are domain experts — they know what their programs contain. They don't need retrieval mechanics explained. The attribution pattern is useful not for transparency about how the system works, but because it gives the expert user enough scope information to immediately recognize if the answer was based on a different slice of the curriculum than they had in mind.

<!-- Add new entries above this line, most recent first -->
