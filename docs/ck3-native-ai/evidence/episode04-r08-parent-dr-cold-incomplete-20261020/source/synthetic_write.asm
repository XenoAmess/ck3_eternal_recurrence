PUBLIC SyntheticWrite
PUBLIC SyntheticWriteStart
PUBLIC SyntheticWriteAfter
.code
SyntheticWrite PROC
SyntheticWriteStart LABEL BYTE
 mov qword ptr [rcx],rdx
SyntheticWriteAfter LABEL BYTE
 ret
SyntheticWrite ENDP
END
