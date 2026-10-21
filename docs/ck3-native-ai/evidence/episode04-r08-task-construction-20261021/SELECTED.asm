0x28f6ad1 440fb689b84c0000 movzx r9d, byte ptr [rcx + 0x4cb8]
0x28f6ad9 4d69d140260000 imul r10, r9, 0x2640
0x28f6ae0 488db130260000 lea rsi, [rcx + 0x2630]
0x28f6ae7 4903f2 add rsi, r10
0x28f6aea 4c8db118260000 lea r14, [rcx + 0x2618]
0x28f6af1 4d03f2 add r14, r10
0x28f6b0b 448b829c000000 mov r8d, dword ptr [rdx + 0x9c]
0x28f6b12 b889888888 mov eax, 0x88888889
0x28f6b17 41f7e0 mul r8d
0x28f6b1a c1ea04 shr edx, 4
0x28f6b1d 6bc21e imul eax, edx, 0x1e
0x28f6b20 442bc0 sub r8d, eax
0x28f6b23 4b8d0c40 lea rcx, [r8 + r8*2]
0x28f6b27 498d04ca lea rax, [r10 + rcx*8]
0x28f6b2b 4d8dac24e0000000 lea r13, [r12 + 0xe0]
0x28f6b33 4c03e8 add r13, rax
0x28f6f49 48895c2430 mov qword ptr [rsp + 0x30], rbx
0x28f6f4e 498d8424084d0000 lea rax, [r12 + 0x4d08]
0x28f6f56 4889442438 mov qword ptr [rsp + 0x38], rax
0x28f6f5b 488d8d30030000 lea rcx, [rbp + 0x330]
0x28f6f62 e8e9c113ff call 0x1a33150
0x28f6f67 4889b570030000 mov qword ptr [rbp + 0x370], rsi
0x28f6f6e 0f10442430 movups xmm0, xmmword ptr [rsp + 0x30]
0x28f6f73 0f118578030000 movups xmmword ptr [rbp + 0x378], xmm0
0x28f6f7a 8b460c mov eax, dword ptr [rsi + 0xc]
0x28f6fbb 4c8d8530030000 lea r8, [rbp + 0x330]
0x28f6fc2 488d5500 lea rdx, [rbp]
0x28f6fc6 488d4c2458 lea rcx, [rsp + 0x58]
0x28f6fcb e860ab0000 call 0x2901b30
0x2901bec 4881c330010000 add rbx, 0x130
0x2901bf3 8b4f08 mov ecx, dword ptr [rdi + 8]
0x2901bf6 890b mov dword ptr [rbx], ecx
0x2901bf8 0f1007 movups xmm0, xmmword ptr [rdi]
0x2901bfb 0f114308 movups xmmword ptr [rbx + 8], xmm0
0x2901bff 0f104f10 movups xmm1, xmmword ptr [rdi + 0x10]
0x2901c03 0f114b18 movups xmmword ptr [rbx + 0x18], xmm1
0x2901c07 498b06 mov rax, qword ptr [r14]
0x2901c0a 48894328 mov qword ptr [rbx + 0x28], rax
0x2901c0e 498b4608 mov rax, qword ptr [r14 + 8]
0x2901c12 48894330 mov qword ptr [rbx + 0x30], rax
0x2901c6c 498b4640 mov rax, qword ptr [r14 + 0x40]
0x2901c70 48894368 mov qword ptr [rbx + 0x68], rax
0x2901c74 410f104648 movups xmm0, xmmword ptr [r14 + 0x48]
0x2901c79 0f114370 movups xmmword ptr [rbx + 0x70], xmm0
0x2901c7d 488bbdd8000000 mov rdi, qword ptr [rbp + 0xd8]
0x2901c84 4889bdf0000000 mov qword ptr [rbp + 0xf0], rdi
0x2901c8b 488d4c2470 lea rcx, [rsp + 0x70]
0x2901c90 e8db16f8fd call 0x883370
0x2901c95 90 nop 
0x2901c96 418bd5 mov edx, r13d
0x2901c99 488d4c2470 lea rcx, [rsp + 0x70]
0x2901c9e e89d14f8fd call 0x883140
0x2901ca3 488d051627e601 lea rax, [rip + 0x1e62716]
0x2901caa 4889442430 mov qword ptr [rsp + 0x30], rax
0x2901caf 48895c2438 mov qword ptr [rsp + 0x38], rbx
0x2901cb4 488d442430 lea rax, [rsp + 0x30]
0x2901cb9 4889442468 mov qword ptr [rsp + 0x68], rax
0x2901cbe 488b85f8000000 mov rax, qword ptr [rbp + 0xf8]
0x2901cc5 4889442428 mov qword ptr [rsp + 0x28], rax
0x2901cca 488d442470 lea rax, [rsp + 0x70]
0x2901ccf 4889442420 mov qword ptr [rsp + 0x20], rax
0x2901cd4 458bcd mov r9d, r13d
0x2901cd7 488d542430 lea rdx, [rsp + 0x30]
0x2901cdc 488b0dc5d43b03 mov rcx, qword ptr [rip + 0x33bd4c5]
0x2901ce3 e8e8fd6801 call 0x3f91ad0
0x3f916da 48c7403800000000 mov qword ptr [rax + 0x38], 0
0x3f916e2 488b4f38 mov rcx, qword ptr [rdi + 0x38]
0x3f916e6 4885c9 test rcx, rcx
0x3f916e9 7410 je 0x3f916fb
0x3f916eb 488b11 mov rdx, qword ptr [rcx]
0x3f916ee 4c8b02 mov r8, qword ptr [rdx]
0x3f916f1 488bd0 mov rdx, rax
0x3f916f4 41ffd0 call r8
0x3f916f7 48894338 mov qword ptr [rbx + 0x38], rax
0x3f9176a 4584e4 test r12b, r12b
0x3f9176d 740f je 0x3f9177e
0x3f9176f f0ff4364 lock inc dword ptr [rbx + 0x64]
0x3f91773 488bd3 mov rdx, rbx
0x3f91776 498bcf mov rcx, r15
0x3f91779 e8f20e0000 call 0x3f92670
0x3f91cc9 0f1f8000000000 nop dword ptr [rax]
0x3f91cd0 488b0b mov rcx, qword ptr [rbx]
0x3f91cd3 488bd6 mov rdx, rsi
0x3f91cd6 488b4918 mov rcx, qword ptr [rcx + 0x18]
0x3f91cda e811edffff call 0x3f909f0
0x2909460 488b4908 mov rcx, qword ptr [rcx + 8]
0x2909464 e997470000 jmp 0x290dc00
0x2909470 488d0549afe501 lea rax, [rip + 0x1e5af49]
0x2909477 488902 mov qword ptr [rdx], rax
0x290947a 488b4108 mov rax, qword ptr [rcx + 8]
0x290947e 48894208 mov qword ptr [rdx + 8], rax
0x2909482 488bc2 mov rax, rdx
0x2909485 c3 ret 
