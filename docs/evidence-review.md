# Manual Evidence And Claim Review

The evidence workspace helps reviewers organize human fact-checking context around saved analyses. It does not verify claims automatically and does not turn evidence counts into `REAL` or `FAKE` labels.

## Workflow

```text
Prediction
-> Explanation
-> Manual Claims
-> Manual Evidence
-> Human Review
-> Verified Label
-> Production Performance
```

1. A saved analysis stores the submitted article, model prediction, probabilities, and optional explanation.
2. A reviewer opens the evidence workspace for that saved analysis.
3. The reviewer manually identifies individual claims from the article.
4. The reviewer manually finds outside references using their own workflow.
5. The reviewer records each reference URL, optional source metadata, excerpt, and notes.
6. The reviewer manually assesses whether the reference `supports`, `contradicts`, is `neutral`, or is `unclear` for one claim.
7. The reviewer uses that context when assigning an optional human-verified `REAL` or `FAKE` label.
8. Reviewed-production metrics use only the explicit human label and the original persisted model prediction.

## What The Model Provides

The model provides:

- predicted label
- `REAL` and `FAKE` probabilities
- confidence
- model metadata
- optional SHAP or feature-attribution explanation

These values explain model behavior. They are not evidence that a claim is true or false.

## What Reviewers Provide

Reviewers provide:

- claim text
- optional claim offsets and notes
- external reference URL
- optional source title, publisher/source name, and publication date
- optional excerpt and reviewer note
- manual evidence assessment
- optional verified review label

The backend stores this information as human-entered text and workflow metadata.

## Backend Boundaries

The evidence subsystem does not:

- fetch URLs
- resolve DNS
- follow redirects
- inspect OpenGraph metadata
- download favicons
- scrape article text
- crawl websites
- call search or fact-checking APIs
- run an LLM
- use RAG or embeddings
- extract claims automatically
- classify evidence automatically
- assign source credibility, publisher trust, or political-bias scores
- set verified labels from evidence
- retrain, promote, archive, or deploy models

URL validation is local and syntactic. The backend accepts only `http` and `https` URL shapes, stores the original URL, and stores a normalized URL for duplicate checks within the same claim.

## Evidence Summaries

Evidence summaries report:

- total claims
- claims with at least one evidence reference
- evidence coverage percentage
- total evidence references
- assessment counts for `supports`, `contradicts`, `neutral`, and `unclear`
- latest evidence update timestamp

These are workflow readiness indicators. They are not credibility scores.

## Limitations

Manual evidence can be incomplete, stale, contradictory, incorrectly summarized, or attached to the wrong claim. Publisher/source names and excerpts are entered by reviewers and are not independently verified by the backend.

A `supports` assessment means a reviewer judged that one reference supports one claim. It does not mean the platform has proven the entire article is true. A `contradicts` assessment means a reviewer judged that one reference contradicts one claim. It does not mean the platform has proven the entire article is false.

Final verified labels remain explicit human review decisions. The platform never derives them from evidence counts, evidence coverage, source URL, publisher, model confidence, explanation tokens, or monitoring diagnostics.
