
        ORG  7000H
        MEM  7000H

        CALL SKAKREK

;       NAVNE - INPUT

;       Clear nederste del af skaermen

        LD   HL,098AH
        LD   B,9
CLEAR1: PUSH BC
        LD   B,64
CLEAR2: LD   A,32
        LD   (HL),A
        INC  HL
        DJNZ CLEAR2
        POP  BC
        DJNZ CLEAR1
CUR:    EQU  0C29H
        LD   DE,098CH
        LD   HL,SPILH
        LD   BC,14
        LDIR
        LD   DE,09CCH
        LD   (CUR),DE
        LD   B,20
NAVN:   SCAL 7BH
        CP   13
        JR   Z,SND
        RST  30H
        DJNZ NAVN
SND:    LD   HL,SPILS
        LD   DE,098AH+28
        LD   BC,14
        LDIR
        LD   DE,09CAH+28
        LD   (CUR),DE
        LD   B,20
NAVN1:  SCAL 7BH
        CP   13
        JR   Z,FINITE
        RST  30H
        DJNZ NAVN1

;       RAMME OUTPUT
;       Overkant

FINITE: LD   HL,0A0AH+26
        LD   E,228
        LD   B,21
OV:     LD   (HL),E
        INC  HL
        DJNZ OV

;       Stolper
        LD   A,228
        LD   (0A0AH+25),A
        LD   (0A0AH+47),A
        LD   A,255
        LD   DE,40
        LD   HL,0A4AH-14
        LD   B,2
ST3:    PUSH BC
        ADD  HL,DE
        LD   B,3
ST2:    PUSH BC
        DEC  HL
        LD   B,3
ST1:    LD   (HL),A
        INC  HL
        INC  HL
        INC  HL
        DJNZ ST1
        POP  BC
        DJNZ ST2
        POP  BC
        DJNZ ST3


;       Total - tid output

        LD   DE,0ACAH+19
        LD   HL,TOTAL
        LD   BC,11
        LDIR
        LD   A,':'
        LD   (0B0AH+21),A
        LD   (0B0AH+26),A

;       PRIKKER OUTPUT

        LD   HL,0A4AH+6
        LD   (HL),210
        LD   HL,0A4AH+14
        LD   (HL),210
        LD   HL,0A8AH+6
        LD   (HL),201
        LD   HL,0A8AH+14
        LD   (HL),201
        LD   HL,0A4AH+32
        LD   (HL),237
        LD   HL,0A4AH+40
        LD   (HL),237
        LD   HL,0A8AH+32
        LD   (HL),246
        LD   HL,0A8AH+40
        LD   (HL),246

;       SORT'S NULLER
        LD   HL,0A4AH+26
        LD   IX,A0=9ALT
        CALL TALOUT
        LD   (TPALT+10),IX
        INC  HL
        INC  HL
        INC  HL
        LD   IX,A0=9ALT
        CALL TALOUT
        LD   (TPALT+8),IX
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        LD   IX,A0=9ALT
        CALL TALOUT
        LD   (TPALT+6),IX
        INC  HL
        INC  HL
        INC  HL
        LD   IX,A0=9ALT
        CALL TALOUT
        LD   (TPALT+4),IX
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        LD   IX,A0=9ALT
        CALL TALOUT
        LD   (TPALT+2),IX
        INC  HL
        INC  HL
        INC  HL
        LD   IX,A0=9ALT
        CALL TALOUT
        LD   (TPALT),IX

;       *********************************
;       *    U R  -  F U N K T I O N    *
;       *********************************

;       Initialisering

        LD   HL,0A4AH

;       Klokke - taeller

ROUND:  LD   B,10
        LD   DE,(STARTH)
        LD   (TPT=10),DE
T=10:   LD   (CTT=10),BC
        LD   IX,(TPT=10)
        CALL TALOUT
        LD   (TPT=10),IX
        INC  HL
        INC  HL
        INC  HL
        LD   B,10
        LD   DE,(STARTH)
        LD   (TPT=1),DE
T=1:    LD   (CTT=1),BC
        LD   IX,(TPT=1)
        CALL TALOUT
        LD   (TPT=1),IX
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        LD   B,6
        LD   DE,(STARTH)
        LD   (TPM=10),DE
M=10:   LD   (CTM=10),BC
        LD   IX,(TPM=10)
        CALL TALOUT
        LD   (TPM=10),IX
        INC  HL
        INC  HL
        INC  HL
        LD   B,10
        LD   DE,(STARTH)
        LD   (TPM=1),DE
M=1:    LD   (CTM=1),BC
        LD   IX,(TPM=1)
        CALL TALOUT
        LD   (TPM=1),IX
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        INC  HL
        LD   B,6
        LD   DE,(STARTH)
        LD   (TPS=10),DE
S=10:   LD   (CTS=10),BC
        LD   IX,(TPS=10)
        CALL TALOUT
        LD   (TPS=10),IX
        INC  HL
        INC  HL
        INC  HL
        LD   B,10
        LD   DE,(STARTH)
        LD   (TPS=1),DE
S=1:    LD   (CTS=1),BC
        LD   IX,(TPS=1)
        CALL TALOUT
        LD   (TPS=1),IX
        CALL PAUSE
        LD   BC,(CTS=1)
        DJNZ S=1
        DEC  HL
        DEC  HL
        DEC  HL
        LD   BC,(CTS=10)
        DJNZ S=10
        DEC  HL
        DEC  HL
        DEC  HL
        DEC  HL
        DEC  HL
        LD   BC,(CTM=1)
        DJNZ M=1
        DEC  HL
        DEC  HL
        DEC  HL
        LD   BC,(CTM=10)
        DEC  B
        JP   NZ,M=10
        DEC  HL
        DEC  HL
        DEC  HL
        DEC  HL
        DEC  HL
        LD   BC,(CTT=1)
        DEC  B
        JP   NZ,T=1
        DEC  HL
        DEC  HL
        DEC  HL
        LD   BC,(CTT=10)
        DEC  B
        JP   NZ,T=10
        JP   ROUND

;       *    TALOUT - RUTINE    *

TALOUT: PUSH HL
        PUSH BC
        LD   DE,62
        LD   B,2
        XOR  A
        SBC  HL,DE
TO2:    PUSH BC
        ADD  HL,DE
        LD   B,2
TO1:    LD   C,(IX+0)
        LD   (HL),C
        INC  HL
        INC  IX
        DJNZ TO1
        POP  BC
        DJNZ TO2
        POP  BC
        POP  HL
        RET

;       *    PAUSE - RUTINE    *

PAUSE:  LD   B,10
A1:     PUSH BC
        LD   B,82H
A2:     SCAL 62H
        CALL C,CHANGE
        DJNZ A2
        POP  BC
        DJNZ A1
        RET

;       *    CHANGE - RUTINE    *

CHANGE: LD   HL,TPS=1
        LD   DE,TPCHA
        CALL EXCH1
        LD   HL,TPALT
        LD   DE,TPS=1
        CALL EXCH1
        LD   HL,TPCHA
        LD   DE,TPALT
        CALL EXCH1
;Skaermpointer change
        LD   BC,(SPAD)
        LD   (SPC),BC
        LD   BC,(SPAL)
        LD   (SPAD),BC
        LD   BC,(SPC)
        LD   (SPAL),BC
;       Counter change
        LD   HL,CTS=1
        LD   DE,CTCHA
        CALL EXCH1
        LD   HL,CTALT
        LD   DE,CTS=1
        CALL EXCH1
        LD   HL,CTCHA
        LD   DE,CTALT
        CALL EXCH1
;       Start change
        LD   BC,(STARTH)
        LD   (STARTC),BC
        LD   BC,(STARTS)
        LD   (STARTH),BC
        LD   BC,(STARTC)
        LD   (STARTS),BC
        LD   HL,(SPAD)
        RET

;       EXCH1 - SUB SUB RUTINE

EXCH1:  LD   BC,12
        LDIR
        RET

;       **************************************
;       *    S K A K U R  -  R E K L A M E    *
;       ***************************************

;Clear Screen
SKAKREK:LD   A,0CH
        RST  30H

;Overkant - output

SADDO:  EQU  084EH
        LD   DE,SADDO
        LD   HL,GCO
        LD   BC,40
        LDIR

;Underkant - output

SADDU:  EQU  094EH
        LD   DE,SADDU
        LD   BC,40
        LDIR

;side - output

SADDV:  EQU  088EH
SADDH:  EQU  08B5H
        LD   IX,SADDV
        LD   DE,64
        RCAL SID
        LD   IX,SADDH
        RCAL SID
        JR   VID
SID:    LD   B,3
SIDX:   LD   A,(HL)
        LD   (IX+0),A
        ADD  IX,DE
        INC  HL
        DJNZ SIDX
        RET

;       SKAKUR - Output

SBO:    EQU  088EH
VID:    LD   IX,SBO
        LD   B,2
Y1:     PUSH BC
        INC  IX
        LD   B,3
Y2:     PUSH BC
        LD   DE,58
        LD   B,3
        LD   A,255
        CALL PAUSE1
BOG1:   PUSH BC
        LD   B,6
BOG2:   LD   A,(HL)
        LD   (IX+0),A
        INC  IX
        INC  HL
        DJNZ BOG2
        ADD  IX,DE
        POP  BC
        DJNZ BOG1
        LD   (REGC),IX
        LD   DE,(REGC)
        XOR  A          ;IX=IX-198
        LD   A,E        ; - " -
        SUB  186        ; - " -
        LD   E,A        ; - " -
        LD   A,D        ; - " -
        SBC  A,0        ; - " -
        LD   D,A        ; - " -
        LD   (REGC),DE
        LD   IX,(REGC)   ; - " -
        POP  BC
        DJNZ Y2
        POP  BC
        DJNZ Y1
        LD   A,255
        CALL PAUSE1
        CALL PAUSE1
        CALL PAUSE1
        CALL SKBO

;       PMJ - Output

        LD   HL,PMJD
        LD   IX,0A8EH
        LD   B,3
PRK2:   PUSH BC
        LD   B,16
PRK1:   LD   A,(HL)
        LD   (IX+0),A
        INC  IX
        INC  HL
        DJNZ PRK1
        LD   DE,48
        ADD  IX,DE
        POP  BC
        DJNZ PRK2
        CALL SKBO

;       Software - Output

        LD   IX,SOFT
        LD   HL,0A9EH
        LD   B,8
BO3:    PUSH BC
        LD   B,3
BO2:    PUSH BC
        LD   B,3
BO1:    LD   A,(IX+0)
        LD   (HL),A
        INC  HL
        INC  IX
        DJNZ BO1
        LD   DE,61
        ADD  HL,DE
        POP  BC
        DJNZ BO2
        CALL SKBO
        XOR  A
        LD   DE,189
        SBC  HL,DE
        POP  BC
        DJNZ BO3
        LD   B,5
        CALL SKBO
        LD   DE,0B4EH
        LD   HL,COPY
        LD   BC,38
        LDIR
        LD   A,255
        CALL PAUSE1
        CALL PAUSE1
        CALL PAUSE1
        CALL PAUSE1
        RET

;       Skakbraet - Output (SUBRUTINE)

SKBO:   PUSH IX
        PUSH HL
        LD   B,3
RAEK4:  PUSH BC
        LD   HL,SBR
        LD   B,2
RAEK3:  PUSH BC
        LD   IX,099EH
        LD   B,4
RAEK2:  PUSH BC
        LD   D,(HL)
        INC  HL
        LD   E,(HL)
        INC  HL
        LD   B,4
RAEK1:  LD   (IX+0),D
        INC  IX
        LD   (IX+0),E
        INC  IX
        DJNZ RAEK1
        LD   DE,38H
        ADD  IX,DE
        POP  BC
        DJNZ RAEK2
        LD   A,100
        CALL PAUSE1
        POP  BC
        DJNZ RAEK3
        POP  BC
        DJNZ RAEK4
        POP  HL
        POP  IX
        RET



;       PAUSE - SUBRUTINE  (1 sek.)
PAUSE1: PUSH BC
        LD   B,2
P3:     PUSH BC
        LD   B,A
P2:     PUSH BC
        LD   B,100
P1:     PUSH HL
        POP  HL
        DJNZ P1
        POP  BC
        DJNZ P2
        POP  BC
        DJNZ P3
        POP  BC
        RET
;       ***  GRAFIK - TAL  DATA  ***

A0=9:   DB   207,249,211,218
        DB   200,199,192,195
        DB   237,253,211,210
        DB   233,253,210,218
        DB   231,252,192,216
        DB   239,237,210,218
        DB   231,228,211,218
        DB   201,249,192,216
        DB   239,253,211,218
        DB   239,253,192,216
A0=9ALT:DB   240,198,236,229
        DB   247,248,255,252
        DB   210,194,236,237
        DB   214,194,237,229
        DB   216,195,255,231
        DB   208,210,237,229
        DB   216,219,236,229
        DB   246,198,255,231
        DB   208,194,236,229
        DB   208,194,255,231
TPS=1:  DW   A0=9
TPS=10: DW   A0=9
TPM=1:  DW   A0=9
TPM=10: DW   A0=9
TPT=1:  DW   A0=9
TPT=10: DW   A0=9
TPALT:  DW   A0=9ALT,A0=9ALT,A0=9ALT,A0=9ALT
        DW   A0=9ALT,A0=9ALT
TPCHA:  DS   12
SPAD:   DW   0A4AH+19
SPAL:   DW   0A4AH+45
SPC:    DS   2
CTS=1:  DB   0,10
CTS=10: DB   0,6
CTM=1:  DB   0,10
CTM=10: DB   0,6
CTT=1:  DB   0,10
CTT=10: DB   0,10
CTALT:  DB   0,10,0,6,0,10,0,6,0,10,0,10
CTCHA:  DS   12
STARTH: DW   A0=9
STARTS: DW   A0=9ALT
STARTC: DS   2
TOTAL:  DB   'Total-tid :'
SPILH:  DB   'Spiller HVID :'
SPILS:  DB   'Spiller SORT :'
;       Grafik-data
;       Overkant
GCO:    DB   239,217,203,217,203,217,203,217
        DB   203,217,203,217,203,217,203,217
        DB   203,217,203,217,203,217,203,217
        DB   203,217,203,217,203,217,203,217
        DB   203,217,203,217,203,217,203,253
;       Underkant
        DB   239,244,230,244,230,244,230,244
        DB   230,244,230,244,230,244,230,244
        DB   230,244,230,244,230,244,230,244
        DB   230,244,230,244,230,244,230,244
        DB   230,244,230,244,230,244,230,253
;       Siderne
        DB   215,239,215,250,253,250
;       Bogstav S
        DB   224,222,201,217,194,192
        DB   192,217,210,242,196,192
        DB   192,242,228,244,203,192
;       Bogstav K
        DB   200,255,225,222,201,192
        DB   192,255,251,196,192,192
        DB   224,255,196,217,230,192
;       Bogstav A
        DB   192,224,222,217,230,192
        DB   192,255,228,228,252,199
        DB   224,255,196,192,252,231
;       Bogstav K
        DB   200,255,225,222,201,192
        DB   192,255,251,196,192,192
        DB   224,255,196,217,230,192
;       Bogstav U
        DB   200,255,193,192,249,207
        DB   192,255,192,192,248,199
        DB   192,200,243,244,203,192
;       Bogstav R
        DB   192,200,255,201,217,230
        DB   192,192,255,210,250,197
        DB   192,224,255,196,216,231
;       Skakbraet tern
SBR:    DB   192,228,237,210,210,237,201,192
        DB   228,192,210,237,237,210,192,201
;       PMJ
PMJD:   DB   228,228,228,255,237,249,198,192
        DB   254,233,253,231,228,228,196,192
        DB   228,228,228,228,255,192,217,218
        DB   193,192,248,199,192,248,199,210
        DB   255,192,192,255,192,192,192,192
        DB   192,210,254,231,228,252,199,192
;       SOFTWARE - Bogstaver
SOFT:   DB  224,228,196,216,210,198,200,201,193
        DB  224,228,196,248,192,199,200,201,193
        DB  224,228,196,248,210,192,200,192,192
        DB  224,228,196,192,255,192,192,201,192
        DB  224,192,224,248,240,248,200,201,201
        DB  192,228,228,192,215,250,192,193,200
        DB  192,228,228,192,215,222,192,193,193
        DB  192,228,228,192,215,194,192,201,201
COPY:   DB   'september  1982    All rights '
        DB   'reserved'
REGC:   DS   2
        END






