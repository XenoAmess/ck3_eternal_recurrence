0x28f43a5 6bc21e imul eax, edx, 0x1e
0x28f43a8 442bc0 sub r8d, eax
0x28f43ab b889888888 mov eax, 0x88888889
0x28f43b0 f7e1 mul ecx
0x28f43b2 c1ea04 shr edx, 4
0x28f43b5 6bc21e imul eax, edx, 0x1e
0x28f43b8 2bc8 sub ecx, eax
0x28f43ba 413bc8 cmp ecx, r8d
0x28f43bd 7520 jne 0x28f43df
0x28f43bf 488b0b mov rcx, qword ptr [rbx]
0x28f43c2 488d542430 lea rdx, [rsp + 0x30]
0x28f43c7 4881c1f8250000 add rcx, 0x25f8
0x28f43ce 4c894c2430 mov qword ptr [rsp + 0x30], r9
0x28f43d3 e868bff8fd call 0x880340
0x28f43d8 4c8b5310 mov r10, qword ptr [rbx + 0x10]
0x28f43dc 4d8b0a mov r9, qword ptr [r10]
0x28f49cb 418b0c24 mov ecx, dword ptr [r12]
0x28f49cf b8abaaaa2a mov eax, 0x2aaaaaab
0x28f49d4 81e9c0559c02 sub ecx, 0x29c55c0
0x28f49da 48897dd0 mov qword ptr [rbp - 0x30], rdi
0x28f49de f7e9 imul ecx
0x28f49e0 488975e0 mov qword ptr [rbp - 0x20], rsi
0x28f49e4 448bc2 mov r8d, edx
0x28f49e7 48897de8 mov qword ptr [rbp - 0x18], rdi
0x28f49eb 41c1f802 sar r8d, 2
0x28f49ef 418bc0 mov eax, r8d
0x28f49f2 c1e81f shr eax, 0x1f
0x28f49f5 4403c0 add r8d, eax
0x28f514f 0fb681b84c0000 movzx eax, byte ptr [rcx + 0x4cb8]
0x28f5156 488bd9 mov rbx, rcx
0x28f5159 fec8 dec al
0x28f515b 4883c138 add rcx, 0x38
0x28f515f 83e001 and eax, 1
0x28f5162 4c8bca mov r9, rdx
0x28f5165 4869c040260000 imul rax, rax, 0x2640
0x28f516c 4803c8 add rcx, rax
0x28f516f e80ceeffff call 0x28f3f80
0x28f5174 488d7b20 lea rdi, [rbx + 0x20]
0x28f5178 4d8bc1 mov r8, r9
0x28f517b 488bd7 mov rdx, rdi
0x28f517e e83df7ffff call 0x28f48c0
0x28f5409 488b0540383703 mov rax, qword ptr [rip + 0x3373840]
0x28f5410 48894518 mov qword ptr [rbp + 0x18], rax
0x28f5414 488b4808 mov rcx, qword ptr [rax + 8]
0x28f5418 48894c2430 mov qword ptr [rsp + 0x30], rcx
0x28f541d 8d4118 lea eax, [rcx + 0x18]
0x28f5420 89442430 mov dword ptr [rsp + 0x30], eax
0x28f54ae 4d8d65f8 lea r12, [r13 - 8]
0x28f56f0 488d542430 lea rdx, [rsp + 0x30]
0x28f56f5 498bcc mov rcx, r12
0x28f56f8 e843faffff call 0x28f5140
0x28f56fd 410fb68424b84c0000 movzx eax, byte ptr [r12 + 0x4cb8]
0x28f5706 fec8 dec al
0x28f5708 83e001 and eax, 1
0x28f570b 4869f840260000 imul rdi, rax, 0x2640
0x28f8831 4c8d4567 lea r8, [rbp + 0x67]
0x28f8835 488bd7 mov rdx, rdi
0x28f8838 488bcb mov rcx, rbx
0x28f883b e860e2ffff call 0x28f6aa0
