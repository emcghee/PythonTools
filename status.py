from argparse import ArgumentParser
from subprocess import Popen, PIPE
from tabulate import tabulate

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('--cs', '--cobaltstrike', action='store_true', help='Show cobalt strike servers grouped')
    parser.add_argument('--gp', '--gophish', action='store_true', help='Show gophish servers grouped')
    parser.add_argument('--nh', '--nighthawk', action='store_true', help='Show nighthawk servers grouped')
    parser.add_argument('--pwn', '--pwndrop', action='store_true', help='Show pwndrop servers grouped')
    parser.add_argument('--redir', '--redirector', action='store_true', help='Show redirector servers grouped')
    # parser.add_argument('--lab', action='store_true', help='Show lab servers grouped')
    parser.add_argument('--s1', '--stage1', action='store_true', help='Show stage1 servers grouped')
    parser.add_argument('--other', '--general', '--misc', '--miscellaneous', action='store_true', help='Show miscellaneous servers grouped')
    parser.add_argument('--all', '--grouped', action='store_true', help='Show all servers grouped')

    return parser.parse_args()

def main(args):
    showCS = args.cs
    showGP = args.gp
    showNH = args.nh
    showPWN = args.pwn
    showREDIR = args.redir
    # showLAB = args.lab
    showS1 = args.s1
    showOTHER = args.other
    showALL = args.all
    # and not showLAB
    showUNFORMATTED = not showCS and not showGP and not showNH and not showPWN and not showREDIR and not showS1 and not showOTHER and not showALL

    process = Popen("tailscale status", stdout=PIPE)
    process.wait()
    stdout = process.stdout.read().decode()
    stdoutSplit = stdout.split('\n')
    headers = ['IP', 'Hostname', 'OS', 'Connection Status']
    other = list()
    cobaltstrike = list()
    gophish = list()
    nighthawk = list()
    pwndrop = list()
    redir = list()
    # lab = list()
    s1 = list()
    unformatted = list()
    for line in stdoutSplit:
        line = line.strip()
        if not line or line[0] == '#':
            continue

        lineSplit = line.split(' ')
        # Remove empty elements
        lineSplit = [split for split in lineSplit if split]
        if len(lineSplit) >= 5:
            ip = lineSplit[0]
            hostname = lineSplit[1]
            os = lineSplit[3]
            status = ' '.join(lineSplit[4:])

            row = [ip, hostname, os, status]
            if showUNFORMATTED:
                unformatted.append(row)
                continue

            if hostname.startswith('cs-') or hostname.startswith('cs2n1-'):
                table = cobaltstrike

            elif hostname.startswith('gp-'):
                table = gophish

            elif hostname.startswith('nh-'):
                table = nighthawk

            elif hostname.startswith('pwn-'):
                table = pwndrop

            elif hostname.startswith('redir-'):
                table = redir

            # elif hostname.startswith('lab-'):
            #     table = lab

            elif hostname.startswith('s1-'):
                table = s1

            else:
                table = other
            table.append(row)
        else:
            print(f"[-] Unable to parse {line}")

    if showUNFORMATTED:
        print(tabulate(unformatted, headers=headers))
        return

    elif showALL:
        showCS = showGP = showNH = showPWN = showREDIR = showLAB = showOTHER = True

    output = str()
    if showCS and cobaltstrike:
        output += tabulate(cobaltstrike, headers=headers)
        output += "\n\n"

    if showGP and gophish:
        output += tabulate(gophish, headers=headers)
        output += "\n\n"

    if showNH and nighthawk:
        output += tabulate(nighthawk, headers=headers)
        output += "\n\n"

    if showPWN and pwndrop:
        output += tabulate(pwndrop, headers=headers)
        output += "\n\n"

    if showREDIR and redir:
        output += tabulate(redir, headers=headers)
        output += "\n\n"

    # if showLAB and lab:
    #     output += tabulate(lab, headers=headers)
    #     output += "\n\n"

    if showS1 and s1:
        output += tabulate(s1, headers=headers)
        output += "\n\n"

    if showOTHER and other:
        output += tabulate(other, headers=headers)
        output += "\n\n"

    output = output[:-2]
    print(output)

if __name__ == '__main__':
    args = parseArguments()
    main(args)
