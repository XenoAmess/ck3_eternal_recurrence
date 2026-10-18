0005914C0 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
0005914C5 57                                 push     rdi
0005914C6 4883ec30                           sub      rsp, 0x30
0005914CA 488b0d17d97205                     mov      rcx, qword ptr [rip + 0x572d917] ; RIP=0x5cbede8
0005914D1 488d05788c2204                     lea      rax, [rip + 0x4228c78] ; RIP=0x47ba150
0005914D8 4889442420                         mov      qword ptr [rsp + 0x20], rax
0005914DD c74424280f000000                   mov      dword ptr [rsp + 0x28], 0xf
0005914E5 c644242c00                         mov      byte ptr [rsp + 0x2c], 0
0005914EA 4885c9                             test     rcx, rcx
0005914ED 7508                               jne      0x5914f7
0005914EF e8ece29b03                         call     0x3f4f7e0
0005914F4 488bc8                             mov      rcx, rax
0005914F7 0f28442420                         movaps   xmm0, xmmword ptr [rsp + 0x20]
0005914FC 488d542420                         lea      rdx, [rsp + 0x20]
000591501 660f7f442420                       movdqa   xmmword ptr [rsp + 0x20], xmm0
000591507 e874dd9b03                         call     0x3f4f280
00059150C 8bf8                               mov      edi, eax
00059150E e8eda21903                         call     0x372b800
000591513 488b1d9e8f6d05                     mov      rbx, qword ptr [rip + 0x56d8f9e] ; RIP=0x5c6a4b8
00059151A b918000000                         mov      ecx, 0x18
00059151F e87026c903                         call     0x4223b94
000591524 488d0dd58b2204                     lea      rcx, [rip + 0x4228bd5] ; RIP=0x47ba100
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
