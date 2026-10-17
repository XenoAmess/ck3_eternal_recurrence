002303100 4053                             push     rbx
002303102 55                               push     rbp
002303103 4156                             push     r14
002303105 4883ec30                         sub      rsp, 0x30
002303109 83790c00                         cmp      dword ptr [rcx + 0xc], 0
00230310D 498bd8                           mov      rbx, r8
002303110 4c8bf2                           mov      r14, rdx
002303113 488be9                           mov      rbp, rcx
002303116 7525                             jne      0x230313d
002303118 e843e0edfe                       call     0x11e1160
00230311D 498d5668                         lea      rdx, [r14 + 0x68]
002303121 488d4d68                         lea      rcx, [rbp + 0x68]
002303125 e8260e87fe                       call     0xb73f50
00230312A 488bd3                           mov      rdx, rbx
00230312D 488bcd                           mov      rcx, rbp
002303130 4883c430                         add      rsp, 0x30
002303134 415e                             pop      r14
002303136 5d                               pop      rbp
002303137 5b                               pop      rbx
002303138 e943020000                       jmp      0x2303380
00230313D 4c897c2420                       mov      qword ptr [rsp + 0x20], r15
002303142 4c637a0c                         movsxd   r15, dword ptr [rdx + 0xc]
002303146 4d85ff                           test     r15, r15
002303149 0f8e19010000                     jle      0x2303268
00230314F 4889742450                       mov      qword ptr [rsp + 0x50], rsi
002303154 49ba09e1d1c6116bf129             movabs   r10, 0x29f16b11c6d1e109
00230315E 4c89642460                       mov      qword ptr [rsp + 0x60], r12
002303163 33f6                             xor      esi, esi
002303165 4c896c2428                       mov      qword ptr [rsp + 0x28], r13
00230316A 41bc33f304b5                     mov      r12d, 0xb504f333
002303170 49bd66e6096a01000000             movabs   r13, 0x16a09e666
00230317A 48897c2458                       mov      qword ptr [rsp + 0x58], rdi
00230317F 41bbffff0000                     mov      r11d, 0xffff
002303185 6666660f1f840000000000           nop      word ptr [rax + rax]
002303190 498b4668                         mov      rax, qword ptr [r14 + 0x68]
002303194 488b0cf0                         mov      rcx, qword ptr [rax + rsi*8]
002303198 4a8d0421                         lea      rax, [rcx + r12]
00230319C 493bc5                           cmp      rax, r13
00230319F 7726                             ja       0x23031c7
0023031A1 4a8d0423                         lea      rax, [rbx + r12]
0023031A5 493bc5                           cmp      rax, r13
0023031A8 771d                             ja       0x23031c7
0023031AA 480fafcb                         imul     rcx, rbx
0023031AE 498bc2                           mov      rax, r10
0023031B1 48f7e9                           imul     rcx
0023031B4 488bfa                           mov      rdi, rdx
0023031B7 48c1ff0e                         sar      rdi, 0xe
0023031BB 488bc7                           mov      rax, rdi
0023031BE 48c1e83f                         shr      rax, 0x3f
0023031C2 4803f8                           add      rdi, rax
0023031C5 eb51                             jmp      0x2303218
0023031C7 483bd9                           cmp      rbx, rcx
0023031CA 4c8bc3                           mov      r8, rbx
0023031CD 4c8bcb                           mov      r9, rbx
0023031D0 498bc2                           mov      rax, r10
0023031D3 4c0f4cc1                         cmovl    r8, rcx
0023031D7 4c0f4fc9                         cmovg    r9, rcx
0023031DB 49f7e8                           imul     r8
0023031DE 488bca                           mov      rcx, rdx
0023031E1 48c1f90e                         sar      rcx, 0xe
0023031E5 488bc1                           mov      rax, rcx
0023031E8 48c1e83f                         shr      rax, 0x3f
0023031EC 4803c8                           add      rcx, rax
0023031EF 4869c1a0860100                   imul     rax, rcx, 0x186a0
0023031F6 490fafc9                         imul     rcx, r9
0023031FA 4c2bc0                           sub      r8, rax
0023031FD 498bc2                           mov      rax, r10
002303200 4d0fafc1                         imul     r8, r9
002303204 49f7e8                           imul     r8
002303207 48c1fa0e                         sar      rdx, 0xe
00230320B 488bfa                           mov      rdi, rdx
00230320E 48c1ef3f                         shr      rdi, 0x3f
002303212 4803fa                           add      rdi, rdx
002303215 4803f9                           add      rdi, rcx
002303218 498b06                           mov      rax, qword ptr [r14]
00230321B 0fb71470                         movzx    edx, word ptr [rax + rsi*2]
00230321F 66413bd3                         cmp      dx, r11w
002303223 7423                             je       0x2303248
002303225 488bcd                           mov      rcx, rbp
002303228 e8d3060000                       call     0x2303900
00230322D 4863c8                           movsxd   rcx, eax
002303230 49ba09e1d1c6116bf129             movabs   r10, 0x29f16b11c6d1e109
00230323A 488b4568                         mov      rax, qword ptr [rbp + 0x68]
00230323E 41bbffff0000                     mov      r11d, 0xffff
002303244 48013cc8                         add      qword ptr [rax + rcx*8], rdi
002303248 48ffc6                           inc      rsi
00230324B 493bf7                           cmp      rsi, r15
00230324E 0f8c3cffffff                     jl       0x2303190
002303254 4c8b6c2428                       mov      r13, qword ptr [rsp + 0x28]
002303259 4c8b642460                       mov      r12, qword ptr [rsp + 0x60]
00230325E 488b7c2458                       mov      rdi, qword ptr [rsp + 0x58]
002303263 488b742450                       mov      rsi, qword ptr [rsp + 0x50]
002303268 4c8b7c2420                       mov      r15, qword ptr [rsp + 0x20]
00230326D 4883c430                         add      rsp, 0x30
002303271 415e                             pop      r14
002303273 5d                               pop      rbp
002303274 5b                               pop      rbx
002303275 c3                               ret      
