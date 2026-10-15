0290DC00  40 53                            push rbx
0290DC02  55                               push rbp
0290DC03  56                               push rsi
0290DC04  57                               push rdi
0290DC05  41 54                            push r12
0290DC07  41 55                            push r13
0290DC09  41 56                            push r14
0290DC0B  41 57                            push r15
0290DC0D  48 81 ec a8 00 00 00             sub rsp, 0xa8
0290DC14  0f 29 b4 24 90 00 00 00          movaps xmmword ptr [rsp + 0x90], xmm6
0290DC1C  4c 8b f9                         mov r15, rcx
0290DC1F  44 8b 69 14                      mov r13d, dword ptr [rcx + 0x14]
0290DC23  44 89 ac 24 f8 00 00 00          mov dword ptr [rsp + 0xf8], r13d
0290DC2B  8b 49 1c                         mov ecx, dword ptr [rcx + 0x1c]
0290DC2E  89 8c 24 00 01 00 00             mov dword ptr [rsp + 0x100], ecx
0290DC35  8b d9                            mov ebx, ecx
0290DC37  f0 41 0f c1 1f                   lock xadd dword ptr [r15], ebx
0290DC3C  41 3b dd                         cmp ebx, r13d
0290DC3F  0f 8d 74 01 00 00                jge 0x290ddb9
0290DC45  48 8d 15 d4 20 00 00             lea rdx, [rip + 0x20d4]
0290DC4C  0f 1f 40 00                      nop dword ptr [rax]
0290DC50  8d 04 0b                         lea eax, [rbx + rcx]
0290DC53  41 8b ed                         mov ebp, r13d
0290DC56  41 3b c5                         cmp eax, r13d
0290DC59  0f 4c e8                         cmovl ebp, eax
0290DC5C  3b dd                            cmp ebx, ebp
0290DC5E  0f 84 40 01 00 00                je 0x290dda4
0290DC64  4d 8d 6f 70                      lea r13, [r15 + 0x70]
0290DC68  4d 8d 77 48                      lea r14, [r15 + 0x48]
0290DC6C  48 8d 44 24 70                   lea rax, [rsp + 0x70]
0290DC71  48 89 44 24 40                   mov qword ptr [rsp + 0x40], rax
0290DC76  48 89 54 24 48                   mov qword ptr [rsp + 0x48], rdx
0290DC7B  0f 28 74 24 40                   movaps xmm6, xmmword ptr [rsp + 0x40]
0290DC80  4d 8b 67 68                      mov r12, qword ptr [r15 + 0x68]
0290DC84  89 9c 24 f0 00 00 00             mov dword ptr [rsp + 0xf0], ebx
0290DC8B  4c 89 6c 24 20                   mov qword ptr [rsp + 0x20], r13
0290DC90  e8 9b ab 06 01                   call 0x3978830
0290DC95  f6 40 30 01                      test byte ptr [rax + 0x30], 1
0290DC99  75 09                            jne 0x290dca4
0290DC9B  be ff ff ff ff                   mov esi, 0xffffffff
0290DCA0  33 ff                            xor edi, edi
0290DCA2  eb 22                            jmp 0x290dcc6
0290DCA4  48 8b c8                         mov rcx, rax
0290DCA7  e8 b4 be 06 01                   call 0x3979b60
0290DCAC  48 8b 38                         mov rdi, qword ptr [rax]
0290DCAF  48 85 ff                         test rdi, rdi
0290DCB2  75 07                            jne 0x290dcbb
0290DCB4  be ff ff ff ff                   mov esi, 0xffffffff
0290DCB9  eb 0b                            jmp 0x290dcc6
0290DCBB  48 8b 0f                         mov rcx, qword ptr [rdi]
0290DCBE  e8 cd e3 06 01                   call 0x397c090
0290DCC3  8b 70 1c                         mov esi, dword ptr [rax + 0x1c]
0290DCC6  89 74 24 30                      mov dword ptr [rsp + 0x30], esi
0290DCCA  48 89 7c 24 38                   mov qword ptr [rsp + 0x38], rdi
0290DCCF  0f 28 44 24 30                   movaps xmm0, xmmword ptr [rsp + 0x30]
0290DCD4  66 0f 7f 44 24 60                movdqa xmmword ptr [rsp + 0x60], xmm0
0290DCDA  e8 51 ab 06 01                   call 0x3978830
0290DCDF  f6 40 30 01                      test byte ptr [rax + 0x30], 1
0290DCE3  74 32                            je 0x290dd17
0290DCE5  48 8b c8                         mov rcx, rax
0290DCE8  e8 73 be 06 01                   call 0x3979b60
0290DCED  48 8b 08                         mov rcx, qword ptr [rax]
0290DCF0  4c 89 30                         mov qword ptr [rax], r14
0290DCF3  48 85 c9                         test rcx, rcx
0290DCF6  74 0f                            je 0x290dd07
0290DCF8  48 8b 09                         mov rcx, qword ptr [rcx]
0290DCFB  e8 90 e3 06 01                   call 0x397c090
0290DD00  c7 40 1c ff ff ff ff             mov dword ptr [rax + 0x1c], 0xffffffff
0290DD07  4d 85 f6                         test r14, r14
0290DD0A  74 0b                            je 0x290dd17
0290DD0C  49 8b 0e                         mov rcx, qword ptr [r14]
0290DD0F  e8 7c e3 06 01                   call 0x397c090
0290DD14  89 58 1c                         mov dword ptr [rax + 0x1c], ebx
0290DD17  48 8d 44 24 20                   lea rax, [rsp + 0x20]
0290DD1C  48 89 44 24 70                   mov qword ptr [rsp + 0x70], rax
0290DD21  4c 89 64 24 78                   mov qword ptr [rsp + 0x78], r12
0290DD26  48 8d 84 24 f0 00 00 00          lea rax, [rsp + 0xf0]
0290DD2E  48 89 84 24 80 00 00 00          mov qword ptr [rsp + 0x80], rax
0290DD36  66 0f 7f 74 24 50                movdqa xmmword ptr [rsp + 0x50], xmm6
0290DD3C  48 8d 4c 24 50                   lea rcx, [rsp + 0x50]
0290DD41  e8 ba ae 06 01                   call 0x3978c00
0290DD46  90                               nop 
0290DD47  e8 e4 aa 06 01                   call 0x3978830
0290DD4C  f6 40 30 01                      test byte ptr [rax + 0x30], 1
0290DD50  74 32                            je 0x290dd84
0290DD52  48 8b c8                         mov rcx, rax
0290DD55  e8 06 be 06 01                   call 0x3979b60
0290DD5A  48 8b 08                         mov rcx, qword ptr [rax]
0290DD5D  48 89 38                         mov qword ptr [rax], rdi
0290DD60  48 85 c9                         test rcx, rcx
0290DD63  74 0f                            je 0x290dd74
0290DD65  48 8b 09                         mov rcx, qword ptr [rcx]
0290DD68  e8 23 e3 06 01                   call 0x397c090
0290DD6D  c7 40 1c ff ff ff ff             mov dword ptr [rax + 0x1c], 0xffffffff
0290DD74  48 85 ff                         test rdi, rdi
0290DD77  74 0b                            je 0x290dd84
0290DD79  48 8b 0f                         mov rcx, qword ptr [rdi]
0290DD7C  e8 0f e3 06 01                   call 0x397c090
0290DD81  89 70 1c                         mov dword ptr [rax + 0x1c], esi
0290DD84  ff c3                            inc ebx
0290DD86  3b dd                            cmp ebx, ebp
0290DD88  0f 85 f2 fe ff ff                jne 0x290dc80
0290DD8E  44 8b ac 24 f8 00 00 00          mov r13d, dword ptr [rsp + 0xf8]
0290DD96  8b 8c 24 00 01 00 00             mov ecx, dword ptr [rsp + 0x100]
0290DD9D  48 8d 15 7c 1f 00 00             lea rdx, [rip + 0x1f7c]
0290DDA4  41 3b ed                         cmp ebp, r13d
0290DDA7  74 10                            je 0x290ddb9
0290DDA9  8b d9                            mov ebx, ecx
0290DDAB  f0 41 0f c1 1f                   lock xadd dword ptr [r15], ebx
0290DDB0  41 3b dd                         cmp ebx, r13d
0290DDB3  0f 8c 97 fe ff ff                jl 0x290dc50
0290DDB9  0f 28 b4 24 90 00 00 00          movaps xmm6, xmmword ptr [rsp + 0x90]
0290DDC1  48 81 c4 a8 00 00 00             add rsp, 0xa8
0290DDC8  41 5f                            pop r15
0290DDCA  41 5e                            pop r14
0290DDCC  41 5d                            pop r13
0290DDCE  41 5c                            pop r12
0290DDD0  5f                               pop rdi
0290DDD1  5e                               pop rsi
0290DDD2  5d                               pop rbp
0290DDD3  5b                               pop rbx
0290DDD4  c3                               ret 
