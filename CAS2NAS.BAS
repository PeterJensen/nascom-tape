REM Convert a NASCOM Cassette (CAS) Format File to NASSYS LOAD "L" (NAS) File:
REM ==========================================================================
REM for QBASIC.EXE or BASIC Compiler 7.1 (BC.EXE)
TYPE header
  blkstart AS INTEGER
  blklen   AS STRING * 1
  blkcount AS STRING * 1
  checksum AS STRING * 1
END TYPE

DEFINT A-Z
DIM h AS header
if command$="" then
  print "File "+command$+".CAS not found."
end if
cas$=command$+".CAS"
nas$=command$+".NAS"
OPEN cas$ FOR BINARY AS #1
f = 1
a$ = STRING$(256, 0): GET #1, , a$' read 256 padding for PLL sync
OPEN nas$ FOR OUTPUT AS #2

DO
  a$ = STRING$(5, 0): GET #1, , a$' read 00 ff ff ff ff
  IF a$ <> CHR$(0) + STRING$(4, 255) THEN GOTO caserr
  GET #1, , h
  IF f = 1 THEN f = 0: progbase = h.blkstart
  l = ASC(h.blklen): IF l = 0 THEN l = 256
  a$ = STRING$(l, 0): GET #1, , a$
  e$ = e$ + a$
  c$ = " ": GET #1, , c$' read checksum
  a$ = STRING$(10, 0): GET #1, , a$' read 10 * 0x00
  IF LEN(e$) >= 16386 THEN
    FOR i = 1 TO LEN(e$)
      IF (i - 1) MOD 8 = 0 THEN
        b$ = RIGHT$("0000" + HEX$(progbase), 4): PRINT #2, b$; " ";
        chksum = (VAL("&H" + MID$(b$, 1, 2)) + VAL("&H" + MID$(b$, 3, 2))) AND &HFF
        progbase = progbase + 8
      END IF
      c = ASC(MID$(e$, i, 1)): chksum = (chksum + c) AND &HFF
      PRINT #2, RIGHT$("00" + HEX$(c), 2); " ";
      IF (i - 1) MOD 8 = 7 THEN
        PRINT #2, RIGHT$("00" + HEX$(chksum), 2); CHR$(8); CHR$(8)
        chksum = 0
      END IF
    NEXT
    e$ = ""
  END IF
LOOP UNTIL ASC(h.blkcount) = 0

FOR i = 1 TO LEN(e$)
  IF (i - 1) MOD 8 = 0 THEN
    b$ = RIGHT$("0000" + HEX$(progbase), 4): PRINT #2, b$; " ";
    chksum = (VAL("&H" + MID$(b$, 1, 2)) + VAL("&H" + MID$(b$, 3, 2))) AND &HFF
    progbase = progbase + 8
  END IF
  c = ASC(MID$(e$, i, 1)): chksum = (chksum + c) AND &HFF
  PRINT #2, RIGHT$("00" + HEX$(c), 2); " ";
  IF (i - 1) MOD 8 = 7 THEN
    PRINT #2, RIGHT$("00" + HEX$(chksum), 2); CHR$(8); CHR$(8)
    chksum = 0
  END IF
NEXT

PRINT #2, ".": CLOSE #2: CLOSE #1
END

caserr:
 END

