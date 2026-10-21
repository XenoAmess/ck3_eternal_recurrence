; RVA bytes instruction; all from retained .4 spans
29676F2 FF5010 call [rax+10h] ; pre
29676FB FF5020 call [rax+20h]
2967703 740A je 296770F
2967708 E8B3000000 call 29677C0 ; true
2967712 FF5008 call [rax+8] ; false
296771B FF5018 call [rax+18h] ; post
29677E5 488BF9 mov rdi,rcx
29678F2 FF5008 call [rax+8]
2989BF0 8B5110 mov edx,[rcx+10h]
2989BF6 488B4918 mov rcx,[rcx+18h]
2989BFA 48FF6008 jmp [rax+8]
110CD00 488B01 mov rax,[rcx]
110CD03 48FF6010 jmp [rax+10h]
22A0E6D 83460818 add dword [rsi+8],24
22A1125 488B8EA0000000 mov rcx,[rsi+A0h]
22A112C 0FB681F83A0300 movzx eax,byte [rcx+33AF8h]
22A1133 FEC8 dec al
22A1135 2401 and al,1
22A1137 8881F83A0300 mov [rcx+33AF8h],al
22A1427 488B8EA0000000 mov rcx,[rsi+A0h]
22A142E 4881C148EE0200 add rcx,2EE48h
22A1438 FF5018 call [rax+18h]
