# Propagate Exceptions

## Status

Accepted

## Context

fidelipy uses Selenium to interact with fidelity.com.  An exception may be raised by any
function at any time.  For example, the id of a web element may change, and Selenium
would not be able to find it.  These exceptions can be handled by fidelipy or propagated
to the user.

## Decision

fidelipy will propagate exceptions from Selenium to the user.  It is important for the
user to know exactly what failed to support bug reporting and fixing when changes are
made to fidelity.com.

## Consequences

fidelipy is more agile and maintainable in an unstable environment.
