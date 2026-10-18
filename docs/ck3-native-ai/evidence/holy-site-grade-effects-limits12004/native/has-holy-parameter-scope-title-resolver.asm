002B2EB30 4053                               push     rbx
002B2EB32 4881ec40020000                     sub      rsp, 0x240
002B2EB39 488b02                             mov      rax, qword ptr [rdx]
002B2EB3C 4c8bd2                             mov      r10, rdx
002B2EB3F 488bd9                             mov      rbx, rcx
002B2EB42 66833805                           cmp      word ptr [rax], 5
002B2EB46 7506                               jne      0x2b2eb4e
002B2EB48 448b4808                           mov      r9d, dword ptr [rax + 8]
002B2EB4C eb06                               jmp      0x2b2eb54
002B2EB4E 41b9ffffffff                       mov      r9d, 0xffffffff
002B2EB54 4c8b059def1e03                     mov      r8, qword ptr [rip + 0x31eef9d] ; RIP=0x5d1daf8
002B2EB5B 488b157eef1e03                     mov      rdx, qword ptr [rip + 0x31eef7e] ; RIP=0x5d1dae0
002B2EB62 4d85c0                             test     r8, r8
002B2EB65 7427                               je       0x2b2eb8e
002B2EB67 418bc1                             mov      eax, r9d
002B2EB6A 25ffffff00                         and      eax, 0xffffff
002B2EB6F 413b402c                           cmp      eax, dword ptr [r8 + 0x2c]
002B2EB73 7319                               jae      0x2b2eb8e
002B2EB75 8bc8                               mov      ecx, eax
002B2EB77 498b4020                           mov      rax, qword ptr [r8 + 0x20]
002B2EB7B 4803c9                             add      rcx, rcx
002B2EB7E 488b4cc808                         mov      rcx, qword ptr [rax + rcx*8 + 8]
002B2EB83 4885c9                             test     rcx, rcx
002B2EB86 7406                               je       0x2b2eb8e
002B2EB88 44394910                           cmp      dword ptr [rcx + 0x10], r9d
002B2EB8C 7403                               je       0x2b2eb91
002B2EB8E 488bca                             mov      rcx, rdx
002B2EB91 817914646e614c                     cmp      dword ptr [rcx + 0x14], 0x4c616e64
002B2EB98 0f8532010000                       jne      0x2b2ecd0
002B2EB9E 837910ff                           cmp      dword ptr [rcx + 0x10], -1
002B2EBA2 0f8428010000                       je       0x2b2ecd0
002B2EBA8 488b4148                           mov      rax, qword ptr [rcx + 0x48]
002B2EBAC 4c634864                           movsxd   r9, dword ptr [rax + 0x64]
002B2EBB0 4183f901                           cmp      r9d, 1
002B2EBB4 0f84c4000000                       je       0x2b2ec7e
002B2EBBA 41807a2000                         cmp      byte ptr [r10 + 0x20], 0
002B2EBBF 0f858c010000                       jne      0x2b2ed51
002B2EBC5 4183f907                           cmp      r9d, 7
002B2EBC9 773e                               ja       0x2b2ec09
002B2EBCB 488d152e144dfd                     lea      rdx, [rip - 0x2b2ebd2] ; RIP=0x0
002B2EBD2 428b8c8a60edb202                   mov      ecx, dword ptr [rdx + r9*4 + 0x2b2ed60]
002B2EBDA 4803ca                             add      rcx, rdx
002B2EBDD ffe1                               jmp      rcx
002B2EBDF b907280000                         mov      ecx, 0x2807
002B2EBE4 eb28                               jmp      0x2b2ec0e
002B2EBE6 b9e2270000                         mov      ecx, 0x27e2
002B2EBEB eb21                               jmp      0x2b2ec0e
002B2EBED b9e3270000                         mov      ecx, 0x27e3
002B2EBF2 eb1a                               jmp      0x2b2ec0e
002B2EBF4 b9e4270000                         mov      ecx, 0x27e4
002B2EBF9 eb13                               jmp      0x2b2ec0e
002B2EBFB b9e5270000                         mov      ecx, 0x27e5
002B2EC00 eb0c                               jmp      0x2b2ec0e
002B2EC02 b9f8380000                         mov      ecx, 0x38f8
002B2EC07 eb05                               jmp      0x2b2ec0e
002B2EC09 b965010000                         mov      ecx, 0x165
002B2EC0E e8cd0c4201                         call     0x3f4f8e0
002B2EC13 c784243002000000000000             mov      dword ptr [rsp + 0x230], 0
002B2EC1E 4883781810                         cmp      qword ptr [rax + 0x18], 0x10
002B2EC23 7203                               jb       0x2b2ec28
002B2EC25 488b00                             mov      rax, qword ptr [rax]
002B2EC28 4c8bc8                             mov      r9, rax
002B2EC2B 4c8d05eea7c801                     lea      r8, [rip + 0x1c8a7ee] ; RIP=0x47b9420
002B2EC32 ba00020000                         mov      edx, 0x200
002B2EC37 488d4c2430                         lea      rcx, [rsp + 0x30]
002B2EC3C e87fdcd4fd                         call     0x87c8c0
002B2EC41 b9ff010000                         mov      ecx, 0x1ff
002B2EC46 3bc1                               cmp      eax, ecx
002B2EC48 0f4fc1                             cmovg    eax, ecx
002B2EC4B 488d4c2430                         lea      rcx, [rsp + 0x30]
002B2EC50 89842430020000                     mov      dword ptr [rsp + 0x230], eax
002B2EC57 488d442430                         lea      rax, [rsp + 0x30]
002B2EC5C 4889442420                         mov      qword ptr [rsp + 0x20], rax
002B2EC61 48c7c0ffffffff                     mov      rax, 0xffffffffffffffff
002B2EC68 0f1f840000000000                   nop      dword ptr [rax + rax]
002B2EC70 48ffc0                             inc      rax
002B2EC73 803c0100                           cmp      byte ptr [rcx + rax], 0
002B2EC77 75f7                               jne      0x2b2ec70
002B2EC79 e9ab000000                         jmp      0x2b2ed29
002B2EC7E 4d85c0                             test     r8, r8
002B2EC81 0f84ca000000                       je       0x2b2ed51
002B2EC87 448b8908010000                     mov      r9d, dword ptr [rcx + 0x108]
002B2EC8E 418bc1                             mov      eax, r9d
002B2EC91 25ffffff00                         and      eax, 0xffffff
002B2EC96 413b402c                           cmp      eax, dword ptr [r8 + 0x2c]
002B2EC9A 0f83b1000000                       jae      0x2b2ed51
002B2ECA0 8bc8                               mov      ecx, eax
002B2ECA2 498b4020                           mov      rax, qword ptr [r8 + 0x20]
002B2ECA6 4803c9                             add      rcx, rcx
002B2ECA9 4c8b44c808                         mov      r8, qword ptr [rax + rcx*8 + 8]
002B2ECAE 4d85c0                             test     r8, r8
002B2ECB1 0f849a000000                       je       0x2b2ed51
002B2ECB7 45394810                           cmp      dword ptr [r8 + 0x10], r9d
002B2ECBB 0f8590000000                       jne      0x2b2ed51
002B2ECC1 498bd0                             mov      rdx, r8
002B2ECC4 488bc2                             mov      rax, rdx
002B2ECC7 4881c440020000                     add      rsp, 0x240
002B2ECCE 5b                                 pop      rbx
002B2ECCF c3                                 ret      
002B2ECD0 41807a2000                         cmp      byte ptr [r10 + 0x20], 0
002B2ECD5 757a                               jne      0x2b2ed51
002B2ECD7 4c8d0582abc801                     lea      r8, [rip + 0x1c8ab82] ; RIP=0x47b9860
002B2ECDE c784243002000000000000             mov      dword ptr [rsp + 0x230], 0
002B2ECE9 ba00020000                         mov      edx, 0x200
002B2ECEE 488d4c2430                         lea      rcx, [rsp + 0x30]
002B2ECF3 e8c8dbd4fd                         call     0x87c8c0
002B2ECF8 b9ff010000                         mov      ecx, 0x1ff
002B2ECFD 3bc1                               cmp      eax, ecx
002B2ECFF 0f4fc1                             cmovg    eax, ecx
002B2ED02 488d4c2430                         lea      rcx, [rsp + 0x30]
002B2ED07 89842430020000                     mov      dword ptr [rsp + 0x230], eax
002B2ED0E 488d442430                         lea      rax, [rsp + 0x30]
002B2ED13 4889442420                         mov      qword ptr [rsp + 0x20], rax
002B2ED18 48c7c0ffffffff                     mov      rax, 0xffffffffffffffff
002B2ED1F 90                                 nop      
002B2ED20 48ffc0                             inc      rax
002B2ED23 803c0100                           cmp      byte ptr [rcx + rax], 0
002B2ED27 75f7                               jne      0x2b2ed20
002B2ED29 89442428                           mov      dword ptr [rsp + 0x28], eax
002B2ED2D 488d542420                         lea      rdx, [rsp + 0x20]
002B2ED32 c644242c00                         mov      byte ptr [rsp + 0x2c], 0
002B2ED37 488bcb                             mov      rcx, rbx
002B2ED3A 0f28442420                         movaps   xmm0, xmmword ptr [rsp + 0x20]
002B2ED3F 660f7f442420                       movdqa   xmmword ptr [rsp + 0x20], xmm0
002B2ED45 e8e61fbe00                         call     0x3710d30
002B2ED4A 488b158fed1e03                     mov      rdx, qword ptr [rip + 0x31eed8f] ; RIP=0x5d1dae0
002B2ED51 488bc2                             mov      rax, rdx
002B2ED54 4881c440020000                     add      rsp, 0x240
002B2ED5B 5b                                 pop      rbx
002B2ED5C c3                                 ret      
002B2ED5D 0f1f00                             nop      dword ptr [rax]
002B2ED60 09ec                               or       esp, ebp
002B2ED62 b202                               mov      dl, 2
002B2ED64 dfeb                               fucompi  st(3)
002B2ED66 b202                               mov      dl, 2
002B2ED68 e6eb                               out      0xeb, al
002B2ED6A b202                               mov      dl, 2
002B2ED6C ed                                 in       eax, dx
002B2ED6D ebb2                               jmp      0x2b2ed21
002B2ED6F 02f4                               add      dh, ah
002B2ED71 ebb2                               jmp      0x2b2ed25
002B2ED73 02fb                               add      bh, bl
002B2ED75 ebb2                               jmp      0x2b2ed29
002B2ED77 0202                               add      al, byte ptr [rdx]
002B2ED79 ec                                 in       al, dx
002B2ED7A b202                               mov      dl, 2
002B2ED7C 09ec                               or       esp, ebp
002B2ED7E b202                               mov      dl, 2
