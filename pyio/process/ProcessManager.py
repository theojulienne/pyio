from .Process import Process

class ProcessManager(object):
	def __init__( self ):
		self.processes = []
	
	def manage( self, process ):
		self.processes.append( process )
	
	def launch( self, *args, **kwargs ):
		process = Process( *args, **kwargs )
		self.manage( process )
		return process
	
	@property
	def running_processes( self ):
		return [ process for process in self.processes if process.returncode is None ]
	
	def terminate_all( self ):
		for process in self.running_processes:
			process.terminate( )
	
	def kill_all( self ):
		for process in self.running_processes:
			process.kill( )
	
	def signal_all( self, signal ):
		for process in self.running_processes:
			process.send_signal( signal )
	
	def poll( self ):
		terminations = []
		
		for process in self.running_processes:
			process.poll( )
			
			# of that recorded a termination, let the caller know
			if process.returncode is not None:
				terminations.append( process )
		
		return terminations
			