import json
import requests

class BIMcloud():

	def __init__(self, url, client, user, password):
		self.url = url
		self.client = client
		self.user = user
		self.password = password
		self.auth = None

		self.connect()

	def connect(self):
		request = {
			'grant_type': 'password',
			'username': self.user,
			'password': self.password,
			'client_id': self.client
		}
		url = self.url + '/management/client/oauth2/token'
		response = requests.post(url, data=request, headers={ 'Content-Type': 'application/x-www-form-urlencoded' })
		if response.ok:
			self.auth = response.json()
			print (f'Connected to {self.url}')

	def get_projects(self, criterion={}, options={}):
		url = self.url + '/management/client/get-projects-by-criterion'
		response = requests.post(url, headers={'Authorization': f'Bearer {self.auth['access_token']}'}, params={}, json={**criterion, **options})
		# print(json.dumps(response.json(), indent = 4))
		return response.json() if response.ok else None
		