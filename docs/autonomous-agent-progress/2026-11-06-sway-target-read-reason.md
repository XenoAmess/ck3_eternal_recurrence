# Retain the Sway target-read refusal reason

The Sway target consumer used one fixed `current selected Sway target read unavailable` exception message for every non-Known result. That hid the typed read's original refusal reason from the existing scheduler error archive.

The same exception now retains at most 1024 characters of `PlanningReadResult.Unavailable.reason`. The original prefix, exception type and throw frontier remain. A null or other non-Known result keeps the previous fixed message. The Known object, read count, result bookkeeping, scopes, guards, target request and submit path are unchanged; no packet, dispatch, source payload or observation reference is appended.

Validation: one changed translation unit compiled successfully in 5.0649194 seconds, producing 9 classes. All class structures were identical, with no new type, field, method or API. The single raw source span inverts exactly, and formal source equals the qualified current-source candidate. Independent review also checked the existing error propagation and archive route. No mirrored diagnostic test or old green suite was rerun.

This is a diagnostic software change. The latest actual Sway refusal, runtime loading and a useful completed scheme still need their own evidence; older job failures are not assumed to be the current cause.
