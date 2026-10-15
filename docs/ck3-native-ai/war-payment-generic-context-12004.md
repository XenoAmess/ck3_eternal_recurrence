# CK3 1.20.0.4 generic ADD raw context

This default-OFF candidate captures raw source inputs at personal ADD return PC
`0x28A6D7C`. It does not identify a military-only paid maintenance component.
Exact build is1.20.0.4 / Steam25734779 / EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.

## Pointer source proof

The already retained complete574B function `0x28A6D10..0x28A6F4E` has SHA
`f2e377a5e4948042852a95bd5b4e0fe3d38159defb8eb5f823ec0fabb33fe348`.
The source means **context = *(Character+0x1C0)**. Character+0x1C0 is a pointer
field, rather than the address of an inline context object.

| RVA | Exact bytes | Instruction |
| --- | --- | --- |
|28A6D16|48 8B 81 C0 01 00 00|mov rax,qword ptr[rcx+1C0]|
|28A6D1D|4C 8B F9|mov r15,rcx|
|28A6D20|48 85 C0|test rax,rax; the following JE exits on null|
|28A6D29|4C 8B 40 28|mov r8,qword ptr[rax+28]|
|28A6D32|48 8B 98 C0 02 00 00|mov rbx,qword ptr[rax+2C0]|
|28A6D39|48 2B 98 C8 02 00 00|sub rbx,qword ptr[rax+2C8]|
|28A6D45|48 8B 70 30|mov rsi,qword ptr[rax+30]|
|28A6D4E|49 8D 3C 30|lea rdi,[r8+rsi]; arithmetic only|
|28A6D52|48 2B DF|sub rbx,rdi|
|28A6D71|4D 8B C7|mov r8,r15; pass original Character|
|28A6D77|E8 C4 80 FB FF|call285EE40; actual return28A6D7C|

Thus `a=context[2C0], b=context[2C8], c=context[28], d=context[30]` supplies
signed64 wrapping `a-b-(c+d)`, with the source positive guard before this ADD.
No `lea rax,[rcx+1C0]` constructs an inline object. The byte-audit receipt is
[POINTER-GETTER-AUDIT.actual.json](acceptance/2026-10-15-war-payment-generic-context/POINTER-GETTER-AUDIT.actual.json).
This reuses preserved source bytes; no new EXE read or hash was performed.

## Existing getter comparison and open meaning

The exact4 cash binder selects income2BCA940, expense context Character28BFD80,
full expenses2BCB160, current military monthly rate2C13F60 and all-raised alternative
military monthly rate2C152B0. The shared reader calls their existing native ABIs;
it does not read the four settlement-context offsets. The settlement function
does not call these five getters directly. Its transitive callees are not closed.
The expense-context getter returns a Character; no evidence equates it with
the raw secondary context pointer loaded at Character+1C0.

Consequently no field name is inferred from numerical similarity or from these
getter bindings. Exact2C0/2C8/28/30 producers, freshness, caller/date cadence and
military-only applied portion remain unknown. The historically referenced finite
getter map onZ: was unavailable at its exact recorded path during this review;
there was no wider source/xref/image scan. maintenance_attribution stays unclosed.

## Focused reusable regression

The checked-in candidate fixture under native_bridge/tests/war_payment_generic_context
is identical to the actual136-check/16-case native source. Its actual MSVC argv and
result pins are retained beside it. The repo-relative runner freezes exact inputs,
uses installed MSVC, gates EXE execution on exact Defender verification, and emits
append-only receipts in an explicitly supplied external build directory. It does
not build or deploy the whole bridge. The relative-path adaptation itself received
syntax and plan-only checking; the prior native result is not relabeled a new run.

Python strictconsumer regression uses relative fixtures and the actual production
normalizer. The native wire is synthetic, including its absolute pointer values;
it does not establish actual OS unwind through a CK3 detour or live-game inputs.
All unavailable/changed fields remain raw unknown; the extension cannot promote
maintenance attribution or change existing boarding qualification.

## 2026-10-16：负 NET 分配函数已闭合，军事归因继续未知

[经济 NET 与28A6B50专题](war-payment-net-settlement-allocation-12004.md)补齐574B负支两次directCALL的435B纯整数分配函数。它没有军事getter或类别来源，正常域有内外两次截断，不能全域化简为deficit*component/total，也不能强制两笔SUB之和等于-NET。现有kind2 generic足够支持符合资格的一笔实际正NET钱包对账partial；完整同次settlement entry/return和军事applied component仍未实现/未闭合，不因source新解码提升militaryclaim。
