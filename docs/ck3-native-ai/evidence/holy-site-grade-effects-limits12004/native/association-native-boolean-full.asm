002B29C70 48895c2410                         mov      qword ptr [rsp + 0x10], rbx
002B29C75 48896c2418                         mov      qword ptr [rsp + 0x18], rbp
002B29C7A 4889742420                         mov      qword ptr [rsp + 0x20], rsi
002B29C7F 57                                 push     rdi
002B29C80 4154                               push     r12
002B29C82 4155                               push     r13
002B29C84 4156                               push     r14
002B29C86 4157                               push     r15
002B29C88 4881ec50020000                     sub      rsp, 0x250
002B29C8F 488bda                             mov      rbx, rdx
002B29C92 488bf9                             mov      rdi, rcx
002B29C95 e8964e0000                         call     0x2b2eb30
002B29C9A 488d4f40                           lea      rcx, [rdi + 0x40]
002B29C9E 488bd3                             mov      rdx, rbx
002B29CA1 4c8d4710                           lea      r8, [rdi + 0x10]
002B29CA5 4c8be8                             mov      r13, rax
002B29CA8 e8530b1eff                         call     0x1d0a800
002B29CAD 81780c74696146                     cmp      dword ptr [rax + 0xc], 0x46616974
002B29CB4 0f8570010000                       jne      0x2b29e2a
002B29CBA 837808ff                           cmp      dword ptr [rax + 8], -1
002B29CBE 0f8466010000                       je       0x2b29e2a
002B29CC4 488b9890080000                     mov      rbx, qword ptr [rax + 0x890]
002B29CCB 4863809c080000                     movsxd   rax, dword ptr [rax + 0x89c]
002B29CD2 488d3c83                           lea      rdi, [rbx + rax*4]
002B29CD6 483bdf                             cmp      rbx, rdi
002B29CD9 0f84cb010000                       je       0x2b29eaa
002B29CDF 65488b042558000000                 mov      rax, qword ptr gs:[0x58]
002B29CE8 458b8dec010000                     mov      r9d, dword ptr [r13 + 0x1ec]
002B29CEF 4d8bbde0010000                     mov      r15, qword ptr [r13 + 0x1e0]
002B29CF6 41ba10000000                       mov      r10d, 0x10
002B29CFC 4c0310                             add      r10, qword ptr [rax]
002B29CFF 4c89942480020000                   mov      qword ptr [rsp + 0x280], r10
002B29D07 4533e4                             xor      r12d, r12d
002B29D0A 660f1f440000                       nop      word ptr [rax + rax]
002B29D10 4c392569411f03                     cmp      qword ptr [rip + 0x31f4169], r12 ; RIP=0x5d1de80
002B29D17 742e                               je       0x2b29d47
002B29D19 8b13                               mov      edx, dword ptr [rbx]
002B29D1B 8bc2                               mov      eax, edx
002B29D1D 4c8b055c411f03                     mov      r8, qword ptr [rip + 0x31f415c] ; RIP=0x5d1de80
002B29D24 25ffffff00                         and      eax, 0xffffff
002B29D29 413b402c                           cmp      eax, dword ptr [r8 + 0x2c]
002B29D2D 7318                               jae      0x2b29d47
002B29D2F 8bc8                               mov      ecx, eax
002B29D31 498b4020                           mov      rax, qword ptr [r8 + 0x20]
002B29D35 4803c9                             add      rcx, rcx
002B29D38 488b44c808                         mov      rax, qword ptr [rax + rcx*8 + 8]
002B29D3D 4885c0                             test     rax, rax
002B29D40 7405                               je       0x2b29d47
002B29D42 395010                             cmp      dword ptr [rax + 0x10], edx
002B29D45 7407                               je       0x2b29d4e
002B29D47 488b05d2401f03                     mov      rax, qword ptr [rip + 0x31f40d2] ; RIP=0x5d1de20
002B29D4E 448b7010                           mov      r14d, dword ptr [rax + 0x10]
002B29D52 418b02                             mov      eax, dword ptr [r10]
002B29D55 3905e1601303                       cmp      dword ptr [rip + 0x31360e1], eax ; RIP=0x5c5fe3c
002B29D5B 4963f1                             movsxd   rsi, r9d
002B29D5E 498d2cb7                           lea      rbp, [r15 + rsi*4]
002B29D62 0f8f65010000                       jg       0x2b29ecd
002B29D68 488b05d1601303                     mov      rax, qword ptr [rip + 0x31360d1] ; RIP=0x5c5fe40
002B29D6F 48c1e820                           shr      rax, 0x20
002B29D73 3de84e0000                         cmp      eax, 0x4ee8
002B29D78 7212                               jb       0x2b29d8c
002B29D7A 4c8bcd                             mov      r9, rbp
002B29D7D 4489742420                         mov      dword ptr [rsp + 0x20], r14d
002B29D82 4d8bc7                             mov      r8, r15
002B29D85 e8e66a4601                         call     0x3f90870
002B29D8A eb52                               jmp      0x2b29dde
002B29D8C 48c1ee02                           shr      rsi, 2
002B29D90 498bc7                             mov      rax, r15
002B29D93 48c1e604                           shl      rsi, 4
002B29D97 4903f7                             add      rsi, r15
002B29D9A 66410f6ece                         movd     xmm1, r14d
002B29D9F 660f70c900                         pshufd   xmm1, xmm1, 0
002B29DA4 4c3bfe                             cmp      r15, rsi
002B29DA7 7422                               je       0x2b29dcb
002B29DA9 0f1f8000000000                     nop      dword ptr [rax]
002B29DB0 f30f6f00                           movdqu   xmm0, xmmword ptr [rax]
002B29DB4 660f76c1                           pcmpeqd  xmm0, xmm1
002B29DB8 0f50c8                             movmskps ecx, xmm0
002B29DBB 4863d1                             movsxd   rdx, ecx
002B29DBE 85c9                               test     ecx, ecx
002B29DC0 7554                               jne      0x2b29e16
002B29DC2 4883c010                           add      rax, 0x10
002B29DC6 483bc6                             cmp      rax, rsi
002B29DC9 75e5                               jne      0x2b29db0
002B29DCB 483bc5                             cmp      rax, rbp
002B29DCE 740e                               je       0x2b29dde
002B29DD0 443930                             cmp      dword ptr [rax], r14d
002B29DD3 7409                               je       0x2b29dde
002B29DD5 4883c004                           add      rax, 4
002B29DD9 483bc5                             cmp      rax, rbp
002B29DDC 75f2                               jne      0x2b29dd0
002B29DDE 4d638dec010000                     movsxd   r9, dword ptr [r13 + 0x1ec]
002B29DE5 4d8bbde0010000                     mov      r15, qword ptr [r13 + 0x1e0]
002B29DEC 4b8d148f                           lea      rdx, [r15 + r9*4]
002B29DF0 483bc2                             cmp      rax, rdx
002B29DF3 490f44c4                           cmove    rax, r12
002B29DF7 4885c0                             test     rax, rax
002B29DFA 7527                               jne      0x2b29e23
002B29DFC 4c8b942480020000                   mov      r10, qword ptr [rsp + 0x280]
002B29E04 4883c304                           add      rbx, 4
002B29E08 483bdf                             cmp      rbx, rdi
002B29E0B 0f85fffeffff                       jne      0x2b29d10
002B29E11 e994000000                         jmp      0x2b29eaa
002B29E16 480fbcca                           bsf      rcx, rdx
002B29E1A 4863c9                             movsxd   rcx, ecx
002B29E1D 488d0488                           lea      rax, [rax + rcx*4]
002B29E21 ebbb                               jmp      0x2b29dde
002B29E23 b001                               mov      al, 1
002B29E25 e982000000                         jmp      0x2b29eac
002B29E2A 807b2000                           cmp      byte ptr [rbx + 0x20], 0
002B29E2E 757a                               jne      0x2b29eaa
002B29E30 4533e4                             xor      r12d, r12d
002B29E33 4c8d0dae02c901                     lea      r9, [rip + 0x1c902ae] ; RIP=0x47ba0e8
002B29E3A 4c8d0547979701                     lea      r8, [rip + 0x1979747] ; RIP=0x44a3588
002B29E41 4489a42440020000                   mov      dword ptr [rsp + 0x240], r12d
002B29E49 ba00020000                         mov      edx, 0x200
002B29E4E 488d4c2440                         lea      rcx, [rsp + 0x40]
002B29E53 e8682ad5fd                         call     0x87c8c0
002B29E58 b9ff010000                         mov      ecx, 0x1ff
002B29E5D 3bc1                               cmp      eax, ecx
002B29E5F 0f4fc1                             cmovg    eax, ecx
002B29E62 488d4c2440                         lea      rcx, [rsp + 0x40]
002B29E67 89842440020000                     mov      dword ptr [rsp + 0x240], eax
002B29E6E 488d442440                         lea      rax, [rsp + 0x40]
002B29E73 4889442430                         mov      qword ptr [rsp + 0x30], rax
002B29E78 48c7c0ffffffff                     mov      rax, 0xffffffffffffffff
002B29E7F 90                                 nop      
002B29E80 48ffc0                             inc      rax
002B29E83 44382401                           cmp      byte ptr [rcx + rax], r12b
002B29E87 75f7                               jne      0x2b29e80
002B29E89 89442438                           mov      dword ptr [rsp + 0x38], eax
002B29E8D 488d542430                         lea      rdx, [rsp + 0x30]
002B29E92 448864243c                         mov      byte ptr [rsp + 0x3c], r12b
002B29E97 488bcf                             mov      rcx, rdi
002B29E9A 0f28442430                         movaps   xmm0, xmmword ptr [rsp + 0x30]
002B29E9F 660f7f442430                       movdqa   xmmword ptr [rsp + 0x30], xmm0
002B29EA5 e8866ebe00                         call     0x3710d30
002B29EAA 32c0                               xor      al, al
002B29EAC 4c8d9c2450020000                   lea      r11, [rsp + 0x250]
002B29EB4 498b5b38                           mov      rbx, qword ptr [r11 + 0x38]
002B29EB8 498b6b40                           mov      rbp, qword ptr [r11 + 0x40]
002B29EBC 498b7348                           mov      rsi, qword ptr [r11 + 0x48]
002B29EC0 498be3                             mov      rsp, r11
002B29EC3 415f                               pop      r15
002B29EC5 415e                               pop      r14
002B29EC7 415d                               pop      r13
002B29EC9 415c                               pop      r12
002B29ECB 5f                                 pop      rdi
002B29ECC c3                                 ret      
002B29ECD 488d0d685f1303                     lea      rcx, [rip + 0x3135f68] ; RIP=0x5c5fe3c
002B29ED4 e8ab9b6f01                         call     0x4223a84
002B29ED9 833d5c5f1303ff                     cmp      dword ptr [rip + 0x3135f5c], -1 ; RIP=0x5c5fe3c
002B29EE0 0f8582feffff                       jne      0x2b29d68
002B29EE6 e87595d5fd                         call     0x883460
002B29EEB 488d0d4a5f1303                     lea      rcx, [rip + 0x3135f4a] ; RIP=0x5c5fe3c
002B29EF2 e82d9b6f01                         call     0x4223a24
002B29EF7 e96cfeffff                         jmp      0x2b29d68
002B29EFC cc                                 int3     
002B29EFD cc                                 int3     
002B29EFE cc                                 int3     
002B29EFF cc                                 int3     
