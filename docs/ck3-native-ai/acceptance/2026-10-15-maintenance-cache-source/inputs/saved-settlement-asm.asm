028A6D10  41 57                            push r15
028A6D12  48 83 ec 40                      sub rsp, 0x40
028A6D16  48 8b 81 c0 01 00 00             mov rax, qword ptr [rcx + 0x1c0]
028A6D1D  4c 8b f9                         mov r15, rcx
028A6D20  48 85 c0                         test rax, rax
028A6D23  0f 84 1e 02 00 00                je 0x1428a6f47
028A6D29  4c 8b 40 28                      mov r8, qword ptr [rax + 0x28]
028A6D2D  48 89 5c 24 58                   mov qword ptr [rsp + 0x58], rbx
028A6D32  48 8b 98 c0 02 00 00             mov rbx, qword ptr [rax + 0x2c0]
028A6D39  48 2b 98 c8 02 00 00             sub rbx, qword ptr [rax + 0x2c8]
028A6D40  48 89 74 24 38                   mov qword ptr [rsp + 0x38], rsi
028A6D45  48 8b 70 30                      mov rsi, qword ptr [rax + 0x30]
028A6D49  48 89 7c 24 30                   mov qword ptr [rsp + 0x30], rdi
028A6D4E  49 8d 3c 30                      lea rdi, [r8 + rsi]
028A6D52  48 2b df                         sub rbx, rdi
028A6D55  48 85 db                         test rbx, rbx
028A6D58  7e 4a                            jle 0x1428a6da4
028A6D5A  48 8b 89 b0 01 00 00             mov rcx, qword ptr [rcx + 0x1b0]
028A6D61  48 85 c9                         test rcx, rcx
028A6D64  0f 84 ce 01 00 00                je 0x1428a6f38
028A6D6A  48 81 c1 f8 00 00 00             add rcx, 0xf8
028A6D71  4d 8b c7                         mov r8, r15
028A6D74  48 8b d3                         mov rdx, rbx
028A6D77  e8 c4 80 fb ff                   call 0x14285ee40
028A6D7C  49 8b 87 b0 01 00 00             mov rax, qword ptr [r15 + 0x1b0]
028A6D83  48 8b 88 78 02 00 00             mov rcx, qword ptr [rax + 0x278]
028A6D8A  48 83 79 20 00                   cmp qword ptr [rcx + 0x20], 0
028A6D8F  0f 84 a3 01 00 00                je 0x1428a6f38
028A6D95  4c 8b c3                         mov r8, rbx
028A6D98  33 d2                            xor edx, edx
028A6D9A  e8 e1 40 14 ff                   call 0x1419eae80
028A6D9F  e9 94 01 00 00                   jmp 0x1428a6f38
028A6DA4  48 85 ff                         test rdi, rdi
028A6DA7  0f 84 8b 01 00 00                je 0x1428a6f38
028A6DAD  48 89 6c 24 60                   mov qword ptr [rsp + 0x60], rbp
028A6DB2  48 8d 4c 24 50                   lea rcx, [rsp + 0x50]
028A6DB7  48 f7 db                         neg rbx
028A6DBA  4c 89 64 24 28                   mov qword ptr [rsp + 0x28], r12
028A6DBF  48 8b d3                         mov rdx, rbx
028A6DC2  4c 89 74 24 20                   mov qword ptr [rsp + 0x20], r14
028A6DC7  4c 8b cf                         mov r9, rdi
028A6DCA  e8 81 fd ff ff                   call 0x1428a6b50
028A6DCF  49 8b 8f b0 01 00 00             mov rcx, qword ptr [r15 + 0x1b0]
028A6DD6  45 33 e4                         xor r12d, r12d
028A6DD9  48 8b 28                         mov rbp, qword ptr [rax]
028A6DDC  45 8d 74 24 03                   lea r14d, [r12 + 3]
028A6DE1  48 85 c9                         test rcx, rcx
028A6DE4  0f 84 96 00 00 00                je 0x1428a6e80
028A6DEA  48 85 ed                         test rbp, rbp
028A6DED  0f 84 8d 00 00 00                je 0x1428a6e80
028A6DF3  48 81 c1 f8 00 00 00             add rcx, 0xf8
028A6DFA  4d 8b c7                         mov r8, r15
028A6DFD  48 8b d5                         mov rdx, rbp
028A6E00  e8 cb 80 fb ff                   call 0x14285eed0
028A6E05  49 8b 87 b0 01 00 00             mov rax, qword ptr [r15 + 0x1b0]
028A6E0C  48 8b 88 78 02 00 00             mov rcx, qword ptr [rax + 0x278]
028A6E13  48 8b 49 20                      mov rcx, qword ptr [rcx + 0x20]
028A6E17  48 85 c9                         test rcx, rcx
028A6E1A  74 64                            je 0x1428a6e80
028A6E1C  48 85 ed                         test rbp, rbp
028A6E1F  78 5f                            js 0x1428a6e80
028A6E21  48 81 c1 60 01 00 00             add rcx, 0x160
028A6E28  74 56                            je 0x1428a6e80
028A6E2A  48 8b 41 08                      mov rax, qword ptr [rcx + 8]
028A6E2E  48 3b c5                         cmp rax, rbp
028A6E31  7c 09                            jl 0x1428a6e3c
028A6E33  48 2b c5                         sub rax, rbp
028A6E36  48 89 41 08                      mov qword ptr [rcx + 8], rax
028A6E3A  eb 44                            jmp 0x1428a6e80
028A6E3C  4c 89 61 08                      mov qword ptr [rcx + 8], r12
028A6E40  45 8b c6                         mov r8d, r14d
028A6E43  49 8b d6                         mov rdx, r14
028A6E46  48 2b e8                         sub rbp, rax
028A6E49  0f 1f 80 00 00 00 00             nop dword ptr [rax]
028A6E50  48 8b 04 d1                      mov rax, qword ptr [rcx + rdx*8]
028A6E54  48 3b c5                         cmp rax, rbp
028A6E57  7d 1b                            jge 0x1428a6e74
028A6E59  48 2b e8                         sub rbp, rax
028A6E5C  4c 89 24 d1                      mov qword ptr [rcx + rdx*8], r12
028A6E60  41 ff c8                         dec r8d
028A6E63  48 83 ea 01                      sub rdx, 1
028A6E67  79 e7                            jns 0x1428a6e50
028A6E69  48 85 ed                         test rbp, rbp
028A6E6C  7e 12                            jle 0x1428a6e80
028A6E6E  48 29 69 18                      sub qword ptr [rcx + 0x18], rbp
028A6E72  eb 0c                            jmp 0x1428a6e80
028A6E74  49 63 c0                         movsxd rax, r8d
028A6E77  48 29 2c c1                      sub qword ptr [rcx + rax*8], rbp
028A6E7B  0f 1f 44 00 00                   nop dword ptr [rax + rax]
028A6E80  4c 8b cf                         mov r9, rdi
028A6E83  48 8d 4c 24 50                   lea rcx, [rsp + 0x50]
028A6E88  4c 8b c6                         mov r8, rsi
028A6E8B  48 8b d3                         mov rdx, rbx
028A6E8E  e8 bd fc ff ff                   call 0x1428a6b50
028A6E93  49 8b 8f b0 01 00 00             mov rcx, qword ptr [r15 + 0x1b0]
028A6E9A  48 8b 6c 24 60                   mov rbp, qword ptr [rsp + 0x60]
028A6E9F  48 8b 18                         mov rbx, qword ptr [rax]
028A6EA2  48 85 c9                         test rcx, rcx
028A6EA5  0f 84 83 00 00 00                je 0x1428a6f2e
028A6EAB  48 85 db                         test rbx, rbx
028A6EAE  74 7e                            je 0x1428a6f2e
028A6EB0  48 81 c1 f8 00 00 00             add rcx, 0xf8
028A6EB7  4d 8b c7                         mov r8, r15
028A6EBA  48 8b d3                         mov rdx, rbx
028A6EBD  e8 0e 80 fb ff                   call 0x14285eed0
028A6EC2  49 8b 87 b0 01 00 00             mov rax, qword ptr [r15 + 0x1b0]
028A6EC9  48 8b 88 78 02 00 00             mov rcx, qword ptr [rax + 0x278]
028A6ED0  48 8b 49 20                      mov rcx, qword ptr [rcx + 0x20]
028A6ED4  48 85 c9                         test rcx, rcx
028A6ED7  74 55                            je 0x1428a6f2e
028A6ED9  48 85 db                         test rbx, rbx
028A6EDC  78 50                            js 0x1428a6f2e
028A6EDE  48 81 c1 60 01 00 00             add rcx, 0x160
028A6EE5  74 47                            je 0x1428a6f2e
028A6EE7  48 8b 51 18                      mov rdx, qword ptr [rcx + 0x18]
028A6EEB  48 3b d3                         cmp rdx, rbx
028A6EEE  7c 09                            jl 0x1428a6ef9
028A6EF0  48 2b d3                         sub rdx, rbx
028A6EF3  48 89 51 18                      mov qword ptr [rcx + 0x18], rdx
028A6EF7  eb 35                            jmp 0x1428a6f2e
028A6EF9  4c 89 61 18                      mov qword ptr [rcx + 0x18], r12
028A6EFD  49 8b c6                         mov rax, r14
028A6F00  48 2b da                         sub rbx, rdx
028A6F03  48 8b 14 c1                      mov rdx, qword ptr [rcx + rax*8]
028A6F07  48 3b d3                         cmp rdx, rbx
028A6F0A  7d 1b                            jge 0x1428a6f27
028A6F0C  48 2b da                         sub rbx, rdx
028A6F0F  4c 89 24 c1                      mov qword ptr [rcx + rax*8], r12
028A6F13  41 ff ce                         dec r14d
028A6F16  48 83 e8 01                      sub rax, 1
028A6F1A  79 e7                            jns 0x1428a6f03
028A6F1C  48 85 db                         test rbx, rbx
028A6F1F  7e 0d                            jle 0x1428a6f2e
028A6F21  48 29 59 18                      sub qword ptr [rcx + 0x18], rbx
028A6F25  eb 07                            jmp 0x1428a6f2e
028A6F27  49 63 c6                         movsxd rax, r14d
028A6F2A  48 29 1c c1                      sub qword ptr [rcx + rax*8], rbx
028A6F2E  4c 8b 64 24 28                   mov r12, qword ptr [rsp + 0x28]
028A6F33  4c 8b 74 24 20                   mov r14, qword ptr [rsp + 0x20]
028A6F38  48 8b 74 24 38                   mov rsi, qword ptr [rsp + 0x38]
028A6F3D  48 8b 5c 24 58                   mov rbx, qword ptr [rsp + 0x58]
028A6F42  48 8b 7c 24 30                   mov rdi, qword ptr [rsp + 0x30]
028A6F47  48 83 c4 40                      add rsp, 0x40
028A6F4B  41 5f                            pop r15
028A6F4D  c3                               ret 
