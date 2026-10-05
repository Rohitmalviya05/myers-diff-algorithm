import sys
from array import array

# array("i") stores the saved V rows using 4-byte integers.
# This keeps the same fast Myers backtracking idea while using much
# less memory than a Python dictionary for every saved row.


import sys
from array import array

# array("i") stores the saved V rows using 4-byte integers.
# This keeps the same fast Myers backtracking idea while using much
# less memory than a Python dictionary for every saved row.

def read_lines(path):
    """Read raw bytes and split only on the newline byte."""
    with open(path, "rb") as file:
        data = file.read()
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def myers_operations(a,b):
 a=list(a); b=list(b); n=len(a); m=len(b)
 if not n:return [('insert',x) for x in b]
 if not m:return [('delete',x) for x in a]
 offset=n+m+1; size=2*(n+m)+3
 v=[-2]*size; v[offset+1]=0
 trace=[]; end_d=0; found=False
 for d in range(n+m+1):
  trace.append(array('i', v[offset-d:offset+d+1]))
  for k in range(-d,d+1,2):
   idx=offset+k
   left=v[idx-1]; right=v[idx+1]
   left_cmp=-1 if left==-2 else left; right_cmp=-1 if right==-2 else right
   if k==-d or (k!=d and left_cmp<right_cmp):
    x=0 if right==-2 else right
   else:
    x=(0 if left==-2 else left)+1
   y=x-k
   while x<n and y<m and a[x]==b[y]: x+=1;y+=1
   v[idx]=x
   if x>=n and y>=m:
    end_d=d;found=True;break
  if found:break
 x=n;y=m; rev=[]
 for d in range(end_d,-1,-1):
  if d==0:
   while x>0 and y>0:
    rev.append(('equal',a[x-1]));x-=1;y-=1
   while x>0:rev.append(('delete',a[x-1]));x-=1
   while y>0:rev.append(('insert',b[y-1]));y-=1
   break
  previous=trace[d]; prev_d=d-1; prev_lo=-prev_d; trace_lo=-d; k=x-y
  def get(pk,default=-1):
   if pk<prev_lo or pk>prev_d:return default
   val=previous[pk-trace_lo]
   return default if val==-2 else val
  if k==-d or (k!=d and get(k-1,-1)<get(k+1,-1)): prev_k=k+1
  else: prev_k=k-1
  prev_x=get(prev_k,0); prev_y=prev_x-prev_k
  while x>prev_x and y>prev_y:
   rev.append(('equal',a[x-1]));x-=1;y-=1
  if x==prev_x:
   rev.append(('insert',b[y-1]));y-=1
  else:
   rev.append(('delete',a[x-1]));x-=1
 rev.reverse(); return rev


def delete_first(ops):
 out=[];i=0
 while i<len(ops):
  if ops[i][0]=='equal':out.append(ops[i]);i+=1;continue
  dels=[];ins=[]
  while i<len(ops) and ops[i][0]!='equal':
   (dels if ops[i][0]=='delete' else ins).append(ops[i]);i+=1
  out.extend(dels);out.extend(ins)
 return out

def myers_diff(a,b):return delete_first(myers_operations(a,b))


def format_ranges(ranges):
    if not ranges:
        return "."
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return ",".join(f"{start}-{end}" for start, end in merged)


def changed_ranges(old_line, new_line):
    """Run Myers on Unicode code points and return changed ranges."""
    old = list(old_line.decode("utf-8"))
    new = list(new_line.decode("utf-8"))
    operations = myers_diff(old, new)

    old_ranges = []
    new_ranges = []
    old_pos = 0
    new_pos = 0
    old_start = None
    new_start = None

    for operation, _ in operations:
        if operation == "equal":
            if old_start is not None:
                old_ranges.append((old_start, old_pos))
                old_start = None
            if new_start is not None:
                new_ranges.append((new_start, new_pos))
                new_start = None
            old_pos += 1
            new_pos += 1
        elif operation == "delete":
            if old_start is None:
                old_start = old_pos
            old_pos += 1
        else:
            if new_start is None:
                new_start = new_pos
            new_pos += 1

    if old_start is not None:
        old_ranges.append((old_start, old_pos))
    if new_start is not None:
        new_ranges.append((new_start, new_pos))

    return format_ranges(old_ranges), format_ranges(new_ranges)


def print_lines_diff(a, b):
    """Part A: print the line edit script."""
    output = sys.stdout.buffer
    for operation, line in myers_diff(a, b):
        if operation == "equal":
            prefix = b" "
        elif operation == "delete":
            prefix = b"-"
        else:
            prefix = b"+"
        output.write(prefix + line + b"\n")


def print_highlight(a, b):
    """Part B: print the line diff and character ranges."""
    operations = myers_diff(a, b)
    output = sys.stdout.buffer
    i = 0

    while i < len(operations):
        if operations[i][0] == "equal":
            output.write(b" " + operations[i][1] + b"\n")
            i += 1
            continue

        deletes = []
        inserts = []

        while i < len(operations) and operations[i][0] != "equal":
            operation, line = operations[i]
            if operation == "delete":
                deletes.append(line)
            else:
                inserts.append(line)
            i += 1

        for line in deletes:
            output.write(b"-" + line + b"\n")

        # Pair the first deletion with the first insertion, etc.
        for j, line in enumerate(inserts):
            output.write(b"+" + line + b"\n")
            if j < len(deletes):
                old_ranges, new_ranges = changed_ranges(deletes[j], line)
                output.write(
                    f"? {old_ranges} | {new_ranges}\n".encode("utf-8")
                )


def main():
    if len(sys.argv) != 4:
        print("Usage: python src/main.py lines A B", file=sys.stderr)
        print("   or: python src/main.py highlight A B", file=sys.stderr)
        return 2

    mode = sys.argv[1]
    file_a = sys.argv[2]
    file_b = sys.argv[3]

    try:
        a = read_lines(file_a)
        b = read_lines(file_b)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if mode == "lines":
        print_lines_diff(a, b)
        return 0

    if mode == "highlight":
        print_highlight(a, b)
        return 0

    print("error: mode must be 'lines' or 'highlight'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
