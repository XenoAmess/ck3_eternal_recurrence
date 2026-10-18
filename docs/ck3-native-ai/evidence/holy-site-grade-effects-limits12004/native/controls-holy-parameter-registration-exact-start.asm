000591600 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
000591605 57                                 push     rdi
000591606 4883ec30                           sub      rsp, 0x30
00059160A 488b0dd7d77205                     mov      rcx, qword ptr [rip + 0x572d7d7] ; RIP=0x5cbede8
000591611 488d05a88a2204                     lea      rax, [rip + 0x4228aa8] ; RIP=0x47ba0c0
000591618 4889442420                         mov      qword ptr [rsp + 0x20], rax
00059161D c744242821000000                   mov      dword ptr [rsp + 0x28], 0x21
000591625 c644242c00                         mov      byte ptr [rsp + 0x2c], 0
00059162A 4885c9                             test     rcx, rcx
00059162D 7508                               jne      0x591637
00059162F e8ace19b03                         call     0x3f4f7e0
000591634 488bc8                             mov      rcx, rax
000591637 0f28442420                         movaps   xmm0, xmmword ptr [rsp + 0x20]
00059163C 488d542420                         lea      rdx, [rsp + 0x20]
000591641 660f7f442420                       movdqa   xmmword ptr [rsp + 0x20], xmm0
000591647 e834dc9b03                         call     0x3f4f280
00059164C 8bf8                               mov      edi, eax
00059164E e8ada11903                         call     0x372b800
000591653 488b1d5e8e6d05                     mov      rbx, qword ptr [rip + 0x56d8e5e] ; RIP=0x5c6a4b8
00059165A b918000000                         mov      ecx, 0x18
00059165F e83025c903                         call     0x4223b94
000591664 488d0dc5892204                     lea      rcx, [rip + 0x42289c5] ; RIP=0x47ba030
00059166B 4889442440                         mov      qword ptr [rsp + 0x40], rax
000591670 4c8bc0                             mov      r8, rax
000591673 8bd7                               mov      edx, edi
000591675 48894808                           mov      qword ptr [rax + 8], rcx
000591679 488d0d28a62204                     lea      rcx, [rip + 0x422a628] ; RIP=0x47bbca8
000591680 488908                             mov      qword ptr [rax], rcx
000591683 488bcb                             mov      rcx, rbx
000591686 897810                             mov      dword ptr [rax + 0x10], edi
000591689 488b5c2448                         mov      rbx, qword ptr [rsp + 0x48]
00059168E 4883c430                           add      rsp, 0x30
000591692 5f                                 pop      rdi
000591693 e978a61903                         jmp      0x372bd10
000591698 cc                                 int3     
000591699 cc                                 int3     
00059169A cc                                 int3     
00059169B cc                                 int3     
00059169C cc                                 int3     
00059169D cc                                 int3     
00059169E cc                                 int3     
00059169F cc                                 int3     
