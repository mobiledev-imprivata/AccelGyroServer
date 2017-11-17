#!/usr/local/bin/python3

from flask import Flask, request, abort, make_response, jsonify, render_template, send_file
import os
import sys
import time

# Flask's default directory home for static files is static.
# Change it to . (current directory).

app = Flask(__name__, static_folder = '.', static_url_path = '')

RUN_FROM_DIR_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
LOGS_DIR_PATH = RUN_FROM_DIR_PATH + '/logs'

outfiles = {}

def timestamp():
	timestamp_string = time.strftime("%Y%m%d-%H%M%S")
	return timestamp_string

def write_to_file(message):
	# create directory if it doesn't already exist
	if not os.path.exists(LOGS_DIR_PATH):
		os.makedirs(LOGS_DIR_PATH)

	# print("Received message:\n%s" % message)

	lines = message.split('\n')
	# print(len(lines))

	timestamp_string = timestamp()
	outfiles = {}

	for line in lines:
		if not line: continue
		print(line)
		fields = line.split(':')
		# print(len(fields))
		# print(fields[0], fields[1], fields[2])

		event_type = fields[0]
		if fields[1] == 'header':
			filename = LOGS_DIR_PATH + '/' + timestamp_string + '_' + event_type + '.txt'
			print('opening', filename)
			outfiles[event_type] = open(filename, 'w')
			outfiles[event_type].write(fields[2] + '\n')
			continue

		text = fields[1] + ',' + fields[2] + '\n'

		if event_type != 'user':
			outfiles[event_type].write(text)
			continue

		# event type was user, so write it to all outfiles
		for outfile in outfiles.values():
			outfile.write(text)

	for outfile in outfiles.values():
		outfile.close()
		print("closing", outfile.name)
		size = os.stat(outfile.name).st_size
		print("size is", size)
		# remove files with no real data, just header
		if size <= 20:
			print("removing", outfile.name)
			os.remove(outfile.name)


def handle_parse_failure(e):
	abort(400)

@app.route('/')
def index():
	return "LogServer"

@app.route('/upload', methods=['POST'])
def upload():
	request.on_json_loading_failed = handle_parse_failure
	data = request.get_json()
	print("Received data:\n %s" % request.data)

	try:
		message = data['text']
		write_to_file(message)
	except KeyError:
		abort(500)

	response = make_response(jsonify({ 'status': 'OK'}), 200)
	response.mimetype = 'application/json'
	return response

# path converter to display files in browser

@app.route('/logs', defaults = {'req_path': ''})
@app.route('/logs/<path:req_path>')
def dir_listing(req_path):
	abs_path = os.path.join(LOGS_DIR_PATH, req_path)

	# Return 404 if the path doesn't exist
	if not os.path.exists(abs_path):
		return abort(404)

	# Check if path is a file and serve
	if os.path.isfile(abs_path):
		return send_file(abs_path)

	# Show directory contents
	files = sorted(os.listdir(LOGS_DIR_PATH))
	response = render_template('files.html', files = files)
	return response

def welcome():
	print("LogServer")
	print("To configure the port, specify as an argument:")
	print("\tpython accelgyro.py <port>")
	print("Defaults to 5000")

# Set debug = True to
#   1) create a debugging page upon an HHTP error
#   2) activate the automatic reloader (reload automatically when .py script changes)

if __name__ == '__main__':
	welcome()
	svrPort = 5000 if len(sys.argv) == 1 else int(sys.argv[1])
	print("Starting LogServer on port %s" % svrPort)
	app.run(host = '0.0.0.0', threaded = True, port = svrPort, debug = True)
