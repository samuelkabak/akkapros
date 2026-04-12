# Word Count Verification

This page is a worked verification note for the lexlinks construct corpus word
counts surfaced by metrics. It exists for one reason: the public `Total words`
lines in the metrics report must be auditable against a reference method that
does not come from `src/akkapros/lib/metrics.py`.

The reference uses the checked-in phone artifacts from the lexlinks construct
demo:

- original stream: `demo/akkapros/lexlinks/results/erra_construct_ophone.txt`
- accentuated stream: `demo/akkapros/lexlinks/results/erra_construct_phone.txt`

## Counting Contract

The reference counter works directly from phone rows after front matter is
removed.

For this verification, count one word whenever a non-silence row starts:

1. at the beginning of the stream
2. immediately after any silence or punctuation row
3. immediately after a previous non-silence row whose boundary marker is `F`

Do not increment the count across internal boundaries such as:

- syllable boundaries
- hyphen boundaries
- explicit merge connectors
- internal merge connectors

This method is intentionally simple. It counts merged-word starts from the
phone-row boundary contract instead of reusing metrics word extraction.

## Reference Values

Applying that counting method to the checked-in lexlinks fixtures yields these
fixed totals:

- original word count: `1169`
- accentuated word count: `963`

The same corpus also carries these frontmatter-derived prominence values in the
metrics output:

- function words: `189`
- explicitly linked words: `63`
- prominence candidates: `917`

The prominence-candidate count follows the documented formula:

`917 = 1169 - 189 - 63`

## Required Metrics Surfaces

The automated regression tied to this note asserts that metrics emits:

- `Total words: 1169 words`
- `Total words: 963 words`
- `Function words: 189 words`
- `Explicitly linked words: 63 words`
- `Prominence candidates: 917 words`

If any of those values change, either a regression was introduced or the
artifact contract changed and this note must be updated together with the new
expected values.
