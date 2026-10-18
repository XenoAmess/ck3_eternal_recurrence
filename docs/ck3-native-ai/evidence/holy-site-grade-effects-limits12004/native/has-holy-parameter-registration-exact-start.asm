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
