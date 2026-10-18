002B2A2F0 4053                               push     rbx
002B2A2F2 57                                 push     rdi
002B2A2F3 4155                               push     r13
002B2A2F5 4156                               push     r14
002B2A2F7 4883ec28                           sub      rsp, 0x28
002B2A2FB 488b02                             mov      rax, qword ptr [rdx]
002B2A2FE 4c8be9                             mov      r13, rcx
002B2A301 6683380d                           cmp      word ptr [rax], 0xd
002B2A305 7505                               jne      0x2b2a30c
002B2A307 8b5008                             mov      edx, dword ptr [rax + 8]
002B2A30A eb05                               jmp      0x2b2a311
002B2A30C baffffffff                         mov      edx, 0xffffffff
002B2A311 4c8b05e83f1f03                     mov      r8, qword ptr [rip + 0x31f3fe8] ; RIP=0x5d1e300
002B2A318 4d85c0                             test     r8, r8
002B2A31B 7426                               je       0x2b2a343
002B2A31D 8bc2                               mov      eax, edx
002B2A31F 25ffffff00                         and      eax, 0xffffff
002B2A324 413b402c                           cmp      eax, dword ptr [r8 + 0x2c]
002B2A328 7319                               jae      0x2b2a343
002B2A32A 8bc8                               mov      ecx, eax
002B2A32C 498b4020                           mov      rax, qword ptr [r8 + 0x20]
002B2A330 4803c9                             add      rcx, rcx
002B2A333 4c8b74c808                         mov      r14, qword ptr [rax + rcx*8 + 8]
002B2A338 4d85f6                             test     r14, r14
002B2A33B 7406                               je       0x2b2a343
002B2A33D 41395608                           cmp      dword ptr [r14 + 8], edx
002B2A341 7407                               je       0x2b2a34a
002B2A343 4c8b35963f1f03                     mov      r14, qword ptr [rip + 0x31f3f96] ; RIP=0x5d1e2e0
002B2A34A 498b9e90080000                     mov      rbx, qword ptr [r14 + 0x890]
002B2A351 4963869c080000                     movsxd   rax, dword ptr [r14 + 0x89c]
002B2A358 48896c2450                         mov      qword ptr [rsp + 0x50], rbp
002B2A35D 4889742458                         mov      qword ptr [rsp + 0x58], rsi
002B2A362 4c89642460                         mov      qword ptr [rsp + 0x60], r12
002B2A367 488d3c83                           lea      rdi, [rbx + rax*4]
002B2A36B 4c897c2420                         mov      qword ptr [rsp + 0x20], r15
002B2A370 483bdf                             cmp      rbx, rdi
002B2A373 0f84b5000000                       je       0x2b2a42e
002B2A379 488b2d003b1f03                     mov      rbp, qword ptr [rip + 0x31f3b00] ; RIP=0x5d1de80
002B2A380 4c8b25993a1f03                     mov      r12, qword ptr [rip + 0x31f3a99] ; RIP=0x5d1de20
002B2A387 4885ed                             test     rbp, rbp
002B2A38A 7427                               je       0x2b2a3b3
002B2A38C 8b13                               mov      edx, dword ptr [rbx]
002B2A38E 8bc2                               mov      eax, edx
002B2A390 25ffffff00                         and      eax, 0xffffff
002B2A395 3b452c                             cmp      eax, dword ptr [rbp + 0x2c]
002B2A398 7319                               jae      0x2b2a3b3
002B2A39A 8bc8                               mov      ecx, eax
002B2A39C 488b4520                           mov      rax, qword ptr [rbp + 0x20]
002B2A3A0 4803c9                             add      rcx, rcx
002B2A3A3 4c8b5cc808                         mov      r11, qword ptr [rax + rcx*8 + 8]
002B2A3A8 4d85db                             test     r11, r11
002B2A3AB 7406                               je       0x2b2a3b3
002B2A3AD 41395310                           cmp      dword ptr [r11 + 0x10], edx
002B2A3B1 7403                               je       0x2b2a3b6
002B2A3B3 4d8bdc                             mov      r11, r12
002B2A3B6 41807b1800                         cmp      byte ptr [r11 + 0x18], 0
002B2A3BB 7464                               je       0x2b2a421
002B2A3BD 498b4b20                           mov      rcx, qword ptr [r11 + 0x20]
002B2A3C1 418b4540                           mov      eax, dword ptr [r13 + 0x40]
002B2A3C5 4c63514c                           movsxd   r10, dword ptr [rcx + 0x4c]
002B2A3C9 488b7140                           mov      rsi, qword ptr [rcx + 0x40]
002B2A3CD 488bce                             mov      rcx, rsi
002B2A3D0 4e8d3c96                           lea      r15, [rsi + r10*4]
002B2A3D4 4d85d2                             test     r10, r10
002B2A3D7 7e24                               jle      0x2b2a3fd
002B2A3D9 0f1f8000000000                     nop      dword ptr [rax]
002B2A3E0 4d8bca                             mov      r9, r10
002B2A3E3 49d1e9                             shr      r9, 1
002B2A3E6 4d2bd1                             sub      r10, r9
002B2A3E9 42390489                           cmp      dword ptr [rcx + r9*4], eax
002B2A3ED 4e8d0491                           lea      r8, [rcx + r10*4]
002B2A3F1 4d8bd1                             mov      r10, r9
002B2A3F4 490f4cc8                           cmovl    rcx, r8
002B2A3F8 4d85c9                             test     r9, r9
002B2A3FB 75e3                               jne      0x2b2a3e0
002B2A3FD 493bcf                             cmp      rcx, r15
002B2A400 741f                               je       0x2b2a421
002B2A402 3b01                               cmp      eax, dword ptr [rcx]
002B2A404 7c1b                               jl       0x2b2a421
002B2A406 482bce                             sub      rcx, rsi
002B2A409 48c1f902                           sar      rcx, 2
002B2A40D 83f9ff                             cmp      ecx, -1
002B2A410 740f                               je       0x2b2a421
002B2A412 498bd3                             mov      rdx, r11
002B2A415 498bce                             mov      rcx, r14
002B2A418 e8137b91ff                         call     0x2441f30
002B2A41D 84c0                               test     al, al
002B2A41F 752e                               jne      0x2b2a44f
002B2A421 4883c304                           add      rbx, 4
002B2A425 483bdf                             cmp      rbx, rdi
002B2A428 0f8559ffffff                       jne      0x2b2a387
002B2A42E 32c0                               xor      al, al
002B2A430 4c8b7c2420                         mov      r15, qword ptr [rsp + 0x20]
002B2A435 4c8b642460                         mov      r12, qword ptr [rsp + 0x60]
002B2A43A 488b742458                         mov      rsi, qword ptr [rsp + 0x58]
002B2A43F 488b6c2450                         mov      rbp, qword ptr [rsp + 0x50]
002B2A444 4883c428                           add      rsp, 0x28
002B2A448 415e                               pop      r14
002B2A44A 415d                               pop      r13
002B2A44C 5f                                 pop      rdi
002B2A44D 5b                                 pop      rbx
002B2A44E c3                                 ret      
002B2A44F b001                               mov      al, 1
002B2A451 ebdd                               jmp      0x2b2a430
