# Evidence behind the lexicons

Do language studies actually back these concepts — the claim that some words *indicate* a
concept and others *rule it out*? For a good number of them, yes. This page answers that per
lexicon: which rest on established linguistics (often with an openly-licensed word list you can
copy), which rest on a recent finding about model output, and which are craft heuristics with no
study behind them.

Where a lexicon draws terms from an outside list, that list is openly licensed — MIT or Apache-2.0.
Proprietary resources such as LIWC are left out on purpose. Citing a finding is not the same as
copying a list: several concepts here are grounded in a paper or book whose *idea* is cited without
any text being lifted.

The citation lives with the lexicon: a `source` line in its definition, rendered in its row on the
[lexicon pages](lexicons/index.md), so it cannot drift from the code. This page is the narrative
behind those one-line citations and the full bibliography.

## What each concept rests on

**Politeness.** The classic account is Brown & Levinson's *Politeness: Some Universals in
Language Usage* (1987): politeness works through indirection, deference, and softening a
face-threatening act. The computational version is the Stanford Politeness Corpus — about ten
thousand requests annotated for politeness — and a classifier built on lexical and syntactic
politeness features (Danescu-Niculescu-Mizil, Sudhof, Jurafsky, Leskovec & Potts, ACL 2013). The
[paper](https://nlp.stanford.edu/pubs/politeness.pdf) and its Apache-2.0
[implementation](https://github.com/sudhof/politeness) name the strategies — gratitude,
deference, greeting, indirection — that the shipped `Politeness` list draws its generic markers
from (`appreciate it`, `grateful`, `would you mind`, `sorry to bother`). The theory also grounds
the `rules_out` side: sarcasm and profanity are face-threatening, so a "please" wrapped around an
insult is not polite — which is exactly what `Politeness.rules_out` encodes.

**Hedging and boosters.** "Hedge" is Lakoff's term (1973) for words that make a proposition
fuzzier. Hyland's *Metadiscourse* (2005) gives the working taxonomy: **hedges** (`might`,
`perhaps`, `seems`, `possibly`, `likely`, `presumably`) signal a tentative claim, and **boosters**
(`clearly`, `obviously`, `definitely`, `undoubtedly`) signal conviction. That opposition is why
`Hedging` and `Overclaim` are two lexicons: `Overclaim.rules_out` holds the hedge words, so an
over-confident claim softened by a "may" or "typically" resolves to `denied` rather than firing.
The shipped lists draw their epistemic markers from that taxonomy; for an annotated resource, the
CoNLL-2010 Shared Task released uncertainty-cue labels over biomedical text and Wikipedia
([Farkas et al.](https://aclanthology.org/W10-3001.pdf)).

**Intensifiers.** `EmptyIntensifier` targets amplifiers — `very`, `really`, `extremely`,
`completely`, `totally`. Corpus grammar treats these as a class of degree adverbs that have been
semantically bleached (`very` began as an adjective meaning "true") and are strongly
register-dependent — common in speech, thinner in edited prose (Quirk et al., *A Comprehensive
Grammar of the English Language*, 1985; Biber et al., *Longman Grammar of Spoken and Written
English*, 1999). The point the lexicon makes — that the intensifier adds heat, not information —
is the standard reading.

**Weasel words.** `UnsourcedAuthority` ("studies show", "experts agree", "some argue",
"reportedly") is the "weasel word" of Wikipedia's style guide, and there is NLP work detecting
exactly this: Ganter & Strube trained a hedge detector on Wikipedia's own weasel-word tags
([ACL-IJCNLP 2009](https://aclanthology.org/P09-2044.pdf)). Recasens, Danescu-Niculescu-Mizil &
Jurafsky's bias-language work (ACL 2013) released a lexicon of hedges, factive verbs, and
subjective intensifiers built for the same problem — the source for the impersonal-attribution
phrasings the list now carries.

**Temporal expressions.** `DueDate`, `ClockTime`, `Recurrence`, and `Duration` are a keyword
approximation of a solved problem: temporal expression recognition. The standard is TimeML /
TIMEX3 (Pustejovsky et al., 2003), with mature taggers such as SUTime (Chang & Manning, LREC
2012) and HeidelTime. If you need these signals for real work rather than a cheap flag, a temporal
tagger will beat a word list — it normalizes "next Friday" to a date and handles recurrence
properly. The lexicons are useful as a dependency-free tripwire, not as the parser.

**Slop and excess vocabulary.** The strongest empirical result here is Kobak, González-Márquez,
Horvát & Gerlach, "Delving into LLM-assisted writing in biomedical publications through excess
vocabulary" ([arXiv 2406.07016](https://arxiv.org/abs/2406.07016);
[*Science Advances* 2025](https://doi.org/10.1126/sciadv.adt3813)). Borrowing the "excess
mortality" idea, they measured which words spiked in 14M-plus PubMed abstracts after ChatGPT —
style words like *delve*, *underscore*, *showcasing*, *nuanced*. The shipped `Slop` list stays
hand-curated (a few of those excess words are folded in), but the
[slop-forensics](https://github.com/sam-paech/slop-forensics) project — MIT-licensed — derives a
much larger list statistically. Fold that in for the empirical version; just remember these lists
are dated, tracking a model generation and drifting as models change.

**Sycophancy and verbal tics.** Sycophancy — models agreeing with a user against the evidence —
is documented in Sharma et al., "Towards Understanding Sycophancy in Language Models"
([arXiv 2310.13548](https://arxiv.org/abs/2310.13548), Anthropic), which found the pattern across
five RLHF assistants and traced it to preference data. Note the gap: that paper is about
*behavior*, not vocabulary. The specific openers in `Sycophancy` ("great question", "you're
absolutely right") are craft informed by that finding, not lifted from it. The nearest thing to a
marker list is recent work cataloguing model "verbal tics" and scoring them with a Verbal Tic
Index ("The Rise of Verbal Tics in Large Language Models", 2026 preprint,
[arXiv 2604.19139](https://arxiv.org/abs/2604.19139)) — it names sycophantic openers, hedging
frames like "it's important to note", and overused vocabulary. It is a single recent preprint;
treat it as a lead, not settled ground.

**Prompt injection.** `Injection` is a tripwire for a documented attack class: Perez & Ribeiro,
"Ignore Previous Prompt" ([arXiv 2211.09527](https://arxiv.org/abs/2211.09527)) and Greshake et
al. on indirect injection ([arXiv 2302.12173](https://arxiv.org/abs/2302.12173)). The literature
also says why a word list is not a defense — injection phrasing is adversarial and mutates — which
is exactly what the lexicon's `fix` says: treat retrieved text as data, and use the match to log
and strip, not to gate.

## The ones with no study behind them

The rest are judgements about good agent output with nothing to cite: padding and filler
(`Padding`), stalling patterns (`EngagementBait`, `ContrastCliche`), over-caution (`Disclaimer`,
`Refusal`), breaking character (`SelfReference`, `Anthropomorphic`, `SystemLeak`). The domain
group is topic keyword sets — the relevant field is text classification,
where you would train a classifier rather than curate a lexicon, so these are best read as a
fast, transparent stand-in. The task-capture signals (priority, ownership, due-date *semantics* as
opposed to date *strings*) are product decisions about what a to-do system should notice, not
claims about language.

None of that makes them wrong. It makes them opinions, and the way to keep an opinion honest in a
substring matcher is precision: prefer phrases to bare words, and use `rules_out` to cancel the
obvious false positives. That is the same advice as [Writing a lexicon](writing-a-lexicon.md) —
it just matters more when there is no corpus to fall back on.

## Sources

- Brown, P. & Levinson, S. (1987). *Politeness: Some Universals in Language Usage.* Cambridge University Press.
- Lakoff, G. (1973). Hedges: A study in meaning criteria and the logic of fuzzy concepts. *Journal of Philosophical Logic* 2(4).
- Quirk, R., Greenbaum, S., Leech, G. & Svartvik, J. (1985). *A Comprehensive Grammar of the English Language.* Longman.
- Biber, D. et al. (1999). *Longman Grammar of Spoken and Written English.* Longman.
- Hyland, K. (2005). *Metadiscourse: Exploring Interaction in Writing.* Continuum.
- Ganter, V. & Strube, M. (2009). [Finding Hedges by Chasing Weasels](https://aclanthology.org/P09-2044.pdf). *ACL-IJCNLP.*
- Farkas, R. et al. (2010). [The CoNLL-2010 Shared Task: Learning to Detect Hedges and their Scope](https://aclanthology.org/W10-3001.pdf). *CoNLL.*
- Chang, A. & Manning, C. (2012). SUTime: A Library for Recognizing Time Expressions. *LREC.* (TimeML / TIMEX3 lineage)
- Danescu-Niculescu-Mizil, C., Sudhof, M., Jurafsky, D., Leskovec, J. & Potts, C. (2013). [A Computational Approach to Politeness with Application to Social Factors](https://nlp.stanford.edu/pubs/politeness.pdf). *ACL.* — corpus and code: [sudhof/politeness](https://github.com/sudhof/politeness)
- Recasens, M., Danescu-Niculescu-Mizil, C. & Jurafsky, D. (2013). Linguistic Models for Analyzing and Detecting Biased Language. *ACL.*
- Perez, F. & Ribeiro, I. (2022). [Ignore Previous Prompt: Attack Techniques For Language Models](https://arxiv.org/abs/2211.09527). *arXiv.*
- Greshake, K. et al. (2023). [Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173). *arXiv.*
- Sharma, M. et al. (2023). [Towards Understanding Sycophancy in Language Models](https://arxiv.org/abs/2310.13548). *arXiv.*
- Kobak, D., González-Márquez, R., Horvát, E.-Á. & Gerlach, M. (2024). [Delving into LLM-assisted writing in biomedical publications through excess vocabulary](https://arxiv.org/abs/2406.07016). *arXiv*; *Science Advances* (2025), [doi:10.1126/sciadv.adt3813](https://doi.org/10.1126/sciadv.adt3813).
- The Rise of Verbal Tics in Large Language Models: A Systematic Analysis Across Frontier Models (2026). [arXiv 2604.19139](https://arxiv.org/abs/2604.19139).
- Paech, S. [slop-forensics](https://github.com/sam-paech/slop-forensics).
