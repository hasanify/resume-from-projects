# Writing rules for resume text

Apply every rule in this file to all resume text: summary, project descriptions, bullets, skills line, experience bullets. This file is self-contained so the skill works offline and on any agent. It combines three sources:

1. The `write-like-a-human` skill (all rules, Part B).
2. The `anti-slop` project by Miqdad Badjuber, MIT licensed, https://github.com/miqdadbadjuber/anti-slop (copywriting skill in Part C, core rules in Part D). Rules marked R-xx or C-5 keep the numbering used in that project.
3. Resume-specific rules for this skill (Part A and Part E).

Where sources conflict, the stricter rule wins, with the exceptions listed in Part F.

---

## Part A. Truthfulness (hard gate, no exceptions)

- Never invent facts: no employers, titles, degrees, dates, contact details, users, revenue, uptime, speedups, test counts, or team sizes.
- A number goes on the resume only if it comes from the project's code, README, config, tests or git history, or from the user. Counting things in the repo (tests, endpoints, commits, files, supported providers) is allowed. Record where each number came from in the `evidence` field of `resume.json`.
- Describe only what the user did. If git history shows the user wrote 40% of the commits, do not write "built" for the whole system. Use the verb and scope that the evidence supports.
- No number available: describe the concrete result instead (what it does, what it connects to, what it replaced).
- If a sentence needs a detail you do not have, write the plain version without it, or ask the user.

## Part B. write-like-a-human (all rules)

You are writing for a human reader. Every rule below is a standing instruction.

### Banned words and phrases

Never use these. Cut them or rephrase.

**AI filler and buzzwords:** delve into, underscore, pivotal, realm, harness, illuminate, shed light on, bolster, streamline, facilitate, foster, leverage, cutting-edge, state-of-the-art, innovative, revolutionary, game-changing, transformative, groundbreaking, seamless, robust, scalable, holistic, synergy, paradigm shift, nuanced, comprehensive, best practices.

**Hollow openers and affirmations:** Certainly, Absolutely, Of course, Great question, I'd be happy to, Sure, Feel free to ask, Don't hesitate to reach out.

**Transition padding:** That being said, At its core, To put it simply, From a broader perspective, A key takeaway is, It's worth noting, It's important to note, As we navigate, In today's world, In the realm of, When it comes to, It goes without saying, At the end of the day.

**Vague qualifiers:** generally speaking, broadly speaking, to some extent, arguably, tends to, typically (when used to avoid commitment), various, a number of, a wide range of, many people, some experts, in some cases.

**Performance words:** truly, literally, essentially, ultimately, clearly, obviously, undoubtedly, undeniably, fascinating, incredible, wonderful, amazing.

**Formal words with plain alternatives:** utilize (use "use"), commence (use "start"), endeavor (use "try"), ascertain (use "find out"), elucidate (use "explain"), aforementioned (cut it), herein (cut it).

### Structural rules

Write in paragraphs. Use bullet points only for genuinely parallel, discrete items like steps or lists of items. Never use bullet points to break up ideas that belong in prose. (Resume exception: see Part F. Resume bullets are discrete achievements, which is the intended use.)

Skip headers in short and medium-length pieces. Headers belong in documents people navigate. (Resume exception: section headings are required by the layout spec.)

Do not bold random phrases mid-paragraph for emphasis. Emphasis comes from word choice and sentence position.

Never tell the reader what you are about to do. Just do it. Cut sentences like "In this section, we will explore..." and begin.

### Tone and openings

Start answering immediately. Do not open with agreement, affirmation, or a restatement of the question.

End when the answer is done. Do not close with "I hope this helps," "Let me know if you have questions," or any variation.

Match the register of the request. Do not dress up simple things in formal language.

### Sentence rhythm

Vary sentence length. Mix short sentences with longer ones. Never string three sentences of the same structure together. If the prose sounds metronomic when read aloud, rewrite it.

Start sentences with different words. Three consecutive sentences beginning with "This" or "It" signals a rewrite.

### Specificity

Name the thing. Replace "many people believe" with who believes it. Replace "various studies suggest" with which studies. Replace "in some cases" with the actual case. If you cannot be specific, cut the claim.

Take a position. Hedge once if genuinely uncertain, then commit. Do not wrap every sentence in "potentially," "could," "might," or "it is possible that."

### Punctuation

Never use the em-dash as a connective shortcut. Restructure the sentence instead. A comma, a period, or a new sentence handles almost everything an em-dash is used for in AI writing.

No exclamation marks in analytical or professional writing.

### Common AI sentence patterns to avoid

- "Not [X], but [Y]" used as a reframe (e.g. "Not a limitation, but an opportunity")
- "X is not just [A], it's [B]" (e.g. "This is not just a tool, it's a movement")
- "[X] allows us to [vague benefit]" (e.g. "This approach allows us to unlock potential")
- "By [doing X], we can [achieve Y]" as a generic closing statement
- "Whether you are [A] or [B], [generic claim]"
- "[X] is at the heart of [Y]"
- "In an era where [broad claim]..."
- "As [field] continues to evolve..."
- Repeating the question back before answering it

### The test

Before finalizing any output, ask: could this sentence appear in a template? If yes, rewrite it. If a phrase could be dropped into any piece on any topic without changing, it adds nothing. Cut it or replace it with something specific to this piece.

## Part C. anti-slop copywriting skill (all patterns)

Two rules govern everything below. First, never invent facts (R-17, R-36, R-38): a rewrite adds no fact, name, number, date, quote or citation that is not in the source or supplied by the user. Second, do not over-sterilize: copy with no voice is as obviously machine-made as copy full of AI tells. Each pattern lists the tell, why it reads as AI, and the fix.

### Tone and voice

**Empty AI vocabulary.** Verbs and abstract nouns stacked to sound impressive: unlock, elevate, empower, delve, showcase, testament, landscape (abstract), journey, robust, game-changer, next-level, seamless, cutting-edge, revolutionary. They appear far more often in machine text and signal intent to impress, not inform. Before: "Unlock the power of seamless collaboration to elevate your team's journey." After: "Work with your team in one shared space." (R-16, R-36)

**Significance inflation.** "The future of X", "marking a pivotal moment", "a testament to", "revolutionizing", "a new era of". No evidence behind it. Replace with what the thing does. (R-36, C-5)

**Empty claims and social proof with no evidence.** "Trusted by thousands", "industry-leading", "world-class", "loved by customers everywhere". Name a real customer or number, or cut the claim. (R-17, R-18, R-36, C-5)

**Weasel attributions.** "Experts say", "industry observers", "people report". Name the source or cut the sentence. (R-36, C-5)

**Persuasive authority tropes.** "At its core", "the real question is", "what really matters", "fundamentally", "the deeper issue", "the heart of the matter". They restate an ordinary point with ceremony. State the point. (R-36)

**Chatbot closers.** "I hope this helps!", "Let me know if you have any questions", "Would you like me to expand on this?". Conversation artifacts, not copy. (R-36)

**Fake-candid openers.** "Honestly?", "Let's be honest", "Here's the thing", "Real talk". Just say the thing. (R-36)

**Signposting announcements.** "Let's dive in", "Here's what you need to know", "In this article we'll explore", "Without further ado". Do the thing instead of announcing it. (R-36)

**Temporal runway clichés.** "In today's fast-paced world", "In an era of rapid technological disruption", "In today's ever-evolving digital landscape". Start with the subject. (R-16, R-36)

**All-caps emphasis.** Whole clauses in capitals to shout. Write the emphasis into the sentence. A single accent word or a real headline may keep its caps. (R-36)

**Actorless passive.** "The decision was made to...", "the page has been updated". Name the actor. For a resume the actor is the user, written as an implied "I": "Rewrote the pricing page" not "Pricing page was rewritten." Passive stays fine when the actor is unknown or irrelevant ("the server was restarted at 03:00"). (R-02)

**Inanimate subject, human verb.** "The dashboard understands what your team needs", "the data tells us", "the roadmap wants to focus on". Verbs that need a mind (understands, knows, decides, wants, believes, cares) do not belong to software. Ordinary verbs are fine: "the report shows", "the form submits", "the filter narrows the list". (R-02, R-16)

### Rhythm and structure

**Rule of three overuse.** Every idea forced into a trio ("innovation, inspiration, and insights"). Use the number of items the content requires. (R-05, R-36)

**Negative parallelism and tailing negations.** "It's not just X, it's Y", "Not only X, but also Y", clipped tails like "no guessing", "no wasted motion". (R-36)

**Aphorism formulas.** "X is the language of Y", "X is the currency of Z", "Efficiency becomes a trap when". State the point with precision. (R-36)

**Staccato drama.** A run of short fragments to manufacture a punchline ("No templates. No defaults. No safety."). One short sentence for emphasis is fine, a run is not. (R-36)

**Theatrical takeaways.** "Read that again.", "Let that sink in.", "The message is clear:", "That distinction matters.", "The takeaway is simple:", "Here is the bottom line:". Let the claim stand on its evidence. (R-36)

**Synonym cycling.** Swapping synonyms to dodge repetition ("the checkout is fast, the process is quick, the flow is speedy"). Repeat the clearest word when it is clearest. (R-36)

**False ranges.** "From X to Y" where X and Y are not on a real scale ("from onboarding to scale", "from first click to final invoice, and everything in between"). List the specific things instead. (R-36)

### Honesty and evidence

**Fabricated specifics.** Invented numbers, testimonials, names, dates or features that look realistic. This is a defect even when it sounds more human than the vague original. If there is no real figure, write no figure. Any real statistic needs a real source. (R-17, R-18, R-36, R-38, C-5)

**Speculative gap-filling.** When a fact is unknown, writing a sentence about not knowing it and then inventing plausible filler ("the company was likely founded in the 1990s"). Omit the sentence. State a date only if a source provides one. (R-17, R-36)

**Generic positive conclusion.** "The future looks bright", "Exciting times lie ahead", "a major step in the right direction". Cut it. End on the last concrete fact. (R-36)

### Hygiene and markdown

**Em dashes.** The em dash character is banned in output (R-02). Replace each one, in rough order of preference: a period (new sentence), a comma (tight aside), a colon (introduce an explanation), parentheses (true aside), or restructure. Also catch spaced em dashes and double hyphens used the same way. En dashes used as a connective are treated the same way. An en dash is allowed only inside numeric or date ranges such as 2023-2025, and a plain hyphen is fine there too. If the user's own writing sample uses em dashes, name the character, name the rule, and ask whether to keep them. Never keep or cut them silently.

**Boldface overuse.** Bolding every key term. Emphasis everywhere is emphasis nowhere. (Resume exception: the layout spec bolds project names, job titles and the name.)

**Excessive quotation marks.** Scare quotes and quotes as default emphasis. Quotes stay for real quotations and titles. (R-36)

**Inline-header lists.** Bullets that start with a bold header and a colon ("**Performance:** load times are faster"). The header restates the item. Do not use this pattern in resume bullets. (R-36)

**Title Case in list elements.** Capitalizing every word in bullets. Use sentence case. Proper nouns, acronyms and product names keep their capitalization. (R-36)

**Emojis in headings or bullets.** Never on a resume. (R-36)

**Filler phrases.** "In order to" for "to", "due to the fact that" for "because", "at this point in time" for "now", "it is important to note that" for nothing. (R-36)

**Excessive hedging.** "Could potentially possibly", "may perhaps". One qualifier does the work. (R-36)

### What not to flag, and what to preserve

Clean human writers can hit several patterns without any AI involvement. These alone are not tells: perfect grammar, mixed registers, plain dry prose, formal vocabulary that is precise, one "however" or "additionally", curly quotes, one short emphatic sentence, unsourced claims, and text inside quotations, titles, proper names or examples. Look for clusters, not isolated tells. Do not flatten a precise technical term because it sounds formal.

Keep signs of human writing: specific, unusual, hard-to-fabricate detail; variety in sentence length; real asides. On a resume that means the concrete detail (the actual library, the actual provider, the actual constraint) is what to preserve.

### Voice calibration (optional)

If the user supplies a writing sample, read it first and match its sentence lengths, vocabulary and habits instead of only deleting AI patterns. The sample outranks the style rules here except R-02 (em dashes), which goes through the ask-the-owner step above.

## Part D. anti-slop core rules that apply to text

- **R-02 Copywriting.** Forbidden: the em dash character in any text. Use a comma, period, colon or parentheses. Text must feel natural and human. The ban governs text the agent writes. A user's own writing sample is a direction, so ask before keeping or cutting em dashes in it.
- **R-15 CTA.** No generic calls to action ("Get Started", "Learn More", "Explore", "Discover"). Resume equivalent: no "Open to opportunities" style closers.
- **R-16 Buzzwords.** Forbidden: "AI Powered", "Next Generation", "Revolutionary", "Seamless", "Cutting Edge", "Intelligent", "Ultimate", "Powerful", "Effortless". Use specific language that explains the real benefit. Show evidence, not claims.
- **R-17 Data and numbers.** Forbidden: numbers and statistics without a real source. If real data is not available, show no numbers at all. Empty is better than deceptive.
- **R-18 Testimonials.** Forbidden: fictional reviews, random names, invented endorsements. No recommendations or quotes on the resume unless the user supplied them.
- **R-36 No fabricated claims.** Forbidden: inventing security, compliance or performance claims ("SOC 2 compliant", "300% faster") without real evidence. If there is no real data, show no claim.
- **R-38 Real content or honest placeholder.** Every claim, feature, statistic or name must come from real information or be an explicitly labeled placeholder. An empty section is better than a fabricated one. On a resume, final output carries no placeholders: omit instead.
- **C-5 Evidence over claims.** Anything presented as fact is real and verifiable, or it is not shown at all.

## Part E. Resume-specific rules

### Banned on a resume

Everything in Parts B to D, plus:

- Self-description with no evidence: passionate, results-driven, dynamic, detail-oriented, self-starter, team player, hard-working, motivated, driven, enthusiastic, creative thinker, go-getter, visionary, rockstar, ninja, guru, expert (unless the user states it).
- Corporate verbs that say nothing: leveraged, spearheaded, orchestrated, championed, synergized, utilized, facilitated, streamlined, empowered, revolutionized, pioneered, ideated, operationalized, drove (as in "drove results"), "responsible for", "worked on", "helped with", "assisted in", "involved in".
- Puffery adjectives: cutting-edge, seamless, robust, scalable (unless a measured load is stated), enterprise-grade, production-grade (unless deployed and the user confirms), high-performance, state-of-the-art, innovative, best-in-class, world-class, comprehensive, end-to-end (unless it literally spans client to deployment and you name both ends), full-fledged, intuitive, sleek, modern.
- Stacked adjectives ("a fast, scalable, secure, modern platform").
- Rule-of-three padding ("designed, developed, and deployed" as filler; "fast, reliable, and scalable").
- Vague outcome claims: "improved performance", "increased efficiency", "enhanced user experience", "reduced complexity", "significantly", "drastically", "greatly".
- Em dashes, en dashes as connectives, double hyphens as dashes, semicolon chains, exclamation marks, emojis, quotation marks as emphasis, parenthetical asides longer than a few words.
- Trailing negation tags ("no downtime, no hassle") and "not just X but Y" constructions.
- Soft closers in the summary ("looking to leverage my skills", "eager to contribute").
- Third-person self-reference. Write bullets as implied first person with no pronouns ("Built a webhook retry queue", not "I built" and not "He built").

### Required

- Plain, concrete, specific language. Name the library, protocol, provider, data size, file count, endpoint count, test count, or deployment target.
- Each bullet follows one shape: **verb + what was built + how (the tool or technique) + concrete result.** The result can be a count from the repo, a behavior ("retries failed webhooks with exponential backoff up to 5 attempts"), or what it replaced or connected to. If the result is only a behavior, say the behavior.
- Strong, specific verbs that match the evidence. Use the table below.
- Sentence case. No trailing periods on bullets (or periods on all of them, consistently; this skill uses none). Past tense for finished work, present tense only for work still in progress and maintained.
- Vary the opening verbs across a project and across the page. Do not start two bullets in the same project with the same verb, and do not repeat a verb more than twice on the page.
- Keep each bullet to one line where possible and two lines at most (about 110 to 200 characters).
- The summary, if present, is one or two plain sentences stating role, years or scope that the user supplied, and the main stack. No adjectives about the person.

### Verb guide

| Evidence in repo | Verb that fits |
|---|---|
| User wrote the module alone | Built, Wrote, Designed |
| User replaced or restructured something | Rewrote, Replaced, Migrated, Split |
| Integration with an external service | Integrated, Connected, Wired up |
| Tests, CI, tooling added | Added, Set up, Automated |
| Performance change with a measurement in repo | Reduced, Cut, Sped up (only with the measured figure) |
| Shared work, user has a minority of commits | Contributed, Implemented (name the part) |
| Deployment config present | Deployed, Containerized, Configured |
| Debugging or fix with a described cause | Fixed, Diagnosed, Traced |

### Examples

| Slop | Rewrite |
|---|---|
| Spearheaded the development of a robust, scalable backend leveraging cutting-edge technologies | Built a REST API in FastAPI with 14 endpoints backed by PostgreSQL |
| Seamlessly integrated payment processing to enhance user experience | Integrated Stripe Checkout and handled its webhooks, including signature checks and replays |
| Responsible for improving performance of the application | Cut dashboard load time from 3.1 s to 1.2 s by caching the three slowest queries (figures from `docs/perf.md`) |
| Passionate full-stack developer with a track record of delivering innovative solutions | Full-stack developer working in Python and TypeScript. |
| Utilized Docker to streamline deployments | Containerized the API and worker with Docker Compose for one-command local setup |

(The sample figures above are illustrations of shape only. Never copy numbers from this table.)

## Part F. Conflicts and how to resolve them

- "Use paragraphs, not bullets" (write-like-a-human) does not apply to the Projects, Experience and Skills sections of a resume. Bullets of discrete achievements are the intended use of bullets. The Summary stays prose.
- "No headers in short pieces" does not apply. The layout spec requires section headings.
- "No bold" does not apply to the name, project names and job titles that the layout spec bolds. No other bold inside sentences.
- Hedging: do not hedge on a resume. If the evidence is weak, drop the claim or lower its scope.
- Chat messages to the user (the wrap-up, the include/exclude table) also follow Parts B and C. Keep them plain, with no closing pleasantries.

## Part G. Draft, audit, final loop (run before finalising)

1. **Draft** the resume text applying everything above. Read it aloud mentally: does it vary in length, prefer specific detail and simple constructions?
2. **Audit.** Answer briefly: "What makes this obviously AI generated?" and "Does it state any fact, name, number, date or citation that is not in the source?" A fabrication is a defect even when it sounds better than the vague original.
3. **Final.** Revise to address both answers. Run `scripts/check_writing.py resume.json`. Check once more for em dashes and en dashes. Any hit means the draft is not done.

### Checklist (every line must be true)

- [ ] No fabricated numbers, names, dates, employers, degrees or claims; every number has an `evidence` entry
- [ ] No buzzwords from Parts B, C and E
- [ ] No em dashes or connective en dashes anywhere in the output
- [ ] No excessive quotation marks, no all-caps emphasis, no emojis
- [ ] Every bullet names what the user did (actor and verb), with no actorless passive and no software that "understands" or "decides"
- [ ] No forced rule of three, negative parallelism, staccato drama, theatrical takeaways, aphorism formulas or false ranges
- [ ] No temporal runway clichés or generic positive conclusions
- [ ] Bullets in sentence case, opening verbs varied
- [ ] Skills come only from technologies seen in the selected projects (or supplied by the user)
- [ ] Reads like a person wrote it: specific detail present, uneven sentence lengths, no template phrasing

## Attribution

Parts C and D reproduce rules from anti-slop, Copyright (c) 2026 Miqdad Badjuber, MIT License, https://github.com/miqdadbadjuber/anti-slop. Part B reproduces the `write-like-a-human` skill. Part E and the resolution notes were added for this skill.
