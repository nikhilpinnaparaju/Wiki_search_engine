f = open('./index/offset','r')

offset = {}

while 1:
    line = f.readline()

    if not line:
        break

    else:
        row = line.strip().split(':')
    
    offset[row[0]] = int(row[1])

f.close()
f = open('./index/index','r')

f.seek(offset['udit'])
line = f.readline()

# for key in offset:
print(line)