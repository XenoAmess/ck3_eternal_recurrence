03F909F0  48 89 5c 24 18                   mov qword ptr [rsp + 0x18], rbx
03F909F5  57                               push rdi
03F909F6  48 83 ec 20                      sub rsp, 0x20
03F909FA  48 8b d9                         mov rbx, rcx
03F909FD  48 8b fa                         mov rdi, rdx
03F90A00  b9 01 00 00 00                   mov ecx, 1
03F90A05  33 c0                            xor eax, eax
03F90A07  f0 0f b1 4b 60                   lock cmpxchg dword ptr [rbx + 0x60], ecx
03F90A0C  0f 85 c8 00 00 00                jne 0x3f90ada
03F90A12  48 89 74 24 38                   mov qword ptr [rsp + 0x38], rsi
03F90A17  e8 94 13 29 00                   call 0x4221db0
03F90A1C  48 8b f0                         mov rsi, rax
03F90A1F  e8 ac 58 13 00                   call 0x40c62d0
03F90A24  48 81 fe 80 96 98 00             cmp rsi, 0x989680
03F90A2B  75 06                            jne 0x3f90a33
03F90A2D  48 6b c0 64                      imul rax, rax, 0x64
03F90A31  eb 1e                            jmp 0x3f90a51
03F90A33  48 99                            cqo 
03F90A35  48 f7 fe                         idiv rsi
03F90A38  48 8b c8                         mov rcx, rax
03F90A3B  48 69 c2 00 ca 9a 3b             imul rax, rdx, 0x3b9aca00
03F90A42  48 69 c9 00 ca 9a 3b             imul rcx, rcx, 0x3b9aca00
03F90A49  48 99                            cqo 
03F90A4B  48 f7 fe                         idiv rsi
03F90A4E  48 03 c1                         add rax, rcx
03F90A51  48 89 43 70                      mov qword ptr [rbx + 0x70], rax
03F90A55  b8 ff ff ff ff                   mov eax, 0xffffffff
03F90A5A  f0 0f c1 07                      lock xadd dword ptr [rdi], eax
03F90A5E  48 8b 4b 38                      mov rcx, qword ptr [rbx + 0x38]
03F90A62  48 8b 74 24 38                   mov rsi, qword ptr [rsp + 0x38]
03F90A67  48 85 c9                         test rcx, rcx
03F90A6A  74 7b                            je 0x3f90ae7
03F90A6C  48 8b 01                         mov rax, qword ptr [rcx]
03F90A6F  ff 50 10                         call qword ptr [rax + 0x10]
03F90A72  b8 02 00 00 00                   mov eax, 2
03F90A77  87 43 60                         xchg dword ptr [rbx + 0x60], eax
03F90A7A  e8 31 13 29 00                   call 0x4221db0
03F90A7F  48 8b f8                         mov rdi, rax
03F90A82  e8 49 58 13 00                   call 0x40c62d0
03F90A87  48 81 ff 80 96 98 00             cmp rdi, 0x989680
03F90A8E  75 06                            jne 0x3f90a96
03F90A90  48 6b c0 64                      imul rax, rax, 0x64
03F90A94  eb 1e                            jmp 0x3f90ab4
03F90A96  48 99                            cqo 
03F90A98  48 f7 ff                         idiv rdi
03F90A9B  48 8b c8                         mov rcx, rax
03F90A9E  48 69 c2 00 ca 9a 3b             imul rax, rdx, 0x3b9aca00
03F90AA5  48 69 c9 00 ca 9a 3b             imul rcx, rcx, 0x3b9aca00
03F90AAC  48 99                            cqo 
03F90AAE  48 f7 ff                         idiv rdi
03F90AB1  48 03 c1                         add rax, rcx
03F90AB4  48 2b 43 70                      sub rax, qword ptr [rbx + 0x70]
03F90AB8  0f 57 c0                         xorps xmm0, xmm0
03F90ABB  f2 48 0f 2a c0                   cvtsi2sd xmm0, rax
03F90AC0  b0 01                            mov al, 1
03F90AC2  f2 0f 5e 05 5e 5d a6 00          divsd xmm0, qword ptr [rip + 0xa65d5e]
03F90ACA  f2 0f 11 43 68                   movsd qword ptr [rbx + 0x68], xmm0
03F90ACF  48 8b 5c 24 40                   mov rbx, qword ptr [rsp + 0x40]
03F90AD4  48 83 c4 20                      add rsp, 0x20
03F90AD8  5f                               pop rdi
03F90AD9  c3                               ret 
03F90ADA  48 8b 5c 24 40                   mov rbx, qword ptr [rsp + 0x40]
03F90ADF  32 c0                            xor al, al
03F90AE1  48 83 c4 20                      add rsp, 0x20
03F90AE5  5f                               pop rdi
03F90AE6  c3                               ret 
03F90AE7  e8 0c fd 28 00                   call 0x42207f8
03F90AEC  cc                               int3 
