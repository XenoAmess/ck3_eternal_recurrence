002B0D600 e94b080000                         jmp      0x2b0de50
002B0D605 cc                                 int3     
002B0D606 cc                                 int3     
002B0D607 cc                                 int3     
002B0D608 cc                                 int3     
002B0D609 cc                                 int3     
002B0D60A cc                                 int3     
002B0D60B cc                                 int3     
002B0D60C cc                                 int3     
002B0D60D cc                                 int3     
002B0D60E cc                                 int3     
002B0D60F cc                                 int3     
002B0D610 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
002B0D615 57                                 push     rdi
002B0D616 4883ec20                           sub      rsp, 0x20
002B0D61A 488bf9                             mov      rdi, rcx
002B0D61D b968000000                         mov      ecx, 0x68
002B0D622 e86d657101                         call     0x4223b94
002B0D627 488bc8                             mov      rcx, rax
002B0D62A 4889442430                         mov      qword ptr [rsp + 0x30], rax
002B0D62F 488bd8                             mov      rbx, rax
002B0D632 e839f4c100                         call     0x372ca70
002B0D637 488d050256c901                     lea      rax, [rip + 0x1c95602] ; RIP=0x47a2c40
002B0D63E 488903                             mov      qword ptr [rbx], rax
002B0D641 33c0                               xor      eax, eax
002B0D643 48894340                           mov      qword ptr [rbx + 0x40], rax
002B0D647 884340                             mov      byte ptr [rbx + 0x40], al
002B0D64A 48894350                           mov      qword ptr [rbx + 0x50], rax
002B0D64E 488d05cb56c901                     lea      rax, [rip + 0x1c956cb] ; RIP=0x47a2d20
002B0D655 48c743580f000000                   mov      qword ptr [rbx + 0x58], 0xf
