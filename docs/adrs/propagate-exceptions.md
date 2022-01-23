# Propagate Exceptions

## Status

Accepted

## Context

fidelipy uses Playwright to interact with fidelity.com.  An exception may happen if, for
example, the id of a web element changes.  These exceptions can be handled by fidelipy
or propagated to the user.

## Decision

fidelipy will log all exceptions and propagate exceptions from functions that do not
return a Boolean to indicate success or failure.  It is important for the user to know
exactly what failed to support bug reporting and fixing when fidelity.com changes.

## Consequences

fidelipy is more agile and maintainable in an unstable environment.
