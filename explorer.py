import argparse
import json
import platform, subprocess
import requests
import time

from datetime import datetime, timedelta
from urllib.parse import quote, urlencode

from source.archicad import ArchicadWrapper
from source.bimcloud import BIMcloud
from source.database import Database

def timer(f):
	def wrapper(*args, **kwargs):
		time_start = time.time()
		result = f(*args, **kwargs)
		time_end = time.time()
		duration = time_end - time_start
		return result, duration
	return wrapper


class Explorer():

	def __init__(self, user, password, passcode, domain):

		self.user = user
		self.password = password
		self.passcode = passcode
		self.domain = domain

		self.db = Database("C:\\Users\\i.yurasov\\Desktop\\dev\\archicad-project-explorer\\report.db")
		self.hosts = []

	@staticmethod
	def make_uri(host, user, passcode, path):

		en_user = quote(f'{user}:{passcode}', safe=':+')
		en_host = quote(f'{host}', safe='')
		en_path = quote(f'{path}', safe='')
		uri = f'teamwork://{en_user}@{en_host}/{en_path}'.replace('.', '%2E')
		return uri

	def add_hosts(self, hostlist: list[str]):

		for host in hostlist:
			cloud = BIMcloud(host, self.domain, self.user, self.password)
			if cloud:
				self.hosts.append(cloud)

	def run_queue(self, criterion={}, time=3):

		job = self.db.add_job()
		date_back = int((datetime.now() - timedelta(days=time)).timestamp() * 1000)
		criterion = {
			'$and': [
				{'$eq': {'type': 'project'}},
				{'$eq': {'access': 'opened'}},
				{'$gte': {'$modifiedDate': date_back }},
				# {'$eq': {'id': '4268A950-B701-491D-A805-7775A5A97C37' }},
			]
		}
		for host in self.hosts:
			for project in host.get_projects(criterion):
				pId = project['id'].lower()
				if not (project_db := self.db.get_project(pId)) or project_db[2]*1000 < project['$modifiedDate']:
					print (project['name'])
					uri = self.make_uri(host.url, self.user, self.passcode, project['$path'].replace('Project Root/', ''))
					archicad, otime = exp.open_archicad_project(uri)
					if archicad:
						self.db.add_project(pId, job)

	@timer
	def open_archicad_project(self, uri, version=25):

		def is_open_connect():
			connect = ArchicadWrapper()
			if connect.tapir:
				project = connect.tapir.run('GetProjectInfo', {})
				if project:
					print (f'Project "{project['projectName']}" has been opened successfully')
					return connect

		print(f'Opening specified project...')
		app_path = 'C:\\Program Files\\GRAPHISOFT\\ARCHICAD '+str(version)+'\\ARCHICAD.exe'
		app = subprocess.Popen (f'"{app_path}" "{uri}"', start_new_session=True, shell=platform.system())

		while not (connect := is_open_connect()):
			time.sleep(5)

		return connect

	def get_project_metrics(self, connect):

		data = []
		return data


if __name__ == "__main__":

	cmd = argparse.ArgumentParser()
	cmd.add_argument('-d', '--domain', required=True, help='Cloud tw domain')
	cmd.add_argument('-s', '--servers', required=True, help='Servers list, comma separated')
	cmd.add_argument('-u', '--user', required=True, help='User login')
	cmd.add_argument('-p', '--password', required=True, help='User password')
	cmd.add_argument('-c', '--passcode', required=True, help='User tw password hash')
	arg = cmd.parse_args()

	exp = Explorer(arg.user, arg.password, arg.passcode, arg.domain)
	exp.add_hosts([s for s in arg.servers.split(',') if s])
	exp.run_queue()

	# print(json.dumps(time, indent = 4))