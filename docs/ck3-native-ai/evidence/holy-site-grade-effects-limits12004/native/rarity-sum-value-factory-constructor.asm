002B0DE50 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
002B0DE55 57                                 push     rdi
002B0DE56 4883ec20                           sub      rsp, 0x20
002B0DE5A 488bf9                             mov      rdi, rcx
002B0DE5D b930010000                         mov      ecx, 0x130
002B0DE62 e82d5d7101                         call     0x4223b94
002B0DE67 488bc8                             mov      rcx, rax
002B0DE6A 4889442430                         mov      qword ptr [rsp + 0x30], rax
002B0DE6F 488bd8                             mov      rbx, rax
002B0DE72 e8f9ebc100                         call     0x372ca70
002B0DE77 488d05b2939901                     lea      rax, [rip + 0x19993b2] ; RIP=0x44a7230
002B0DE7E 488903                             mov      qword ptr [rbx], rax
002B0DE81 488d4b48                           lea      rcx, [rbx + 0x48]
002B0DE85 c7434065010000                     mov      dword ptr [rbx + 0x40], 0x165
002B0DE8C e8cf9deffd                         call     0xa07c60
002B0DE91 488d05984cc901                     lea      rax, [rip + 0x1c94c98] ; RIP=0x47a2b30
002B0DE98 488903                             mov      qword ptr [rbx], rax
002B0DE9B 488bc3                             mov      rax, rbx
002B0DE9E 8b4f10                             mov      ecx, dword ptr [rdi + 0x10]
002B0DEA1 894b08                             mov      dword ptr [rbx + 8], ecx
002B0DEA4 c6430c00                           mov      byte ptr [rbx + 0xc], 0
002B0DEA8 488b5c2438                         mov      rbx, qword ptr [rsp + 0x38]
002B0DEAD 4883c420                           add      rsp, 0x20
002B0DEB1 5f                                 pop      rdi
002B0DEB2 c3                                 ret      
