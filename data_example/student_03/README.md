# Assignment: Stretchy Words

## Requirements understanding

Given string S and a list of words, count how many words are "stretchy" — meaning we can extend their letter groups (to size >= 3) so the word equals S.

## Solution approach

I used run-length encoding. For each word I check if its RLE can "expand" to match S's RLE under the rule that a group can only grow if the target group in S has length >= 3.

## Output

Tested with the example: S = "heeellooo", words = ["hello", "hi", "helo"]. Output: 1. Only "hello" is stretchy.

## FSA graph

Not included (out of time).

## State-transition table

(Partial) — same idea as RLE: accept when query groups can match S groups with the extension rule.

## Deterministic vs non-deterministic

Deterministic: we process one group at a time, no choices.
