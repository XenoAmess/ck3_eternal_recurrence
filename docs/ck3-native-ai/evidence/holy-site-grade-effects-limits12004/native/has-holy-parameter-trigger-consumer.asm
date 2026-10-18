002B2F770 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
002B2F775 57                                 push     rdi
002B2F776 4883ec20                           sub      rsp, 0x20
002B2F77A 488bf9                             mov      rdi, rcx
002B2F77D b948000000                         mov      ecx, 0x48
002B2F782 e80d446f01                         call     0x4223b94
002B2F787 488bc8                             mov      rcx, rax
002B2F78A 4889442430                         mov      qword ptr [rsp + 0x30], rax
002B2F78F 488bd8                             mov      rbx, rax
002B2F792 e8d9d2bf00                         call     0x372ca70
002B2F797 c7434000000000                     mov      dword ptr [rbx + 0x40], 0
002B2F79E 488d0513b0c801                     lea      rax, [rip + 0x1c8b013] ; RIP=0x47ba7b8
002B2F7A5 488903                             mov      qword ptr [rbx], rax
002B2F7A8 488bc3                             mov      rax, rbx
002B2F7AB 8b4f10                             mov      ecx, dword ptr [rdi + 0x10]
002B2F7AE 894b08                             mov      dword ptr [rbx + 8], ecx
002B2F7B1 c6430c00                           mov      byte ptr [rbx + 0xc], 0
002B2F7B5 488b5c2438                         mov      rbx, qword ptr [rsp + 0x38]
002B2F7BA 4883c420                           add      rsp, 0x20
002B2F7BE 5f                                 pop      rdi
002B2F7BF c3                                 ret      
