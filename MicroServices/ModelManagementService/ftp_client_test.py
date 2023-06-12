from ftplib import FTP
ftp = FTP()
ftp.connect('localhost', 2121)
ftp.login(user="digiwind", passwd="digiwind_pw")
print(ftp.getwelcome())
ftp.dir()
ftp.close()