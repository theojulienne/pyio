class LineStream(object):
	def __init__( self, stream ):
		self.stream = stream
		self.data = []
		self.newlines = 0
		
		self.lines = []
	
	def consume( self, num_bytes ):
		new_data = self.stream.read( num_bytes )
		self.newlines += new_data.count( '\n' )
		self.data.append( new_data )
		
		return self.newlines
	
	def _parse_lines( self ):
		combined = ''.join( self.data )
		lines = combined.split( '\n' )
		
		# every element except the last is a full line
		self.lines.extend( lines[:-1] )
		
		# the last element does not yet have a newline
		self.data = lines[-1:]
	
	def readline( self ):
		# if we have no prepared lines, try getting some from the data globs
		if len(self.lines) == 0:
			self._parse_lines( )
		
		if len(self.lines) > 0:
			self.newlines -= 1
			return self.lines.pop( 0 )
		else:
			return None # no more lines to read, consume more first
	
	def readlines( self ):
		# we want all the lines so far, so always parse everything
		self._parse_lines( )
		
		lines = self.lines
		self.lines = []
		self.newlines -= len(lines)
		return lines
	
	def fileno( self ):
		return self.stream.fileno( )