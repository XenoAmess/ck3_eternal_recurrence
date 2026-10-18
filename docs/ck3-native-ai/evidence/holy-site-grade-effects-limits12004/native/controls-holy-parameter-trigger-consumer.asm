002B2F7C0 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
002B2F7C5 57                                 push     rdi
002B2F7C6 4883ec20                           sub      rsp, 0x20
002B2F7CA 488bf9                             mov      rdi, rcx
002B2F7CD b948000000                         mov      ecx, 0x48
002B2F7D2 e8bd436f01                         call     0x4223b94
002B2F7D7 488bc8                             mov      rcx, rax
002B2F7DA 4889442430                         mov      qword ptr [rsp + 0x30], rax
002B2F7DF 488bd8                             mov      rbx, rax
002B2F7E2 e889d2bf00                         call     0x372ca70
002B2F7E7 c7434000000000                     mov      dword ptr [rbx + 0x40], 0
002B2F7EE 488d05b3bdc801                     lea      rax, [rip + 0x1c8bdb3] ; RIP=0x47bb5a8
002B2F7F5 488903                             mov      qword ptr [rbx], rax
002B2F7F8 488bc3                             mov      rax, rbx
002B2F7FB 8b4f10                             mov      ecx, dword ptr [rdi + 0x10]
002B2F7FE 894b08                             mov      dword ptr [rbx + 8], ecx
002B2F801 c6430c00                           mov      byte ptr [rbx + 0xc], 0
002B2F805 488b5c2438                         mov      rbx, qword ptr [rsp + 0x38]
002B2F80A 4883c420                           add      rsp, 0x20
002B2F80E 5f                                 pop      rdi
002B2F80F c3                                 ret      
