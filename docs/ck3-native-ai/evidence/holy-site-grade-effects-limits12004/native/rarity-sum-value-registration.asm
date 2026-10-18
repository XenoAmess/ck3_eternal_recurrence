000588B50 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
000588B55 57                                 push     rdi
000588B56 4883ec30                           sub      rsp, 0x30
000588B5A 488b0d87627305                     mov      rcx, qword ptr [rip + 0x5736287] ; RIP=0x5cbede8
000588B61 488d0500942104                     lea      rax, [rip + 0x4219400] ; RIP=0x47a1f68
000588B68 4889442420                         mov      qword ptr [rsp + 0x20], rax
000588B6D c744242820000000                   mov      dword ptr [rsp + 0x28], 0x20
000588B75 c644242c00                         mov      byte ptr [rsp + 0x2c], 0
000588B7A 4885c9                             test     rcx, rcx
000588B7D 7508                               jne      0x588b87
000588B7F e85c6c9c03                         call     0x3f4f7e0
000588B84 488bc8                             mov      rcx, rax
000588B87 0f28442420                         movaps   xmm0, xmmword ptr [rsp + 0x20]
000588B8C 488d542420                         lea      rdx, [rsp + 0x20]
000588B91 660f7f442420                       movdqa   xmmword ptr [rsp + 0x20], xmm0
000588B97 e8e4669c03                         call     0x3f4f280
000588B9C 8bf8                               mov      edi, eax
000588B9E e85d2c1a03                         call     0x372b800
000588BA3 488b1d0e196e05                     mov      rbx, qword ptr [rip + 0x56e190e] ; RIP=0x5c6a4b8
000588BAA b918000000                         mov      ecx, 0x18
000588BAF e8e0afc903                         call     0x4223b94
000588BB4 488d0dd5932104                     lea      rcx, [rip + 0x42193d5] ; RIP=0x47a1f90
000588BBB 4889442440                         mov      qword ptr [rsp + 0x40], rax
000588BC0 4c8bc0                             mov      r8, rax
000588BC3 8bd7                               mov      edx, edi
000588BC5 48894808                           mov      qword ptr [rax + 8], rcx
000588BC9 488d0d50a22104                     lea      rcx, [rip + 0x421a250] ; RIP=0x47a2e20
000588BD0 488908                             mov      qword ptr [rax], rcx
000588BD3 488bcb                             mov      rcx, rbx
000588BD6 897810                             mov      dword ptr [rax + 0x10], edi
000588BD9 488b5c2448                         mov      rbx, qword ptr [rsp + 0x48]
000588BDE 4883c430                           add      rsp, 0x30
000588BE2 5f                                 pop      rdi
000588BE3 e928311a03                         jmp      0x372bd10
