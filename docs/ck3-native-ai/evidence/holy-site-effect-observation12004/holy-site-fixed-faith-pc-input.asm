0024FB4F6 488b8510040000                   mov      rax, qword ptr [rbp + 0x410]
0024FB4FD 448b707c                         mov      r14d, dword ptr [rax + 0x7c]
0024FB501 41837d6400                       cmp      dword ptr [r13 + 0x64], 0
0024FB506 7436                             je       0x24fb53e
0024FB508 498b4720                         mov      rax, qword ptr [r15 + 0x20]
0024FB50C 488d4858                         lea      rcx, [rax + 0x58]
0024FB510 80b81804000000                   cmp      byte ptr [rax + 0x418], 0
0024FB517 740f                             je       0x24fb528
0024FB519 488bd1                           mov      rdx, rcx
0024FB51C 488b4c2430                       mov      rcx, qword ptr [rsp + 0x30]
0024FB521 e8aa1d0000                       call     0x24fd2d0
0024FB526 eb16                             jmp      0x24fb53e
0024FB528 48898d20040000                   mov      qword ptr [rbp + 0x420], rcx
0024FB52F 488d9520040000                   lea      rdx, [rbp + 0x420]
0024FB536 488bce                           mov      rcx, rsi
0024FB539 e8024e38fe                       call     0x880340
