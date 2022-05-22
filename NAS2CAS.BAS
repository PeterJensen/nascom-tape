rem nas2cas: convert a nas file to  a cas file

TYPE header
  blkstart AS INTEGER
  blklen   AS STRING * 1
  blkcount AS STRING * 1
  checksum AS STRING * 1
END TYPE
defint A-Z

dim h as header
if command$="" goto usage
on error goto notfound
open command$+".nas" for input as #1
on error goto 0 ' nas2cas
open command$+".cas" for binary as #2

' write 256 * 0x00
a$=string$(256,0)
put #2,,a$

h.blkstart=-1
' pass 1 to read how much to convert
while not eof(1)
  line input #1,a$: a$=ltrim$(a$)
  if left$(a$,1)<>"." and left$(a$,1) <> "T" then
    if h.blkstart=-1 then  h.blkstart=val("&H"+left$(a$,4)):st$=hex$(h.blkstart)
    for i=1 to 8
      buf$=buf$+chr$(val("&H"+mid$(a$, i*3+3,2)))
    next   
    if len(buf$)=256 then
      h.blkcount=chr$(asc(h.blkcount)+1)
      buf$=""
    end if
    se=val("&H"+left$(a$,4))
  endif
wend
' reopen again
close #1:open command$+".nas" for input as #1
if len(buf$)=0 then
  h.blkcount=chr$(asc(h.blkcount)-1)
end if
buf$=""
en$=hex$(se+8)
while not eof(1)
  line input #1,a$: a$=ltrim$(a$)
  if left$(a$,1)<>"." and left$(a$,1) <> "T" then
    for i=1 to 8
      buf$=buf$+chr$(val("&H"+mid$(a$, i*3+3,2)))
    next   
  endif
  if len(buf$)=256 then
    ' output a block, first the header
    a$=chr$(0)+string$(4,&Hff): put #2,,a$
    h.blklen=chr$(0)
    h.checksum=chr$(((h.blkstart \ 256) + (h.blkstart and &Hff) + asc(h.blkcount) +asc(h.blklen)) and &Hff)
    put #2,,h
    h.blkstart=h.blkstart+&H100
    h.blkcount=chr$(asc(h.blkcount)-1 and &hFF)
    ' now the data
    put #2,,buf$
    ' output checksum
    c=0:for i=1 to 256: c=(c+asc(mid$(buf$,i,1))) and &Hff:next:s$=chr$(c)
    put #2,,s$
    buf$=""
    a$=string$(10,0):put #2,,a$
  end if
wend
' output last block, first the header
if len(buf$) > 0 then
  a$=chr$(0)+string$(4,&Hff): put #2,,a$

  h.blklen=chr$(len(buf$))
  h.checksum=chr$(((h.blkstart \ 256) + (h.blkstart and &Hff) + asc(h.blkcount) +asc(h.blklen)) and &Hff)
  put #2,,h
  ' now the data
  put #2,,buf$
  ' output checksum
  c=0:for i=1 to len(buf$):c=(c+asc(mid$(buf$,i,1))) and &Hff:next:s$=chr$(c)
  put #2,,s$
  a$=string$(10,0):put #2,,a$
end if
print chr$(4)+"O:";command$;":";st$; " ";en$;" ";st$
close #2: close #1
end
usage:
  print "nas2cas nas_file_without_extention."
  end
nas2cas:
  print "Error ";err; " in nas2cas."
  end

notfound:
  print "File "; command$; ".nas not found."
  end
