import subprocess

command = 'ps -e -o pid,psr,%cpu,cmd | grep \"python\"'
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
stdout, stderr = process.communicate()
# 处理输出结果
print("getNodeInfo: ", stdout)
lines = stdout.splitlines()
process_info = []
for line in lines:
    if "grep" in line:
        continue
    parts = line.split()
    if len(parts) >= 4:
        pid = parts[0]
        psr = parts[1]
        cpu = parts[2]
        cmd = parts[-1]
        process_info.append((pid, psr, cpu, cmd))