# Minimize Input Validation

## Status

Accepted

## Context

fidelipy accepts inputs like account number, stock symbol, quantity in shares or
dollars, and limit price in dollars.  These inputs can be validated before passing them
to fidelity.com, or the validation can be left to fidelity.com.

## Decision

fidelipy will minimize input validation and let fidelity.com report most errors.
Validation by fidelipy would require knowledge of the legal input formats and ranges
which may change over time.  fidelity.com has perfect knowledge of the legal input
formats and ranges.  Users can easily read the popup warning and error dialogs on the
website and correct their input strings.

## Consequences

fidelipy is more generic in that no assumptions are made about input formats.  It is
easier to maintain in that no modifications are necessary for certain future input
format changes.
