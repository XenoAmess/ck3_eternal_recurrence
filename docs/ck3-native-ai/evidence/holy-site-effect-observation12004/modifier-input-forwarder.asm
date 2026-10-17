002438830 4053                             push     rbx
002438832 56                               push     rsi
002438833 57                               push     rdi
002438834 4883ec30                         sub      rsp, 0x30
002438838 837a0c00                         cmp      dword ptr [rdx + 0xc], 0
00243883C 498bd8                           mov      rbx, r8
00243883F 488bf2                           mov      rsi, rdx
002438842 488bf9                           mov      rdi, rcx
002438845 0f8428010000                     je       0x2438973
00243884B f00fbaa92802000000               lock bts dword ptr [rcx + 0x228], 0
002438854 731a                             jae      0x2438870
002438856 66660f1f840000000000             nop      word ptr [rax + rax]
002438860 f390                             pause    
002438862 f00fbaa92802000000               lock bts dword ptr [rcx + 0x228], 0
00243886B 72f3                             jb       0x2438860
00243886D 0f1f00                           nop      dword ptr [rax]
002438870 8b8128020000                     mov      eax, dword ptr [rcx + 0x228]
002438876 83f801                           cmp      eax, 1
002438879 7604                             jbe      0x243887f
00243887B f390                             pause    
00243887D ebf1                             jmp      0x2438870
00243887F 4863410c                         movsxd   rax, dword ptr [rcx + 0xc]
002438883 8b4908                           mov      ecx, dword ptr [rcx + 8]
002438886 4889742420                       mov      qword ptr [rsp + 0x20], rsi
00243888B 48895c2428                       mov      qword ptr [rsp + 0x28], rbx
002438890 3bc1                             cmp      eax, ecx
002438892 0f85af000000                     jne      0x2438947
002438898 660f6ec1                         movd     xmm0, ecx
00243889C 41b808000000                     mov      r8d, 8
0024388A2 488b4f10                         mov      rcx, qword ptr [rdi + 0x10]
0024388A6 0f5bc0                           cvtdq2ps xmm0, xmm0
0024388A9 48896c2450                       mov      qword ptr [rsp + 0x50], rbp
0024388AE 4c89742458                       mov      qword ptr [rsp + 0x58], r14
0024388B3 4c897c2460                       mov      qword ptr [rsp + 0x60], r15
0024388B8 448d7801                         lea      r15d, [rax + 1]
0024388BC 458bf7                           mov      r14d, r15d
0024388BF f30f590529dc5b02                 mulss    xmm0, dword ptr [rip + 0x25bdc29] ; RIP=0x49f64f0
0024388C7 f30f2cc0                         cvttss2si eax, xmm0
0024388CB 443bf8                           cmp      r15d, eax
0024388CE 440f4cf0                         cmovl    r14d, eax
0024388D2 488b01                           mov      rax, qword ptr [rcx]
0024388D5 418bd6                           mov      edx, r14d
0024388D8 48c1e204                         shl      rdx, 4
0024388DC ff5008                           call     qword ptr [rax + 8]
0024388DF 48634f0c                         movsxd   rcx, dword ptr [rdi + 0xc]
0024388E3 488be8                           mov      rbp, rax
0024388E6 0f10442420                       movups   xmm0, xmmword ptr [rsp + 0x20]
0024388EB 4803c9                           add      rcx, rcx
0024388EE 0f1104c8                         movups   xmmword ptr [rax + rcx*8], xmm0
0024388F2 448b4f0c                         mov      r9d, dword ptr [rdi + 0xc]
0024388F6 4585c9                           test     r9d, r9d
0024388F9 7e1d                             jle      0x2438918
0024388FB 488b0f                           mov      rcx, qword ptr [rdi]
0024388FE 488bd0                           mov      rdx, rax
002438901 0f1001                           movups   xmm0, xmmword ptr [rcx]
002438904 41ffc9                           dec      r9d
002438907 488d5210                         lea      rdx, [rdx + 0x10]
00243890B 488d4910                         lea      rcx, [rcx + 0x10]
00243890F 0f1142f0                         movups   xmmword ptr [rdx - 0x10], xmm0
002438913 4585c9                           test     r9d, r9d
002438916 7fe9                             jg       0x2438901
002438918 488b4f10                         mov      rcx, qword ptr [rdi + 0x10]
00243891C 41b808000000                     mov      r8d, 8
002438922 488b17                           mov      rdx, qword ptr [rdi]
002438925 488b01                           mov      rax, qword ptr [rcx]
002438928 ff5010                           call     qword ptr [rax + 0x10]
00243892B 48892f                           mov      qword ptr [rdi], rbp
00243892E 488b6c2450                       mov      rbp, qword ptr [rsp + 0x50]
002438933 44897f0c                         mov      dword ptr [rdi + 0xc], r15d
002438937 4c8b7c2460                       mov      r15, qword ptr [rsp + 0x60]
00243893C 44897708                         mov      dword ptr [rdi + 8], r14d
002438940 4c8b742458                       mov      r14, qword ptr [rsp + 0x58]
002438945 eb15                             jmp      0x243895c
002438947 0f10442420                       movups   xmm0, xmmword ptr [rsp + 0x20]
00243894C 488bc8                           mov      rcx, rax
00243894F 488b07                           mov      rax, qword ptr [rdi]
002438952 4803c9                           add      rcx, rcx
002438955 0f1104c8                         movups   xmmword ptr [rax + rcx*8], xmm0
002438959 ff470c                           inc      dword ptr [rdi + 0xc]
00243895C f083a728020000fe                 lock and dword ptr [rdi + 0x228], 0xfffffffe
002438964 488d4f68                         lea      rcx, [rdi + 0x68]
002438968 4c8bc3                           mov      r8, rbx
00243896B 488bd6                           mov      rdx, rsi
00243896E e88da7ecff                       call     0x2303100
002438973 4883c430                         add      rsp, 0x30
002438977 5f                               pop      rdi
002438978 5e                               pop      rsi
002438979 5b                               pop      rbx
00243897A c3                               ret      
