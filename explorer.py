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

	@staticmethod
	def prep_project_uri(host, user, passcode, path):

		en_user = quote(f'{user}:{passcode}', safe=':+')
		en_host = quote(f'{host}', safe='')
		en_path = quote(f'{path}', safe='')
		uri = f'teamwork://{en_user}@{en_host}/{en_path}'.replace('.', '%2E')
		return uri

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

	def make_queue(self, hostlist: list[str], time=3, criterion={}):

		date_back = int((datetime.now() - timedelta(days=time)).timestamp() * 1000)
		criterion = {
			'$and': [
				{'$eq': {'type': 'project'}},
				{'$eq': {'access': 'opened'}},
				{'$gte': {'$modifiedDate': date_back }},
			]
		}
		queue = [
			(
				self.prep_project_uri(host, self.user, self.passcode, project['$path'].replace('Project Root/', '')),
				project['id'].lower()
			)
	        for host in hostlist
	        for project in BIMcloud(host, self.domain, self.user, self.password).get_projects(criterion)
	        if not (project_db := self.db.get_project(project['id'].lower())) or project_db[2] < project['$modifiedDate']
		]
		return queue or None

	def run_queue(self, queue):

		for q in queue:
			metrics = {}
			archicad, otime = exp.open_archicad_project(q[0])
			if archicad:
				metrics = self.get_project_metrics(archicad)

	def get_project_metrics(self, connect):

		print (otime)

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
	queue = exp.make_queue([s for s in arg.servers.split(',') if s])
	exp.run_queue(queue)

	# print(json.dumps(time, indent = 4))