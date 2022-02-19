import sys
import requests
import threading
from queue import Queue
from bs4 import BeautifulSoup
from urllib.parse import urljoin


VERBOSE = True
MAX_ALLOWED_SUBDOMAINS = 1000


def get_js_links(domain):
	try:
		url = "http://" + domain
		if VERBOSE:
			print(f' * HTTP request to "{url}"')

		response = requests.get(url, allow_redirects=True, timeout=10)
		
		if VERBOSE:
			print(f' * HTTP response "{response.status_code}" at "{url}"')
	except:
		if VERBOSE:
			print(f' * HTTP FAILED AT "{url}"')

		return []

	soup = BeautifulSoup(response.text, "html.parser")


	script_links = []
	for script in soup.find_all("script"):
		if script.attrs.get("src"):
			if "//" in script.attrs.get("src")[:5]:
				script_url = script.attrs.get("src")
				if "http://" not in script_url:
					script_url = "http:" + script.attrs.get("src")

			else:
				script_url = urljoin(response.url, script.attrs.get("src"))
			
			script_links.append(script_url)

	if VERBOSE:
		print(f' * Found {len(script_links)} JS links at "{response.url}"')

	return script_links


def threader():
	global q
	#TODO : add mechanism to clear cache to reduce memory usage
	uri_cache = {}

	while q.qsize():
		cached = False
		target = q.get()
		if "://" in target:
			try:
				if VERBOSE:
					print(f' * HTTP request to "{target}"')

				#cache check
				if not uri_cache.get(target):
					response = requests.get(target, timeout=5)
					uri_cache[target] = 1

				else:
					cached = True
					print(f'CACHED: {target}')

				if VERBOSE:
					print(f' * HTTP response "{response.status_code}" at "{target}"')

			except Exception as e:
				pass

			if not cached:
				data     = response.text
				filename = target.replace("/", "_").split("?")[0].split("#")[0].split("&")[0]

				with open(f'./files/{filename}', 'w+') as file:
					file.write(data)


			q.task_done()


		else:
			links = get_js_links(target)
			for link in links: q.put(link)
			q.task_done()

		

def findall(domains_file, threadcount=30):
	global q
	q = Queue()
	domain_count = len([q.put(x.strip()) for x in open(domains_file).readlines()][:MAX_ALLOWED_SUBDOMAINS])

	if domain_count < threadcount:
		threadcount = len(subdomains)

	for x in range(threadcount):
		t = threading.Thread(target=threader)
		t.start()

	q.join()


findall(sys.argv[1])
