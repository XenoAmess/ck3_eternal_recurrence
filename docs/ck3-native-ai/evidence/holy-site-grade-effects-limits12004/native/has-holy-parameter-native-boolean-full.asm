002B29F00 4156                               push     r14
002B29F02 4157                               push     r15
002B29F04 4883ec28                           sub      rsp, 0x28
002B29F08 4c8bf9                             mov      r15, rcx
002B29F0B e8204c0000                         call     0x2b2eb30
002B29F10 4c8b98e0010000                     mov      r11, qword ptr [rax + 0x1e0]
002B29F17 486380ec010000                     movsxd   rax, dword ptr [rax + 0x1ec]
002B29F1E 4d8d3483                           lea      r14, [r11 + rax*4]
002B29F22 4d3bde                             cmp      r11, r14
002B29F25 0f84db000000                       je       0x2b2a006
002B29F2B 4889742450                         mov      qword ptr [rsp + 0x50], rsi
002B29F30 488b35e93e1f03                     mov      rsi, qword ptr [rip + 0x31f3ee9] ; RIP=0x5d1de20
002B29F37 48897c2420                         mov      qword ptr [rsp + 0x20], rdi
002B29F3C 488b3d3d3f1f03                     mov      rdi, qword ptr [rip + 0x31f3f3d] ; RIP=0x5d1de80
002B29F43 48895c2440                         mov      qword ptr [rsp + 0x40], rbx
002B29F48 48896c2448                         mov      qword ptr [rsp + 0x48], rbp
002B29F4D 0f1f00                             nop      dword ptr [rax]
002B29F50 4885ff                             test     rdi, rdi
002B29F53 7427                               je       0x2b29f7c
002B29F55 418b13                             mov      edx, dword ptr [r11]
002B29F58 8bc2                               mov      eax, edx
002B29F5A 25ffffff00                         and      eax, 0xffffff
002B29F5F 3b472c                             cmp      eax, dword ptr [rdi + 0x2c]
002B29F62 7318                               jae      0x2b29f7c
002B29F64 8bc8                               mov      ecx, eax
002B29F66 488b4720                           mov      rax, qword ptr [rdi + 0x20]
002B29F6A 4803c9                             add      rcx, rcx
002B29F6D 488b4cc808                         mov      rcx, qword ptr [rax + rcx*8 + 8]
002B29F72 4885c9                             test     rcx, rcx
002B29F75 7405                               je       0x2b29f7c
002B29F77 395110                             cmp      dword ptr [rcx + 0x10], edx
002B29F7A 7403                               je       0x2b29f7f
002B29F7C 488bce                             mov      rcx, rsi
002B29F7F 80791800                           cmp      byte ptr [rcx + 0x18], 0
002B29F83 7460                               je       0x2b29fe5
002B29F85 488b4920                           mov      rcx, qword ptr [rcx + 0x20]
002B29F89 418b4740                           mov      eax, dword ptr [r15 + 0x40]
002B29F8D 4c63514c                           movsxd   r10, dword ptr [rcx + 0x4c]
002B29F91 488b5940                           mov      rbx, qword ptr [rcx + 0x40]
002B29F95 4c8bcb                             mov      r9, rbx
002B29F98 488bcb                             mov      rcx, rbx
002B29F9B 4a8d2c93                           lea      rbp, [rbx + r10*4]
002B29F9F 4d85d2                             test     r10, r10
002B29FA2 7e2c                               jle      0x2b29fd0
002B29FA4 0f1f4000                           nop      dword ptr [rax]
002B29FA8 0f1f840000000000                   nop      dword ptr [rax + rax]
002B29FB0 4d8bc2                             mov      r8, r10
002B29FB3 49d1e8                             shr      r8, 1
002B29FB6 4d2bd0                             sub      r10, r8
002B29FB9 43390481                           cmp      dword ptr [r9 + r8*4], eax
002B29FBD 4b8d1491                           lea      rdx, [r9 + r10*4]
002B29FC1 4d8bd0                             mov      r10, r8
002B29FC4 4c0f4cca                           cmovl    r9, rdx
002B29FC8 498bc9                             mov      rcx, r9
002B29FCB 4d85c0                             test     r8, r8
002B29FCE 75e0                               jne      0x2b29fb0
002B29FD0 483bcd                             cmp      rcx, rbp
002B29FD3 7410                               je       0x2b29fe5
002B29FD5 3b01                               cmp      eax, dword ptr [rcx]
002B29FD7 7c0c                               jl       0x2b29fe5
002B29FD9 482bcb                             sub      rcx, rbx
002B29FDC 48c1f902                           sar      rcx, 2
002B29FE0 83f9ff                             cmp      ecx, -1
002B29FE3 750d                               jne      0x2b29ff2
002B29FE5 4983c304                           add      r11, 4
002B29FE9 4d3bde                             cmp      r11, r14
002B29FEC 0f855effffff                       jne      0x2b29f50
002B29FF2 488b6c2448                         mov      rbp, qword ptr [rsp + 0x48]
002B29FF7 488b5c2440                         mov      rbx, qword ptr [rsp + 0x40]
002B29FFC 488b742450                         mov      rsi, qword ptr [rsp + 0x50]
002B2A001 488b7c2420                         mov      rdi, qword ptr [rsp + 0x20]
002B2A006 33c0                               xor      eax, eax
002B2A008 4d3bde                             cmp      r11, r14
002B2A00B 4c0f44d8                           cmove    r11, rax
002B2A00F 4d85db                             test     r11, r11
002B2A012 0f95c0                             setne    al
002B2A015 4883c428                           add      rsp, 0x28
002B2A019 415f                               pop      r15
002B2A01B 415e                               pop      r14
002B2A01D c3                                 ret      
002B2A01E cc                                 int3     
002B2A01F cc                                 int3     
