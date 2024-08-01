import argparse
import json
import platform, subprocess
import requests
import time

from datetime import datetime, timedelta
from urllib.parse import quote, urlencode
from source.bimcloud import BIMcloud

class Explorer():

	def __init__(self, user, password, passcode, domain):

		self.user = user
		self.password = password
		self.passcode = passcode
		self.domain = domain

	@staticmethod
	def prep_project_uri(host, user, passcode, path):

		en_user = quote(f'{user}:{passcode}', safe=':+')
		en_host = quote(f'{host}', safe='')
		en_path = quote(f'{path}', safe='')
		uri = f'teamwork://{en_user}@{en_host}/{en_path}'.replace('.', '%2E')
		return uri

	@staticmethod
	def open_archicad_project(uri, version=25):

		app_path = 'C:\\Program Files\\GRAPHISOFT\\ARCHICAD '+version+'\\ARCHICAD.exe'
		subprocess.Popen (f'"{app_path}" "{uri}"', start_new_session=True, shell=platform.system())

	def make_queue(self, hostlist: list[str], time=3):

		date_back = int((datetime.now() - timedelta(days=time)).timestamp() * 1000)
		criterion = {
			'$and': [
				{'$eq': {'type': 'project'}},
				{'$eq': {'access': 'opened'}},
				{'$gte': {'$modifiedDate': date_back }},
			]
		}

		queue = []
		for host in hostlist:
			bim = BIMcloud(host, self.domain, self.user, self.password)
			for project in bim.get_projects(criterion):
				path = project['$path'].replace('Project Root/', '')
				uri = self.prep_project_uri(host, self.user, self.passcode, path)
				queue.append(uri)

		return queue if queue else None


if __name__ == "__main__":

	cmd = argparse.ArgumentParser()
	cmd.add_argument('-d', '--domain', required=True, help='Cloud tw domain')
	cmd.add_argument('-s', '--servers', required=True, help='Servers list, comma separated')
	cmd.add_argument('-u', '--user', required=True, help='User login')
	cmd.add_argument('-p', '--password', required=True, help='User password')
	cmd.add_argument('-c', '--passcode', required=True, help='User tw password hash')
	arg = cmd.parse_args()

	exp = Explorer(arg.user, arg.password, arg.passcode, arg.domain)
	queue = exp.make_queue([s for s in arg.servers.split(',') if s])

	print (len(queue))
	# print (queue[263])
	# exp.open_archicad_project(queue[263])

	# print(json.dumps(queue, indent = 4))