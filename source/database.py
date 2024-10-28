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
				self.deploy()

	def deploy(self):

		self.connection.execute(
			'CREATE TABLE IF NOT EXISTS jobs \
			(id char(8) primary key, tstamp integer)'
		)
		print (f'table "jobs" has been created')

		self.connection.execute(
			'CREATE TABLE IF NOT EXISTS projects \
			(id char (36) primary key, last_job_id char(8))'
		)
		print (f'table "projects" has been created')

		self.connection.execute(
			'CREATE TABLE IF NOT EXISTS metrics \
			(id char (8) primary key, name char(256), type char(8))'
		)
		print (f'table "metrics" has been created')
		params = [
			'file_name',
			'file_location',
			'file_project',
			'file_type',
			'file_size',
			'file_app_v',
			'file_status',
			'file_ctime',
			'file_mtime',
			'file_atime',
			'file_otime',
			'file_ptime',
			'file_jusers',
			'file_ausers',
		]
		query = [(self.get_short_uuid(), p) for p in params]
		self.cursor.executemany("INSERT INTO metrics (id, name, type) VALUES (?, ?, 'stat')", query)
		self.connection.commit()

		self.connection.execute(
			'CREATE TABLE IF NOT EXISTS metrics_delta \
			(id char (8), project_id char(8), metric_id char(8), value text, type char(4), job_id char(8))'
		)
		print (f'table "projects" has been created')

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

	def upsert_project(self, guid, job_id):

		self.cursor.execute("INSERT INTO projects (id, last_job_id) VALUES (?, ?) ON CONFLICT (id) DO UPDATE SET last_job_id = excluded.last_job_id", (guid.lower(), job_id))
		self.connection.commit()

	def get_project(self, project_id):

		query = self.cursor.execute('SELECT p.*, j.tstamp FROM projects p JOIN jobs j ON p.last_job_id = j.id WHERE p.id = ? ORDER BY j.tstamp DESC', (project_id,))
		result = query.fetchone()
		return result

	def get_metrics(self):

		query = self.cursor.execute('SELECT m.* FROM metrics m')
		result = query.fetchall()
		return result

	def get_metrics_from_deltas(self, project_id):

		query = '''
			SELECT DISTINCT m.name, md.metric_id, md.value, md.type, max(j.tstamp)
			FROM metrics_delta md
			JOIN jobs j ON md.job_id = j.id
			JOIN metrics m ON md.metric_id = m.id
			WHERE md.project_id = ? AND md.type != 'del'
			AND md.metric_id NOT IN (
				SELECT DISTINCT md.metric_id
				FROM metrics_delta md 
				JOIN jobs j ON md.job_id = j.id 
				join projects p on md.project_id = p.id
				WHERE md.project_id = ?
				AND md.type = 'del'
				AND j.id = p.last_job_id
			)
			GROUP BY md.metric_id;
		'''
		result = self.cursor.execute(query, (project_id, project_id))
		return result.fetchall()

	def add_metrics_delta(self, data):

		delta_id = self.get_short_uuid()
		self.cursor.executemany('INSERT INTO metrics_delta (id, project_id, metric_id, value, type, job_id) VALUES ("' + delta_id + '", ?, ?, ?, ?, ?)', data)
		self.connection.commit()
		return delta_id