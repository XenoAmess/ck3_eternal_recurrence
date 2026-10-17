00291E537 488bd7                           mov      rdx, rdi
00291E53A 498bcd                           mov      rcx, r13
00291E53D e86e070000                       call     0x291ecb0
00291E542 488b4748                         mov      rax, qword ptr [rdi + 0x48]
00291E546 83786402                         cmp      dword ptr [rax + 0x64], 2
00291E54A 0f85cb010000                     jne      0x291e71b
00291E550 488b9fe0010000                   mov      rbx, qword ptr [rdi + 0x1e0]
00291E557 486387ec010000                   movsxd   rax, dword ptr [rdi + 0x1ec]
00291E55E 4c8d2c83                         lea      r13, [rbx + rax*4]
00291E562 493bdd                           cmp      rbx, r13
00291E565 0f84a9010000                     je       0x291e714
00291E56B 0f1f440000                       nop      dword ptr [rax + rax]
00291E570 8b03                             mov      eax, dword ptr [rbx]
00291E572 48833d06f93f0300                 cmp      qword ptr [rip + 0x33ff906], 0 ; RIP=0x5d1de80
00291E57A 742e                             je       0x291e5aa
00291E57C 4c8b05fdf83f03                   mov      r8, qword ptr [rip + 0x33ff8fd] ; RIP=0x5d1de80
00291E583 8bc8                             mov      ecx, eax
00291E585 81e1ffffff00                     and      ecx, 0xffffff
00291E58B 413b482c                         cmp      ecx, dword ptr [r8 + 0x2c]
00291E58F 7319                             jae      0x291e5aa
00291E591 8bd1                             mov      edx, ecx
00291E593 4803d2                           add      rdx, rdx
00291E596 498b4820                         mov      rcx, qword ptr [r8 + 0x20]
00291E59A 4c8b74d108                       mov      r14, qword ptr [rcx + rdx*8 + 8]
00291E59F 4d85f6                           test     r14, r14
00291E5A2 7406                             je       0x291e5aa
00291E5A4 41394610                         cmp      dword ptr [r14 + 0x10], eax
00291E5A8 7407                             je       0x291e5b1
00291E5AA 4c8b356ff83f03                   mov      r14, qword ptr [rip + 0x33ff86f] ; RIP=0x5d1de20
00291E5B1 498b4620                         mov      rax, qword ptr [r14 + 0x20]
00291E5B5 83b82402000000                   cmp      dword ptr [rax + 0x224], 0
00291E5BC 0f8445010000                     je       0x291e707
00291E5C2 41807e1800                       cmp      byte ptr [r14 + 0x18], 0
00291E5C7 0f843a010000                     je       0x291e707
00291E5CD 48833d23fd3f0300                 cmp      qword ptr [rip + 0x33ffd23], 0 ; RIP=0x5d1e2f8
00291E5D5 7433                             je       0x291e60a
00291E5D7 418b97b4000000                   mov      edx, dword ptr [r15 + 0xb4]
00291E5DE 4c8b0513fd3f03                   mov      r8, qword ptr [rip + 0x33ffd13] ; RIP=0x5d1e2f8
00291E5E5 8bc2                             mov      eax, edx
00291E5E7 25ffffff00                       and      eax, 0xffffff
00291E5EC 413b402c                         cmp      eax, dword ptr [r8 + 0x2c]
00291E5F0 7318                             jae      0x291e60a
00291E5F2 8bc8                             mov      ecx, eax
00291E5F4 4803c9                           add      rcx, rcx
00291E5F7 498b4020                         mov      rax, qword ptr [r8 + 0x20]
00291E5FB 488b44c808                       mov      rax, qword ptr [rax + rcx*8 + 8]
00291E600 4885c0                           test     rax, rax
00291E603 7405                             je       0x291e60a
00291E605 395008                           cmp      dword ptr [rax + 8], edx
00291E608 7407                             je       0x291e611
00291E60A 488b055f903403                   mov      rax, qword ptr [rip + 0x334905f] ; RIP=0x5c67670
00291E611 4963b6a4000000                   movsxd   rsi, dword ptr [r14 + 0xa4]
00291E618 498bbe98000000                   mov      rdi, qword ptr [r14 + 0x98]
00291E61F 4c8d3cb7                         lea      r15, [rdi + rsi*4]
00291E623 448ba0b8040000                   mov      r12d, dword ptr [rax + 0x4b8]
00291E62A ba10000000                       mov      edx, 0x10
00291E62F 65488b042558000000               mov      rax, qword ptr gs:[0x58]
00291E638 488b08                           mov      rcx, qword ptr [rax]
00291E63B 8b040a                           mov      eax, dword ptr [rdx + rcx]
00291E63E 3905f8173403                     cmp      dword ptr [rip + 0x33417f8], eax ; RIP=0x5c5fe3c
00291E644 0f8ffc050000                     jg       0x291ec46
00291E64A 488b05ef173403                   mov      rax, qword ptr [rip + 0x33417ef] ; RIP=0x5c5fe40
00291E651 48c1e820                         shr      rax, 0x20
00291E655 3de84e0000                       cmp      eax, 0x4ee8
00291E65A 7215                             jb       0x291e671
00291E65C 4489642420                       mov      dword ptr [rsp + 0x20], r12d
00291E661 4d8bcf                           mov      r9, r15
00291E664 4c8bc7                           mov      r8, rdi
00291E667 e804226701                       call     0x3f90870
00291E66C 488bf8                           mov      rdi, rax
00291E66F eb51                             jmp      0x291e6c2
00291E671 66410f6ecc                       movd     xmm1, r12d
00291E676 660f70c900                       pshufd   xmm1, xmm1, 0
00291E67B 48c1ee02                         shr      rsi, 2
00291E67F 48c1e604                         shl      rsi, 4
00291E683 4803f7                           add      rsi, rdi
00291E686 483bfe                           cmp      rdi, rsi
00291E689 7424                             je       0x291e6af
00291E68B 0f1f440000                       nop      dword ptr [rax + rax]
00291E690 f30f6f07                         movdqu   xmm0, xmmword ptr [rdi]
00291E694 660f76c1                         pcmpeqd  xmm0, xmm1
00291E698 0f50c0                           movmskps eax, xmm0
00291E69B 4863c8                           movsxd   rcx, eax
00291E69E 85c0                             test     eax, eax
00291E6A0 0f85a8000000                     jne      0x291e74e
00291E6A6 4883c710                         add      rdi, 0x10
00291E6AA 483bfe                           cmp      rdi, rsi
00291E6AD 75e1                             jne      0x291e690
00291E6AF 493bff                           cmp      rdi, r15
00291E6B2 740e                             je       0x291e6c2
00291E6B4 443927                           cmp      dword ptr [rdi], r12d
00291E6B7 7409                             je       0x291e6c2
00291E6B9 4883c704                         add      rdi, 4
00291E6BD 493bff                           cmp      rdi, r15
00291E6C0 75f2                             jne      0x291e6b4
00291E6C2 498b8e98000000                   mov      rcx, qword ptr [r14 + 0x98]
00291E6C9 496386a4000000                   movsxd   rax, dword ptr [r14 + 0xa4]
00291E6D0 488d1481                         lea      rdx, [rcx + rax*4]
00291E6D4 483bfa                           cmp      rdi, rdx
00291E6D7 41bc00000000                     mov      r12d, 0
00291E6DD 490f44fc                         cmove    rdi, r12
00291E6E1 4885ff                           test     rdi, rdi
00291E6E4 741a                             je       0x291e700
00291E6E6 498b5620                         mov      rdx, qword ptr [r14 + 0x20]
00291E6EA 4881c218020000                   add      rdx, 0x218
00291E6F1 41b8a0860100                     mov      r8d, 0x186a0
00291E6F7 488d4d10                         lea      rcx, [rbp + 0x10]
00291E6FB e8004a9eff                       call     0x2303100
00291E700 4c8bbdd8030000                   mov      r15, qword ptr [rbp + 0x3d8]
00291E707 4883c304                         add      rbx, 4
00291E70B 493bdd                           cmp      rbx, r13
00291E70E 0f855cfeffff                     jne      0x291e570
00291E714 4c8badd0030000                   mov      r13, qword ptr [rbp + 0x3d0]
