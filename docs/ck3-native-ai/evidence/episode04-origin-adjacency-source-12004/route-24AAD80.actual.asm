024AAD80 4c89442418               mov      qword ptr [rsp + 0x18], r8
024AAD85 4889542410               mov      qword ptr [rsp + 0x10], rdx
024AAD8A 55                       push     rbp
024AAD8B 57                       push     rdi
024AAD8C 4154                     push     r12
024AAD8E 4155                     push     r13
024AAD90 4883ec68                 sub      rsp, 0x68
024AAD94 4183780c00               cmp      dword ptr [r8 + 0xc], 0
024AAD99 498be9                   mov      rbp, r9
024AAD9C 498bf8                   mov      rdi, r8
024AAD9F 4c8be2                   mov      r12, rdx
024AADA2 4c8be9                   mov      r13, rcx
024AADA5 7515                     jne      0x24aadbc
024AADA7 48c70200000000           mov      qword ptr [rdx], 0
024AADAE 488bc2                   mov      rax, rdx
024AADB1 4883c468                 add      rsp, 0x68
024AADB5 415d                     pop      r13
024AADB7 415c                     pop      r12
024AADB9 5f                       pop      rdi
024AADBA 5d                       pop      rbp
024AADBB c3                       ret      
024AADBC 48899c2490000000         mov      qword ptr [rsp + 0x90], rbx
024AADC4 488d542438               lea      rdx, [rsp + 0x38]
024AADC9 4889742460               mov      qword ptr [rsp + 0x60], rsi
024AADCE 4c897c2450               mov      qword ptr [rsp + 0x50], r15
024AADD3 e848fbffff               call     0x24aa920
024AADD8 488d542430               lea      rdx, [rsp + 0x30]
024AADDD 498bcd                   mov      rcx, r13
024AADE0 e8fbfdffff               call     0x24aabe0
024AADE5 488b4508                 mov      rax, qword ptr [rbp + 8]
024AADE9 33db                     xor      ebx, ebx
024AADEB 488b37                   mov      rsi, qword ptr [rdi]
024AADEE 4533ff                   xor      r15d, r15d
024AADF1 4c8b90b0000000           mov      r10, qword ptr [rax + 0xb0]
024AADF8 4863470c                 movsxd   rax, dword ptr [rdi + 0xc]
024AADFC 488d04c6                 lea      rax, [rsi + rax*8]
024AAE00 4889442448               mov      qword ptr [rsp + 0x48], rax
024AAE05 483bf0                   cmp      rsi, rax
024AAE08 0f84e0000000             je       0x24aaeee
024AAE0E 4c8b253bde7b03           mov      r12, qword ptr [rip + 0x37bde3b]
024AAE15 4c89742458               mov      qword ptr [rsp + 0x58], r14
024AAE1A 660f1f440000             nop      word ptr [rax + rax]
024AAE20 4183ffff                 cmp      r15d, -1
024AAE24 0f84af000000             je       0x24aaed9
024AAE2A 4c8b4d08                 mov      r9, qword ptr [rbp + 8]
024AAE2E 41ffc7                   inc      r15d
024AAE31 4c8b36                   mov      r14, qword ptr [rsi]
024AAE34 33c0                     xor      eax, eax
024AAE36 458b415c                 mov      r8d, dword ptr [r9 + 0x5c]
024AAE3A 49633e                   movsxd   rdi, dword ptr [r14]
024AAE3D 4585c0                   test     r8d, r8d
024AAE40 0f8e84000000             jle      0x24aaeca
024AAE46 4d8b4950                 mov      r9, qword ptr [r9 + 0x50]
024AAE4A 660f1f440000             nop      word ptr [rax + rax]
024AAE50 4863c8                   movsxd   rcx, eax
024AAE53 488d1449                 lea      rdx, [rcx + rcx*2]
024AAE57 48c1e204                 shl      rdx, 4
024AAE5B 4903d1                   add      rdx, r9
024AAE5E 397a04                   cmp      dword ptr [rdx + 4], edi
024AAE61 7409                     je       0x24aae6c
024AAE63 ffc0                     inc      eax
024AAE65 413bc0                   cmp      eax, r8d
024AAE68 7ce6                     jl       0x24aae50
024AAE6A eb5e                     jmp      0x24aaeca
024AAE6C 4885d2                   test     rdx, rdx
024AAE6F 7459                     je       0x24aaeca
024AAE71 488d442430               lea      rax, [rsp + 0x30]
024AAE76 4883c210                 add      rdx, 0x10
024AAE7A 4889442428               mov      qword ptr [rsp + 0x28], rax
024AAE7F 488d4c2440               lea      rcx, [rsp + 0x40]
024AAE84 488d442438               lea      rax, [rsp + 0x38]
024AAE89 4d8bce                   mov      r9, r14
024AAE8C 4d8bc2                   mov      r8, r10
024AAE8F 4889442420               mov      qword ptr [rsp + 0x20], rax
024AAE94 e867e41900               call     0x2649300
024AAE99 48035c2440               add      rbx, qword ptr [rsp + 0x40]
024AAE9E 498b8424a0000000         mov      rax, qword ptr [r12 + 0xa0]
024AAEA6 83ff01                   cmp      edi, 1
024AAEA9 7c15                     jl       0x24aaec0
024AAEAB 3bb84c010000             cmp      edi, dword ptr [rax + 0x14c]
024AAEB1 7d0d                     jge      0x24aaec0
024AAEB3 488b8040010000           mov      rax, qword ptr [rax + 0x140]
024AAEBA 488b2cf8                 mov      rbp, qword ptr [rax + rdi*8]
024AAEBE eb07                     jmp      0x24aaec7
024AAEC0 488b2dc9348703           mov      rbp, qword ptr [rip + 0x38734c9]
024AAEC7 4d8bd6                   mov      r10, r14
024AAECA 4883c608                 add      rsi, 8
024AAECE 483b742448               cmp      rsi, qword ptr [rsp + 0x48]
024AAED3 0f8547ffffff             jne      0x24aae20
024AAED9 4c8ba42498000000         mov      r12, qword ptr [rsp + 0x98]
024AAEE1 488bbc24a0000000         mov      rdi, qword ptr [rsp + 0xa0]
024AAEE9 4c8b742458               mov      r14, qword ptr [rsp + 0x58]
024AAEEE 41837d4400               cmp      dword ptr [r13 + 0x44], 0
024AAEF3 4c8b7c2450               mov      r15, qword ptr [rsp + 0x50]
024AAEF8 488b742460               mov      rsi, qword ptr [rsp + 0x60]
024AAEFD 0f8414010000             je       0x24ab017
024AAF03 498b4538                 mov      rax, qword ptr [r13 + 0x38]
024AAF07 488b10                   mov      rdx, qword ptr [rax]
024AAF0A 488b07                   mov      rax, qword ptr [rdi]
024AAF0D 488b08                   mov      rcx, qword ptr [rax]
024AAF10 8b02                     mov      eax, dword ptr [rdx]
024AAF12 3901                     cmp      dword ptr [rcx], eax
024AAF14 0f85fd000000             jne      0x24ab017
024AAF1A 498b8d90010000           mov      rcx, qword ptr [r13 + 0x190]
024AAF21 498bbd68010000           mov      rdi, qword ptr [r13 + 0x168]
024AAF28 4885c9                   test     rcx, rcx
024AAF2B 7f27                     jg       0x24aaf54
024AAF2D 488d9424a0000000         lea      rdx, [rsp + 0xa0]
024AAF35 498bcd                   mov      rcx, r13
024AAF38 e863060000               call     0x24ab5a0
024AAF3D 488b8c24a0000000         mov      rcx, qword ptr [rsp + 0xa0]
024AAF45 4885c9                   test     rcx, rcx
024AAF48 750a                     jne      0x24aaf54
024AAF4A b8ffffffff               mov      eax, 0xffffffff
024AAF4F e9c0000000               jmp      0x24ab014
024AAF54 48b8a38d23d6e2530000     movabs   rax, 0x53e2d6238da3
024AAF5E 48ba461b47acc5a70000     movabs   rdx, 0xa7c5ac471b46
024AAF68 4803c7                   add      rax, rdi
024AAF6B 483bc2                   cmp      rax, rdx
024AAF6E 7711                     ja       0x24aaf81
024AAF70 4869c7a0860100           imul     rax, rdi, 0x186a0
024AAF77 4899                     cqo      
024AAF79 48f7f9                   idiv     rcx
024AAF7C e993000000               jmp      0x24ab014
024AAF81 488bc1                   mov      rax, rcx
024AAF84 4899                     cqo      
024AAF86 4833c2                   xor      rax, rdx
024AAF89 482bc2                   sub      rax, rdx
024AAF8C 48ba00e40b5402000000     movabs   rdx, 0x2540be400
024AAF96 483bc2                   cmp      rax, rdx
024AAF99 48b809e1d1c6116bf129     movabs   rax, 0x29f16b11c6d1e109
024AAFA3 7c1e                     jl       0x24aafc3
024AAFA5 48f7e9                   imul     rcx
024AAFA8 488bc7                   mov      rax, rdi
024AAFAB 4c8bc2                   mov      r8, rdx
024AAFAE 4899                     cqo      
024AAFB0 49c1f80e                 sar      r8, 0xe
024AAFB4 498bc8                   mov      rcx, r8
024AAFB7 48c1e93f                 shr      rcx, 0x3f
024AAFBB 4c03c1                   add      r8, rcx
024AAFBE 49f7f8                   idiv     r8
024AAFC1 eb51                     jmp      0x24ab014
024AAFC3 48f7ef                   imul     rdi
024AAFC6 48c1fa0e                 sar      rdx, 0xe
024AAFCA 488bc2                   mov      rax, rdx
024AAFCD 48c1e83f                 shr      rax, 0x3f
024AAFD1 4803d0                   add      rdx, rax
024AAFD4 4c69c2a0860100           imul     r8, rdx, 0x186a0
024AAFDB 498bc0                   mov      rax, r8
024AAFDE 492bf8                   sub      rdi, r8
024AAFE1 4899                     cqo      
024AAFE3 48f7f9                   idiv     rcx
024AAFE6 4c8bd0                   mov      r10, rax
024AAFE9 4c8bca                   mov      r9, rdx
024AAFEC 4869c7a0860100           imul     rax, rdi, 0x186a0
024AAFF3 4899                     cqo      
024AAFF5 48f7f9                   idiv     rcx
024AAFF8 4c8bc0                   mov      r8, rax
024AAFFB 4969c1a0860100           imul     rax, r9, 0x186a0
024AB002 4899                     cqo      
024AB004 48f7f9                   idiv     rcx
024AB007 4969caa0860100           imul     rcx, r10, 0x186a0
024AB00E 4903c0                   add      rax, r8
024AB011 4803c1                   add      rax, rcx
024AB014 482bd8                   sub      rbx, rax
024AB017 49891c24                 mov      qword ptr [r12], rbx
024AB01B 498bc4                   mov      rax, r12
024AB01E 488b9c2490000000         mov      rbx, qword ptr [rsp + 0x90]
024AB026 4883c468                 add      rsp, 0x68
024AB02A 415d                     pop      r13
024AB02C 415c                     pop      r12
024AB02E 5f                       pop      rdi
024AB02F 5d                       pop      rbp
024AB030 c3                       ret      
024AB031 cc                       int3     
024AB032 cc                       int3     
024AB033 cc                       int3     
024AB034 cc                       int3     
024AB035 cc                       int3     
024AB036 cc                       int3     
024AB037 cc                       int3     
024AB038 cc                       int3     
024AB039 cc                       int3     
024AB03A cc                       int3     
024AB03B cc                       int3     
024AB03C cc                       int3     
024AB03D cc                       int3     
024AB03E cc                       int3     
024AB03F cc                       int3     
