import pycurl
import threading
from StringIO import StringIO
import sys
import re
from urlparse import urlparse
from socket import gethostbyname
try:
	import Queue
except ImportError:
	import queue as Queue
found=[]
ips=[]
que=Queue.Queue(maxsize=20000)
fails=20
sem=threading.Semaphore()
class consumer(threading.Thread):
	def __init__(self,q):
		self.q=que
		threading.Thread.__init__(self)
	def request(self,url):
		for i in range(2):
			try:
				c=pycurl.Curl()
				vHtml=StringIO()
				c.setopt(c.URL,url)
				c.setopt(c.USERAGENT,"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0")
				c.setopt(c.WRITEFUNCTION,vHtml.write)
				c.perform()
				c.close()
				html=vHtml.getvalue()
				vHtml.close()
				return html
			except Exception,e:
				#print str(e)
				continue
		return ""
	def findLinks(self,html,currentUrl):
		tmp=[]
		rez=re.findall('\<li class=\"b_algo\"\>\<h2\>\<a href=\"(.*?)\"',html)
		for r in rez:
			parsed=urlparse(r)
			domain=parsed.netloc
			try:
				#ip=gethostbyname(domain)
                                pass
			except Exception,e:
				#print str(e)
				ip=''
			if domain not in tmp:
				tmp.append(domain)
		return tmp
	def process(self,ip):
		global found,sem
		print '[+] Search for '+ip
		html=self.request("http://www.bing.com/search?q=ip%3A+"+ip+"&qs=n&form=QBLH&pq=ip%3A+"+ip+"&count=50")
		#open('h.html','w').write(html)
		rez= self.findLinks(html,ip)
		if rez=="":
			if fails>0:
				fails-=1
			else:
				sys.exit(0)
		for r in rez:
			if r not in found and r!=ip:
                                sem.acquire()
				open("domains.txt",'a').write(r+"\n")
				sem.release()
				print '[!] '+r
				found.append(r)
	def run(self):
		while True:
			ip=self.q.get()
			self.process(ip)
			self.q.task_done()
try:
	found=open('domains.txt').read().splitlines()
except IOError:
	found=[]
try:
	ips=open('ips.txt').read().splitlines()
except IOError:
	print '[!!] File ips.txt not found'
	sys.exit(0)
for i in range(int(sys.argv[1])):
	try:
		t=consumer(que)
		t.daemon=True
		t.start()
	except Exception,e:
		print str(e)
		print '[!] Running only with %s threads'%i
		break
for i in ips:
	que.put(i)
que.join()