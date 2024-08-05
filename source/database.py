import os
import sqlite3
import time
import uuid

class Database():

	def __init__(self, path):

		self.path = path
		self.connection = None
		self.cursor = None

		self.connect()

	def connect(self):

		connection = sqlite3.connect(self.path)
		if connection:
			self.connection = connection
			self.cursor = connection.cursor()
			print (f'Connected to {self.path}')

			try:
				self.cursor.execute('SELECT * FROM projects')
			except sqlite3.Error as e:
				print (f'{e}\ndeploying tables...')
				self.deploy()

	def deploy(self):

		self.connection.execute(
			'CREATE TABLE IF NOT EXISTS jobs \
			(id char(8) primary key, tstamp integer)'
		)

		self.connection.execute(
			'CREATE TABLE IF NOT EXISTS projects \
			(id char (36) primary key, job_id char(8))'
		)

	@staticmethod
	def get_short_uuid():
		return str(uuid.uuid4().hex[:8])

	@staticmethod
	def get_timestamp():
		return round(time.time())

	def add_job(self):

		job_id = self.get_short_uuid()
		self.cursor.execute("INSERT INTO jobs (id, tstamp) VALUES (?, ?)", (job_id, self.get_timestamp()))
		self.connection.commit()
		return job_id

	def add_project(self, guid, job_id):

		self.cursor.execute("INSERT INTO projects (id, job_id) VALUES (?, ?) ON CONFLICT (id) DO UPDATE SET job_id = excluded.job_id", (guid.lower(), job_id))
		self.connection.commit()

	def get_project(self, project_id):

		query = self.cursor.execute('SELECT p.*, j.tstamp FROM projects p JOIN jobs j ON p.job_id = j.id WHERE p.id = ? ORDER BY j.tstamp DESC', (project_id,))
		result = query.fetchone()
		return result if result else None