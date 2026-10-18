002B2F6F0 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
002B2F6F5 4889742418                         mov      qword ptr [rsp + 0x18], rsi
002B2F6FA 57                                 push     rdi
002B2F6FB 4883ec20                           sub      rsp, 0x20
002B2F6FF 488bf1                             mov      rsi, rcx
002B2F702 b9e0000000                         mov      ecx, 0xe0
002B2F707 e888446f01                         call     0x4223b94
002B2F70C 488bc8                             mov      rcx, rax
002B2F70F 4889442430                         mov      qword ptr [rsp + 0x30], rax
002B2F714 488bf8                             mov      rdi, rax
002B2F717 e854d3bf00                         call     0x372ca70
002B2F71C 488d05eddcc601                     lea      rax, [rip + 0x1c6dced] ; RIP=0x479d410
002B2F723 488d4f40                           lea      rcx, [rdi + 0x40]
002B2F727 488907                             mov      qword ptr [rdi], rax
002B2F72A e8014bedfd                         call     0xa04230
002B2F72F 488b5c2438                         mov      rbx, qword ptr [rsp + 0x38]
002B2F734 488d05d583b201                     lea      rax, [rip + 0x1b283d5] ; RIP=0x4657b10
002B2F73B 48894740                           mov      qword ptr [rdi + 0x40], rax
002B2F73F 488d05a2ffc801                     lea      rax, [rip + 0x1c8ffa2] ; RIP=0x47bf6e8
002B2F746 488907                             mov      qword ptr [rdi], rax
002B2F749 488bc7                             mov      rax, rdi
002B2F74C 8b4e10                             mov      ecx, dword ptr [rsi + 0x10]
002B2F74F 488b742440                         mov      rsi, qword ptr [rsp + 0x40]
002B2F754 894f08                             mov      dword ptr [rdi + 8], ecx
002B2F757 c6470c00                           mov      byte ptr [rdi + 0xc], 0
002B2F75B 4883c420                           add      rsp, 0x20
002B2F75F 5f                                 pop      rdi
002B2F760 c3                                 ret      
