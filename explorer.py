import argparse
import json
import platform, subprocess
import requests

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
		user_info = quote(f'{user}:{passcode}', safe=':+')
		host_info = quote(f'{host}', safe='')
		path_info = quote(f'{path}', safe='')
		uri = f'teamwork://{user_info}@{host_info}/{path}'.replace('.', '%2E')
		return uri

	@staticmethod
	def open_archicad_project(uri, version=25):
		app_path = 'C:\\Program Files\\GRAPHISOFT\\ARCHICAD '+version+'\\ARCHICAD.exe'
		subprocess.Popen (f'"{app_path}" "{uri}"', start_new_session=True, shell=platform.system())

	def make_queue(self, hostlist: list[str]):
		queue = []
		for host in hostlist:
			bim = BIMcloud(host, self.domain, self.user, self.password)
			for project in bim.get_projects():
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

	print (queue[263])

	exp.open_archicad_project(queue[263])

	# print(json.dumps(queue, indent = 4))