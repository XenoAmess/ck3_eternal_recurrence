002B0C740 488b02                             mov      rax, qword ptr [rdx]
002B0C743 66833817                           cmp      word ptr [rax], 0x17
002B0C747 7506                               jne      0x2b0c74f
002B0C749 448b4008                           mov      r8d, dword ptr [rax + 8]
002B0C74D eb06                               jmp      0x2b0c755
002B0C74F 41b8ffffffff                       mov      r8d, 0xffffffff
002B0C755 488b0524172103                     mov      rax, qword ptr [rip + 0x3211724] ; RIP=0x5d1de80
002B0C75C 4885c0                             test     rax, rax
002B0C75F 750b                               jne      0x2b0c76c
002B0C761 488b05b8162103                     mov      rax, qword ptr [rip + 0x32116b8] ; RIP=0x5d1de20
002B0C768 8b401c                             mov      eax, dword ptr [rax + 0x1c]
002B0C76B c3                                 ret      
002B0C76C 418bc8                             mov      ecx, r8d
002B0C76F 81e1ffffff00                       and      ecx, 0xffffff
002B0C775 3b482c                             cmp      ecx, dword ptr [rax + 0x2c]
002B0C778 7317                               jae      0x2b0c791
002B0C77A 488b4020                           mov      rax, qword ptr [rax + 0x20]
002B0C77E 4803c9                             add      rcx, rcx
002B0C781 488b54c808                         mov      rdx, qword ptr [rax + rcx*8 + 8]
002B0C786 4885d2                             test     rdx, rdx
002B0C789 7406                               je       0x2b0c791
002B0C78B 44394210                           cmp      dword ptr [rdx + 0x10], r8d
002B0C78F 7407                               je       0x2b0c798
002B0C791 488b1588162103                     mov      rdx, qword ptr [rip + 0x3211688] ; RIP=0x5d1de20
002B0C798 8b421c                             mov      eax, dword ptr [rdx + 0x1c]
002B0C79B c3                                 ret      
002B0C79C cc                                 int3     
002B0C79D cc                                 int3     
002B0C79E cc                                 int3     
002B0C79F cc                                 int3     
002B0C7A0 4883ec28                           sub      rsp, 0x28
002B0C7A4 488b02                             mov      rax, qword ptr [rdx]
002B0C7A7 4c8bc1                             mov      r8, rcx
002B0C7AA 66833817                           cmp      word ptr [rax], 0x17
002B0C7AE 7505                               jne      0x2b0c7b5
002B0C7B0 8b5008                             mov      edx, dword ptr [rax + 8]
002B0C7B3 eb05                               jmp      0x2b0c7ba
002B0C7B5 baffffffff                         mov      edx, 0xffffffff
002B0C7BA 488b05bf162103                     mov      rax, qword ptr [rip + 0x32116bf] ; RIP=0x5d1de80
002B0C7C1 4885c0                             test     rax, rax
002B0C7C4 7423                               je       0x2b0c7e9
002B0C7C6 8bca                               mov      ecx, edx
002B0C7C8 81e1ffffff00                       and      ecx, 0xffffff
