# Native army route read status

The CK3 1.19.0.6 `ReadUnitRoute` reader previously published an empty
`route_province_ids` array both for a valid zero-count route and for an
invalid or unresolvable native path. Its existing route and move-target
fields are unchanged. Each native army row now also publishes:

| `route_read_status` | `route_source_count` | Meaning |
| --- | ---: | --- |
| `complete_empty` | `0` | Header passed the existing bounds checks; no path entries. |
| `complete_nonempty` | positive | Paused read resolved every entry; array length equals source count. |
| `target_only` | positive | Running-map read checked only the last entry; the full route was not traversed. |
| `invalid_header` | `null` | Native count/capacity failed bounds checks. |
| `unresolved_entry` | positive | Header was valid but a path pointer or Province did not resolve. |
| `not_attempted` | `null` | Contract default for a row without a route read. |

The Python normalizer rejects contradictory status/count/route/target
combinations. Older native rows with neither new field remain accepted but
provide no completeness proof. A planner may treat a paused route as complete
only for `complete_empty` or `complete_nonempty` with the matching source
count. `target_only`, absent fields and every failure status leave full route
completeness unproven. This evidence does not enumerate hostile armies or
approve any H3937 date advance.

This is an additive source change to the DLL described by
`h3937-province-local-siege-port.md`. A formal combined H3937 receiver
observation needs a newly built DLL containing both additions, its own SHA,
ordinary rebind and a fresh no-action session. It cannot combine an old DLL
route observation with a later Province read as one same-frame result.
