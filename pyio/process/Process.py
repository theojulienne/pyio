import subprocess
import os
import signal

_signal_map = {}
_signal_int_map = {}
for n,v in signal.__dict__.iteritems():
	if isinstance(v, int) and n == n.upper():
		_signal_map[v] = n
		_signal_int_map[n] = v

class Process(object):
	def __init__( self, cmd, **kwargs ):
		popen_kwargs = {
			'stdout': subprocess.PIPE,
			'stderr': subprocess.PIPE,
			'stdin': subprocess.PIPE,
			'bufsize': 0,
			'env': os.environ,
		}
		
		if 'env_update' in kwargs:
			popen_kwargs['env'].update( kwargs['env_update'] )
			del kwargs['env_update']
		
		popen_kwargs.update( kwargs )
		
		self.cmd = cmd
		self.popen_kwargs = popen_kwargs
		
		self._start( )
	
	@staticmethod
	def signal_name( signal ):
		if signal < 0:
			signal = -signal
		return _signal_map.get( signal, None )
	
	def start_again( self ):
		if self.proc is not None:
			if self.proc.returncode is None:
				raise Exception( 'Process has not yet terminated, cannot restart.' )
		
		self._start( )
	
	def _start( self ):
		self.proc = subprocess.Popen( self.cmd, **self.popen_kwargs )
	
	# the rest of the functions map to Popen() object functions, but slightly more useful
	
	@property
	def returncode( self ):
		return self.proc.returncode

	@property
	def stdin( self ):
		return self.proc.stdin

	@property
	def stdout( self ):
		return self.proc.stdout

	@property
	def stderr( self ):
		return self.proc.stderr

	@property
	def pid( self ):
		return self.proc.pid

	def terminate( self ):
		return self.proc.terminate( )
	
	def kill( self ):
		return self.proc.kill( )
	
	def send_signal( self, signal ):
		# be more friendly: map names to integers
		if isinstance(signal, basestring):
			if signal in _signal_int_map:
				signal = _signal_int_map[signal]
			elif 'SIG'+signal in _signal_int_map:
				signal = _signal_int_map['SIG' + signal]
		
		return self.proc.send_signal( signal )
	
	def communicate( self, input ):
		return self.proc.communicate( input )
	
	def wait( self ):
		self.proc.wait( )
		return self.proc.returncode # be more useful than Popen
	
	def poll( self ):
		self.proc.poll( )
		return self.proc.returncode # be more useful than Popen