from collections import namedtuple
import select

StreamEvent = namedtuple( 'StreamEvent', [ 'fd', 'stream', 'data', 'direction', 'num_bytes', 'eof' ] )

class StreamWatcher(object):
	def __init__( self ):
		if _best_backend is None:
			raise Exception( "No poll/queue backend could be found for your OS." )
		self.backend = _best_backend( )
		self.fd_map = {}
		self.stream_map = {}
	
	def watch( self, fd, data=None, read=True, write=False ):
		# allow python file-like objects that have a backing fd
		if hasattr(fd, 'fileno') and callable(fd.fileno):
			stream = fd
			fd = stream.fileno()
			self.stream_map[fd] = stream
		else:
			self.stream_map[fd] = None
		
		# associate user data with the fd
		self.fd_map[fd] = data
		
		# prepare any event filter additions
		if read:
			self.backend.watch_read( fd )
		if write:
			self.backend.watch_write( fd )
	
	def wait( self, timeout=None, max_events=4 ):
		return self.backend.wait(
			timeout=timeout,
			max_events=max_events,
			fd_data_map=self.fd_map,
			fd_stream_map=self.stream_map )

_best_backend = None

try:
	from select import kqueue, kevent
except ImportError:
	pass
else:
	class KQueueBackend(object):
		def __init__( self ):
			self.kq = kqueue( )

		def watch_read( self, fd ):
			event = kevent( fd, filter=select.KQ_FILTER_READ, flags=select.KQ_EV_ADD )
			self._add_events( [event] )

		def watch_write( self, fd ):
			event = kevent( fd, filter=select.KQ_FILTER_WRITE, flags=select.KQ_EV_ADD )
			self._add_events( [event] )
		
		def _add_events( self, new_events ):
			e = self.kq.control( new_events, 0, 0 )
			assert len(e) == 0, "Not expecting to receive any events while adding filters."
		
		def wait( self, timeout=None, max_events=4, fd_data_map={}, fd_stream_map={} ):
			r_events = self.kq.control( None, max_events, timeout )
			
			e = []
			
			for event in r_events:
				fd = event.ident
				if fd in fd_data_map:
					stream = fd_stream_map.get( fd, None )
					data = fd_data_map.get( fd, None )
				
					direction = 'read' if event.filter == select.KQ_FILTER_READ else 'write'
					num_bytes = event.data
					eof = ( event.flags & select.KQ_EV_EOF != 0 )
				
					e.append( StreamEvent( fd, stream, data, direction, num_bytes, eof ) )
		
			return e
	
	if _best_backend is None:
		_best_backend = KQueueBackend

try:
	from select import epoll
	from fcntl import ioctl
	import array
	import termios
except ImportError:
	pass
else:
	class EPollBackend(object):
		def __init__( self ):
			self.ep = epoll( )

		def watch_read( self, fd ):
			self.ep.register( fd, select.EPOLLIN )

		def watch_write( self, fd ):
			self.ep.register( fd, select.EPOLLOUT )
		
		def wait( self, timeout=None, max_events=None, fd_data_map={}, fd_stream_map={} ):
			if max_events is None:
				max_events = -1
			if timeout is None:
				timeout = -1
			
			r_events = self.ep.poll( timeout, max_events )
			
			e = []
			
			for fd, event in r_events:
				if fd in fd_data_map:
					buf = array.array( 'i', [0] )
					ioctl( fd, termios.FIONREAD, buf, 1 )
					
					stream = fd_stream_map.get( fd, None )
					data = fd_data_map.get( fd, None )
					
					num_bytes = buf[0]
					eof = ( event & (select.EPOLLHUP | select.EPOLLERR) != 0 )
					
					if event & select.EPOLLIN != 0:
						e.append( StreamEvent( fd, stream, data, 'read', num_bytes, eof ) )
					if event & select.EPOLLOUT != 0:
						e.append( StreamEvent( fd, stream, data, 'write', num_bytes, eof ) )
		
			return e
	
	if _best_backend is None:
		_best_backend = EPollBackend
