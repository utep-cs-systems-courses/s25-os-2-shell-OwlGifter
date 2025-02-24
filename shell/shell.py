import os, sys

def executePipeCommand(command, background=False):
    commands = [cmd.strip() for cmd in command.split("|")]
    numCommands = len(commands)
    pipes = []

    for i in range(numCommands - 1):
        pipes.append(os.pipe())
    
    for i, cmd in enumerate(commands):
        pid = os.fork()
        if pid == 0:
            args = cmd.split()
            if i>0:
                os.dup2(pipes[i-1][0], 0)
            if i < numCommands - 1:
                os.dup2(pipes[i][1], 1)
            
            for read_end, write_end in pipes:
                os.close(read_end)
                os.close(write_end)
            
            handleRedirections(args)
            executable = findExe(args[0])
            if executable:
                os.execve(executable, args, os.environ)
            else:
                print(f"Command '{args[0]}' Not found/doesnt exist/plz check", file=sys.stderr)
        else:
            if i > 0:
                os.close(pipes[i-1][0])
            if i < numCommands - 1:
                os.close(pipes[i][1])
            if not background or i == numCommands -1:
                os.waitpid(pid, 0)

def handleRedirections(args):
    if ">" in args:
        idx = args.index(">") #find line with the > command
        filename = args[idx + 1]
        os.close(1) #close write on the console
        os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_TRUNC) #open write in the file
        args.pop(idx) #remove the > from the line and the filename as well
        args.pop(idx)
    if "<" in args:
        idx = args.index("<")
        filename = args[idx + 1]
        os.close(0) #close the read on console and the same as above but for writing
        os.open(filename, os.O_RDONLY)
        args.pop(idx)
        args.pop(idx)

def executeCommand(command, background=False):
    args = command.split()
    
    if args[0] == "cd":
        try:
            os.chdir(args[1] if len(args) > 1 else os.getenv("HOME", "/"))
        except FileNotFoundError:
            print(f"'cd {args[1]}' was not found/doesnt exist/might wanna check", file=sys.stderr)
        return
    
    pid = os.fork()
    if pid == 0:
        handleRedirections(args)
        executable = findExe(args[0])
        if executable:
            os.execve(executable, args, os.environ)
        else:
            print(f"Command '{args[0]}' Not found/doesnt exist/plz check")
            sys.exit()
    else:
        if not background:
            os.waitpid(pid, 0)


def findExe(command):
    if os.path.exists(command) and os.access(command, os.X_OK):
        return command
    for path in os.getenv("PATH", "").split(":"):
        fullPath = os.path.join(path, command)
        if os.path.exists(fullPath) and os.access(fullPath, os.X_OK):
            return fullPath
    return None

while True:
    try:
        prompt = os.getenv("PS1", "$ ")
        command = input(prompt).strip()

        if not command:
            continue
        if command == "exit":
            break

        background = command.endswith("&")
        if background:
            command = command[:-1].strip()
        if "|" in command:
            executePipeCommand(command, background)
        else:
            executeCommand(command, background)
    except KeyboardInterrupt:
        break
