# Accept String Arguments

## Status

Accepted

## Context

fidelipy accepts numeric inputs like quantity in shares or dollars and limit price in
dollars.  These inputs can be accepted as types str, Decimal, or int.

## Decision

fidelipy will accept numeric inputs as type str.  int works well for dollars but would
be confusing when applied to shares which have up to three decimal places.  It would
also break if dollar precision is increased beyond two decimal places.  Decimal makes
more sense for quantities with arbitrary numbers of decimal places but is slightly more
cumbersome to use than str.  The goal of fidelipy is to act as a typing assistant to
speed up the trading process.  str is the most generic type for this purpose.

## Consequences

fidelipy is easier to use and understand.
