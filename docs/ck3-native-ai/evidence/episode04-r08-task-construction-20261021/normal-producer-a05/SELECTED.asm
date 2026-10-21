; exact selected RVA bytes instruction
28F614C 488bf2 mov rsi, rdx
28F6178 488baec0010000 mov rbp, qword ptr [rsi + 0x1c0]
28F6184 488bce mov rcx, rsi
28F6187 e814e2fcff call 0x28c43a0
28F618C 488b18 mov rbx, qword ptr [rax]
28F618F 4533c0 xor r8d, r8d
28F6192 488bd6 mov rdx, rsi
28F619A e811e13100 call 0x2c142b0
28F619F 488b08 mov rcx, qword ptr [rax]
28F61A2 4803cb add rcx, rbx
28F61A5 48894d28 mov qword ptr [rbp + 0x28], rcx
28F61CE 488d90b8030000 lea rdx, [rax + 0x3b8]
28F61D5 488d056c1ef101 lea rax, [rip + 0x1f11e6c]
28F6221 e85acb2c00 call 0x2bc2d80
28F623A 488bbc24a0010000 mov rdi, qword ptr [rsp + 0x1a0]
28F6258 4883b85804000000 cmp qword ptr [rax + 0x458], 0
28F6262 488b058f253c03 mov rax, qword ptr [rip + 0x33c258f]
28F6280 488d05a951f201 lea rax, [rip + 0x1f251a9]
28F62BC e80fa43800 call 0x2c806d0
28F62D9 488b9c24a0010000 mov rbx, qword ptr [rsp + 0x1a0]
28F62E1 4803df add rbx, rdi
28F62F5 e8a6133600 call 0x2c576a0
28F62FA 488b08 mov rcx, qword ptr [rax]
28F62FD 4803cb add rcx, rbx
28F6300 48894d30 mov qword ptr [rbp + 0x30], rcx
29095D0 488b4908 mov rcx, qword ptr [rcx + 8]
29095D4 e9874f0000 jmp 0x290e560
290FEF0 488b4110 mov rax, qword ptr [rcx + 0x10]
290FEF4 4c6300 movsxd r8, dword ptr [rax]
290FEF7 488b4108 mov rax, qword ptr [rcx + 8]
290FEFB 488b10 mov rdx, qword ptr [rax]
290FEFE 4a8b14c2 mov rdx, qword ptr [rdx + r8*8]
290FF02 e92962feff jmp 0x28f6130
2C13F8C 0f57c0 xorps xmm0, xmm0
2C13F8F 0f1101 movups xmmword ptr [rcx], xmm0
2C13FA5 0f8424020000 je 0x2c141cf
2C141D4 498bce mov rcx, r14
2C141D7 e8c401cbff call 0x28c43a0
2C141DF 488b08 mov rcx, qword ptr [rax]
2C141E2 48010b add qword ptr [rbx], rcx
2C1422D 4c8bc7 mov r8, rdi
2C14230 498bd6 mov rdx, r14
2C14238 e873000000 call 0x2c142b0
2C14240 488b08 mov rcx, qword ptr [rax]
2C14243 48010b add qword ptr [rbx], rcx
