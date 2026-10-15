028A6F50  40 57                            push rdi
028A6F52  48 83 ec 20                      sub rsp, 0x20
028A6F56  48 8b 81 b8 01 00 00             mov rax, qword ptr [rcx + 0x1b8]
028A6F5D  48 8b f9                         mov rdi, rcx
028A6F60  48 85 c0                         test rax, rax
028A6F63  74 53                            je 0x1428a6fb8
028A6F65  48 89 5c 24 30                   mov qword ptr [rsp + 0x30], rbx
028A6F6A  48 8b 58 50                      mov rbx, qword ptr [rax + 0x50]
028A6F6E  48 8b 00                         mov rax, qword ptr [rax]
028A6F71  48 03 d8                         add rbx, rax
028A6F74  74 3d                            je 0x1428a6fb3
028A6F76  48 8b 89 b0 01 00 00             mov rcx, qword ptr [rcx + 0x1b0]
028A6F7D  48 85 c9                         test rcx, rcx
028A6F80  74 31                            je 0x1428a6fb3
028A6F82  48 81 c1 f8 00 00 00             add rcx, 0xf8
028A6F89  4c 8b c7                         mov r8, rdi
028A6F8C  48 8b d3                         mov rdx, rbx
028A6F8F  e8 ac 7e fb ff                   call 0x14285ee40
028A6F94  48 8b 87 b0 01 00 00             mov rax, qword ptr [rdi + 0x1b0]
028A6F9B  48 8b 88 78 02 00 00             mov rcx, qword ptr [rax + 0x278]
028A6FA2  48 83 79 20 00                   cmp qword ptr [rcx + 0x20], 0
028A6FA7  74 0a                            je 0x1428a6fb3
028A6FA9  4c 8b c3                         mov r8, rbx
028A6FAC  33 d2                            xor edx, edx
028A6FAE  e8 cd 3e 14 ff                   call 0x1419eae80
028A6FB3  48 8b 5c 24 30                   mov rbx, qword ptr [rsp + 0x30]
028A6FB8  48 83 c4 20                      add rsp, 0x20
028A6FBC  5f                               pop rdi
028A6FBD  c3                               ret 
