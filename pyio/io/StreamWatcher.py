from collections import namedtuple
import select
from select import kqueue, kevent

StreamEvent = namedtuple( 'StreamEvent', [ 'fd', 'stream', 'data', 'direction', 'num_bytes', 'eof' ] )

class StreamWatcher(object):
	def __init__( self ):
		self.kq = kqueue( )
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
		new_events = []
		if read:
			new_events.append( kevent( fd, filter=select.KQ_FILTER_READ, flags=select.KQ_EV_ADD ) )
		if write:
			new_events.append( kevent( fd, filter=select.KQ_FILTER_WRITE, flags=select.KQ_EV_ADD ) )
		
		# go!
		e = self.kq.control( new_events, 0, 0 )
		assert len(e) == 0, "Not expecting to receive any events while adding filters."
	
	def wait( self, timeout=None, max_events=4 ):
		r_events = self.kq.control( None, max_events, timeout )
		
		e = []
		
		for event in r_events:
			fd = event.ident
			if fd in self.fd_map:
				stream = self.stream_map[fd]
				data = self.fd_map[fd]
				
				direction = 'read' if event.filter == select.KQ_FILTER_READ else 'write'
				num_bytes = event.data
				eof = ( event.flags & select.KQ_EV_EOF != 0 )
				
				e.append( StreamEvent( fd, stream, data, direction, num_bytes, eof ) )
		
		return e
