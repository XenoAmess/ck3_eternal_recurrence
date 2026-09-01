# kaishek-validator

Schema-aware, fail-closed validation for the lossless `kaishek-syntax` CST.
`Validator` accepts a parser `ParseResult` (or `Document`) and a profile, then
returns source-spanned diagnostics without modifying the CST. The concrete
`Ck3Profile11906` lives in `kaishek-ck3-11906-profile`; this module depends only
on the profile API and can validate any implementation of its schema contract.
Unknown directories/opcodes and trigger/effect domain mismatches are errors;
unsupported constructs are never silently ignored.  Root declaration names
are checked for duplicate definitions, while nested CK3 executable sequences
and opcode argument blocks retain ordered repeated keys.
