from pyio.process.Process import Process
from pyio.process.ProcessManager import ProcessManager
from pyio.io.StreamWatcher import StreamWatcher
from pyio.io.LineStream import LineStream

import shlex

manager = ProcessManager( )
streams = StreamWatcher( )

cmds = [
	# writes 1..5 to stdout
	('first ', "/bin/bash -c 'for i in 1 2 3 4 5; do echo $i; sleep 1; done'" ),
	# writes b1..b6 to stderr
	('second', "/bin/bash -c 'for i in b1 b2 b3 b4 b5 b6; do echo $i >&2; sleep 1; done'" ),
]

process_map = {}

# run each command in the background, and attach stdout/stderr
for name, cmd in cmds:
	args = shlex.split( cmd )
	process = manager.launch( args )
	
	process.stdin.close()
	
	streams.watch( LineStream( process.stdout ), (process, name, 'stdout') )
	streams.watch( LineStream( process.stderr ), (process, name, 'stderr') )
	
	process._example_name = name
	
	print name, 'started with pid', process.pid

# grab lines as they come, displaying them the user
while len(manager.running_processes) > 0:
	terminations = manager.poll( )

	events = streams.wait( )
	for event in events:
		if event.direction == 'read' and event.num_bytes > 0:
			num_lines = event.stream.consume( event.num_bytes )
			for line in event.stream.readlines():
				process, name, pipe = event.data
				print '%s [%s] %s' % ( name, pipe, line )

	if len(terminations) > 0:
		for process in terminations:
			print process._example_name, 'exited with status', process.returncode