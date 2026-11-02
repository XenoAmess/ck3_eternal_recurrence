# MXCSR boundary of the held 880340 queue-growth path

This is a source and architecture review, with conditional arithmetic examples. It changes no M2 API or implementation and reports no CPU execution, game state, or performance result. M2 owns the queue-scoped FP interface and its implementation.

## Source boundary

The complete held normal body is `[880340,880423)`, 227 bytes, SHA-256 `66d4e2b957668fdb3249ad35233443bcfbcf78d35e98b96914a5d4b2a3fff133`; its complete ASM has SHA-256 `ac11ec3365828749362cd276f82632680cdf4fc1de6479ec9ce3b52a812bc935`.

The DWORD count at object+0xC must equal the DWORD capacity at object+8 to enter growth. `MOVD xmm0,ecx` at 88036D places that raw DWORD in the low lane. The three FP instructions are 88037B `CVTDQ2PS`, 880385 `MULSS` and 88038D `CVTTSS2SI eax,xmm0`. The multiplier is a fresh memory operand at image+0x49F64F0; no authenticated value is supplied. In particular, 1.5 is not an established game constant.

Current `FullCopy437Api.Input`, `CallResult`, their declaring 185 entry/return and 155 register types carry GPR/XMM/DF state but omit MXCSR. Identical values in those interfaces therefore need not identify identical FP behavior. No captured MXCSR or current CPU/OS agreement is supplied.

## Minimum architectural rules

The selected authority is Intel SDM revision 093, September 2026, reached through the [official SDM index](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html).

| Actual instruction | Relevant behavior |
| --- | --- |
| `MOVD xmm0,ecx` | Copies low32; zeros XMM bits127:32. The three other converted lanes are zero. |
| `CVTDQ2PS xmm0,xmm0` | Four signed32 conversions; inexact conversion follows RC. Listed FP condition: Precision. |
| `MULSS xmm0,[factor]` | Low-lane product; preserves upper lanes. Listed conditions: Invalid, Denormal, Overflow, Underflow, Precision. |
| `CVTTSS2SI eax,xmm0` | Signed32 truncation toward zero, independent of RC. Invalid/Precision, no Denormal. Masked Invalid writes `80000000`; this is not Java saturation. |

Instruction references: [Volume 2A](https://cdrdv2.intel.com/v1/dl/getContent/671199), printed 3-211–213 and 3-255–256; [Volume 2B](https://cdrdv2.intel.com/v1/dl/getContent/671241), 4-55–56 and 4-150–151.

MXCSR status0–5 is sticky; masks7–12 use 1=masked. RC13–14 selects nearest-even/down/up/zero. DAZ6 substitutes signed zero for subnormal inputs and suppresses Denormal. FTZ15 applies with Underflow masked; it flushes tiny results and raises Underflow/Precision, including exact-tiny products. Without FTZ, an exact tiny masked result raises neither of those two conditions. Old flags alone do not trigger a fresh exception. On an unmasked condition, the faulting destination is not committed. Mixed pre/post conditions require Intel's priority rules; do not OR every hypothetical condition. OS delivery and handler continuation remain outside the supplied contract. [Volume 1](https://cdrdv2.intel.com/v1/dl/getContent/671436), §§10.2.3, 11.5.2–3, Table4-9 and AppendixD, printed 10-4–5, 11-15–18, 4-19–20 and D-22–23.

## Conditional counterexamples

These are owner-derived fixtures, frozen before reviewing either model answer. They are not captured machine inputs. Each has count=capacity, initially clear status, supported DAZ controls, all six masks set and DAZ=FTZ=0 unless explicitly varied. Hex factors are supplied binary32 bits. Assume the source memory reads complete.

| Fixture | Exact derivation and observable distinction |
| --- | --- |
| RC during conversion: count `01000001`, factor `40000000` (2) | Count16777217 lies halfway between adjacent floats. RC nearest gives CVT `4B800000`; upward gives `4B800001`. Multiplication by2 is exact: `4C000000`/`4C000001`, integers33554432/33554436. After the actual signed max, allocation RDX is `10000000`/`10000020`. Precision originates at CVT. |
| RC during multiplication: count `00800001`, factor `3F800001` | Count8388609 converts exactly to `4B000001`. Exact product is 8388610+2^-23. Nearest/upward products are `4B000002`/`4B000003`, integers8388610/8388611. Allocation RDX is `04000010`/`04000018`; Precision originates at MUL, while CVTT is exact. |
| Precision at truncation: count3, factor `3F000000` (0.5) | CVT and MUL are exact; product is1.5 (`3FC00000`). Masked CVTT returns1. With Precision unmasked, stop at88038D with prior RAX=3, rather than writing1. |
| Invalid conversion: count1, factor `7F800000` (+infinity) | Multiplication by1 does not overflow. Masked CVTT writes EAX=`80000000`, zero-extending RAX; unmasked Invalid stops at88038D and retains prior RAX. |
| Tiny factor: count1, factor `00000001` | DAZ0/FTZ0: exact MUL retains `00000001` with Denormal; CVTT returns0 and adds Precision. DAZ1 gives zero without those new conditions. DAZ0/FTZ1 gives zero with Denormal/Underflow/Precision at MUL. With PM0, UM1, DM1, the first Precision stop moves from88038D (FTZ0) to880385 (FTZ1). Equal EAX0 and eventual capacity2 hide different XMM/status/stop paths. |
| Existing status: count2, factor `40000000` (2) | All three operations are exact. Incoming PE=1 remains1, including with PM0; incoming PE=0 remains0. Missing incoming status cannot be synthesized from equal numeric results. |

The allocation examples follow actual `LEA esi,[rax+1]` modulo32, `CMP/CMOVL` signed max, then `MOV edx,ebp; SHL rdx,3`. They do not imply unsigned-max, saturation, or a 64-bit CVTT destination. A finite integer/Fraction checker confirmed 23 arithmetic relations for these fixtures and M2's independent RC fixture; it did not execute or emulate SSE or test flag handling.

## First-fault boundary

| FP stop PC | State already reached; destination retained on fault |
| --- | --- |
| 88037B | Before the RBP spill at88037E. XMM0 still contains the MOVD raw integer bits. |
| 880385 | RBP spill and `EBP=ESI` have occurred. XMM0 retains the converted value. |
| 88038D | The spill has occurred. Prior full RAX is retained; no EAX write or upper32 zeroing occurs. |

Every listed stop precedes allocator CALL88039F and all later calls/stores. A stopped prefix is not a normal return. Preserve actual earlier RAM/GPR effects; OS delivery, exception handling, NaN payload policy and the complete mixed-exception flag algorithm are not implemented by this checklist.

## Safe narrow subset and remaining gap

A sufficient numeric subset is: every actually converted integer is exactly binary32-representable; scalar operands are finite normal numbers or signed zero; their product is exact, finite and normal or signed zero; and the truncand is an integral valid int32. Those conditions remove new FP conditions and numeric dependence on RC/DAZ/FTZ. They are sufficient, not necessary. Merely saying “exact product in range” fails for1.5, and “representable multiplier” alone admits subnormal inputs.

This subset does not recover incoming sticky flags. Outside it, required controls/masks and first-fault behavior need explicit state or an explicit unsupported/unknown outcome. Nongrowth skips these FP instructions, but that fact does not supply unknown state. Opaque callees can change post-call state; neither their pre-call MXCSR nor the standard startup value establishes their actual result. M2's separate queue-scoped transport work owns that interface gap.

## Review and validation limits

Two independent local-model audit roles each received the complete current source declarations, actual ASM and bounded primary-source notes. Both R1 answers were rejected for substantive arithmetic or fault-state errors. One necessary correction per role produced one repeated semantic rejection and one output-limit truncation, discarded unread; no third round or complete model Oracle was adopted. The checklist and fixtures are owner-written. Primary-source review, actual ASM inspection and finite exact arithmetic checks support this report; no Java compilation, old test rerun, PE read, Game/Dev/GET action or hardware FP validation occurred.
