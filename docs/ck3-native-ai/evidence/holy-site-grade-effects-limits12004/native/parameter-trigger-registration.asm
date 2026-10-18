000591520 7026                               jo       0x591548
000591522 c9                                 leave    
000591523 03488d                             add      ecx, dword ptr [rax - 0x73]
000591526 0dd58b2204                         or       eax, 0x4228bd5
00059152B 4889442440                         mov      qword ptr [rsp + 0x40], rax
000591530 4c8bc0                             mov      r8, rax
000591533 8bd7                               mov      edx, edi
000591535 48894808                           mov      qword ptr [rax + 8], rcx
000591539 488d0d28a72204                     lea      rcx, [rip + 0x422a728] ; RIP=0x47bbc68
000591540 488908                             mov      qword ptr [rax], rcx
000591543 488bcb                             mov      rcx, rbx
000591546 897810                             mov      dword ptr [rax + 0x10], edi
000591549 488b5c2448                         mov      rbx, qword ptr [rsp + 0x48]
00059154E 4883c430                           add      rsp, 0x30
000591552 5f                                 pop      rdi
000591553 e9b8a71903                         jmp      0x372bd10
000591558 cc                                 int3     
000591559 cc                                 int3     
00059155A cc                                 int3     
00059155B cc                                 int3     
00059155C cc                                 int3     
00059155D cc                                 int3     
00059155E cc                                 int3     
00059155F cc                                 int3     
000591560 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
000591565 57                                 push     rdi
000591566 4883ec30                           sub      rsp, 0x30
00059156A 488b0d77d87205                     mov      rcx, qword ptr [rip + 0x572d877] ; RIP=0x5cbede8
000591571 488d05a08a2204                     lea      rax, [rip + 0x4228aa0] ; RIP=0x47ba018
000591578 4889442420                         mov      qword ptr [rsp + 0x20], rax
00059157D c744242817000000                   mov      dword ptr [rsp + 0x28], 0x17
000591585 c644242c00                         mov      byte ptr [rsp + 0x2c], 0
00059158A 4885c9                             test     rcx, rcx
00059158D 7508                               jne      0x591597
00059158F e84ce29b03                         call     0x3f4f7e0
000591594 488bc8                             mov      rcx, rax
000591597 0f28442420                         movaps   xmm0, xmmword ptr [rsp + 0x20]
00059159C 488d542420                         lea      rdx, [rsp + 0x20]
0005915A1 660f7f442420                       movdqa   xmmword ptr [rsp + 0x20], xmm0
0005915A7 e8d4dc9b03                         call     0x3f4f280
0005915AC 8bf8                               mov      edi, eax
0005915AE e84da21903                         call     0x372b800
0005915B3 488b1dfe8e6d05                     mov      rbx, qword ptr [rip + 0x56d8efe] ; RIP=0x5c6a4b8
0005915BA b918000000                         mov      ecx, 0x18
0005915BF e8d025c903                         call     0x4223b94
0005915C4 488d0dd5892204                     lea      rcx, [rip + 0x42289d5] ; RIP=0x47b9fa0
0005915CB 4889442440                         mov      qword ptr [rsp + 0x40], rax
0005915D0 4c8bc0                             mov      r8, rax
0005915D3 8bd7                               mov      edx, edi
0005915D5 48894808                           mov      qword ptr [rax + 8], rcx
0005915D9 488d0da8a62204                     lea      rcx, [rip + 0x422a6a8] ; RIP=0x47bbc88
0005915E0 488908                             mov      qword ptr [rax], rcx
0005915E3 488bcb                             mov      rcx, rbx
0005915E6 897810                             mov      dword ptr [rax + 0x10], edi
0005915E9 488b5c2448                         mov      rbx, qword ptr [rsp + 0x48]
0005915EE 4883c430                           add      rsp, 0x30
0005915F2 5f                                 pop      rdi
0005915F3 e918a71903                         jmp      0x372bd10
0005915F8 cc                                 int3     
0005915F9 cc                                 int3     
0005915FA cc                                 int3     
0005915FB cc                                 int3     
0005915FC cc                                 int3     
0005915FD cc                                 int3     
0005915FE cc                                 int3     
0005915FF cc                                 int3     
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
0005916A0 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
0005916A5 57                                 push     rdi
0005916A6 4883ec30                           sub      rsp, 0x30
0005916AA 488b0d37d77205                     mov      rcx, qword ptr [rip + 0x572d737] ; RIP=0x5cbede8
0005916B1 488d05b8662204                     lea      rax, [rip + 0x42266b8] ; RIP=0x47b7d70
0005916B8 4889442420                         mov      qword ptr [rsp + 0x20], rax
