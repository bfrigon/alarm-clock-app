import os.path
import select


#=========================================================================================
class GPIO():
    
    PIN_INPUT   = "in"
    PIN_OUTPUT  = "out"
    PIN_LOW     = "low"
    PIN_HIGH    = "high"
    
    EDGE_NONE       = "none"
    EDGE_RISING     = "rising"
    EDGE_FALLING    = "falling"
    EDGE_BOTH       = "both"
    
    
    poll_edge = None
    fd_value = None
    
    
    #----------------------------------------------------------------------------
    def __init__( self, kernel_id, mode ):
        
        self.kernel_id = kernel_id
        
        
        ## Get the gpio sysfs path from kernel id ##
        if 0 <= kernel_id < 32:
            self.io_name = "A%d" % ( kernel_id )
            
        elif 32 <= kernel_id < 64:
            self.io_name = "B%d" % ( kernel_id - 32 )
            
        elif 64 <= kernel_id < 96:
            self.io_name = "C%d" % ( kernel_id - 64 )
            
        elif 96 <= kernel_id < 128:
            self.io_name = "D%d" % ( kernel_id - 96 )
        
        elif 128 <= kernel_id < 160:
            self.io_name = "E%d" % ( kernel_id - 128 )
        
        self.io_path = "/sys/class/gpio/pio" + self.io_name
        
        self.export()
        self.set_direction( mode )
    
    
    #----------------------------------------------------------------------------
    def __del__( self ):
        
        if self.poll_edge:
            self.poll_edge.unregister( self.fd_value )
            self.poll_edge.close()
    
    
    #----------------------------------------------------------------------------
    def export( self ):
        if os.path.exists( self.io_path ): 
            return
        
        try:
            f = open( '/sys/class/gpio/export', 'w' )
        
            f.write( str( self.kernel_id ) )
            f.close()
            
        except IOError: 
            raise IOError( "Unable to write to /sys/class/gpio/export for gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def unexport( self ):
        if not os.path.exists( self.io_path ): 
            return
            
        try:
            f = open( '/sys/class/gpio/unexport', 'w' )
            
            f.write( str( self.kernel_id ) )
            f.close()
            
        except IOError: 
            raise IOError( "Unable to write to /sys/class/gpio/unexport for gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def set_direction( self, mode ):
        
        if not mode in ( self.PIN_INPUT, self.PIN_OUTPUT, self.PIN_LOW, self.PIN_HIGH ):
            raise ValueError( "Invalid pin direction" )

        try:
            f = open( self.io_path + "/direction", "w" )
            
            f.write( mode )
            f.close()
            
        except IOError: 
            raise IOError( "Unable to set pin direction parameter for gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def get_direction( self ):

        try:
            f = open( self.io_path + "/direction", "r" )
            
            val = f.read()
            f.close()
            
            return val
            
        except IOError: 
            raise IOError( "Unable to read pin direction parameter for gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def set_edge( self, edge ):
        
        if not edge in ( self.EDGE_NONE, self.EDGE_RISING, self.EDGE_FALLING, self.EDGE_BOTH ):
            raise ValueError( "Invalid edge parameter" )

        try:
            f = open( self.io_path + "/edge", "w" )
            
            f.write( edge )
            f.close()
            
        except IOError: 
            raise IOError( "Unable to set edge parameter for gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def get_edge( self ):

        try:
            f = open( self.io_path + "/edge", "r" )
            
            val = f.read()
            f.close()
            
            return val
            
        except IOError: 
            raise IOError( "Unable to read pin edge parameter of gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def high( self ):
        self.write( 1 )
    
    
    #----------------------------------------------------------------------------
    def low( self ):
        self.write( 0 )
    
    
    #----------------------------------------------------------------------------
    def write( self, value ):
        
        try:

            f = open( self.io_path + "/value", "w" )
            
            f.write( str( value ) )
            f.close()
            
        except IOError: 
            raise IOError( "Unable to write value of gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def read( self ):
        
        try:
            f = open( self.io_path + "/value", "r" )
            
            val = int( f.read( 1 ) )
            f.close()
            
            return val
            
        except IOError: 
            raise IOError( "Unable to read value of gpio '%s'" % ( self.io_name ) )
    
    
    #----------------------------------------------------------------------------
    def wait_edge( self ):
        
        if self.poll_edge is None:
            self.fd_value = open( self.io_path + "/value", "r" )
            
            self.poll_edge = select.epoll()
            self.poll_edge.register( self.fd_value, select.EPOLLET )
            
        self.poll_edge.poll()
        