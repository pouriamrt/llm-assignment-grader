# Stretchy Words

## Requirements understanding

We need to find which words can become the string S by extending letter groups. Groups must be extended to size 3 or more.

## Solution approach

Compare the word to S and allow extending runs when S has at least 3 of that letter.

## Output

Ran the code with heeellooo and ["hello","hi","helo"] and got 1.

## FSA graph

We have states for each character position. We can extend a group if S has 3+ of that character.

## State-transition table

| State | Condition | Next |
|-------|-----------|------|
| match | same char | continue |
| extend | S run >= 3 | continue |

## Deterministic vs non-deterministic

It's deterministic because we only have one way to process each character.
