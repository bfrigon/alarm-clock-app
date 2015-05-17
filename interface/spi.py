import time
import ctypes
from struct import pack
from struct import unpack
from fcntl import ioctl
from ioctl_numbers import _IOR, _IOW
from gpio import GPIO



SPI_IOC_MAGIC   = ord("k")

SPI_CPHA    = 0x01
SPI_CPOL    = 0x02


# Read / Write of SPI mode (SPI_MODE_0..SPI_MODE_3)
SPI_IOC_RD_MODE          = _IOR(SPI_IOC_MAGIC, 1, "=B")
SPI_IOC_WR_MODE          = _IOW(SPI_IOC_MAGIC, 1, "=B")

# Read / Write SPI bit justification
SPI_IOC_RD_LSB_FIRST     = _IOR(SPI_IOC_MAGIC, 2, "=B")
SPI_IOC_WR_LSB_FIRST     = _IOW(SPI_IOC_MAGIC, 2, "=B")

# Read / Write SPI device word length (1..N)
SPI_IOC_RD_BITS_PER_WORD = _IOR(SPI_IOC_MAGIC, 3, "=B")
SPI_IOC_WR_BITS_PER_WORD = _IOW(SPI_IOC_MAGIC, 3, "=B")

# Read / Write SPI device default max speed hz
SPI_IOC_RD_MAX_SPEED_HZ  = _IOR(SPI_IOC_MAGIC, 4, "=I")
SPI_IOC_WR_MAX_SPEED_HZ  = _IOW(SPI_IOC_MAGIC, 4, "=I")

def SPI_IOC_MESSAGE(size):
    return _IOW(SPI_IOC_MAGIC, 0, "=" + ("QQIIHBBI" * size))



#=========================================================================================
class SPI:

    SPI_MODE_0  = (0|0)
    SPI_MODE_1  = (0|SPI_CPHA)
    SPI_MODE_2  = (SPI_CPOL|0)
    SPI_MODE_3  = (SPI_CPOL|SPI_CPHA)
    
    SPI_CS_HIGH     = 0x04
    SPI_LSB_FIRST   = 0x08
    SPI_3WIRE       = 0x10
    SPI_LOOP        = 0x20
    SPI_NO_CS       = 0x40
    SPI_READY       = 0x80
    
    
    #----------------------------------------------------------------------------
    def __init__( self, bus, client, mode = SPI_MODE_0, speed = 5000000 ):
        
        self.speed = speed
        self.mode = mode
        self.delay = 0
        self.bpw = 8
        
        dev = "/dev/spidev%d.%d" % ( bus, client )
        
        self.handle = open( dev, "w+" )
        
        self.set_mode( mode )
        self.set_speed( speed )
    
    
    #----------------------------------------------------------------------------
    def __del__( self ):
        self.handle.close()
    
    
    #----------------------------------------------------------------------------
    def set_mode( self, mode ):
        p = pack("=B", mode)

        ioctl(self.handle, SPI_IOC_RD_MODE, p)
        ioctl(self.handle, SPI_IOC_WR_MODE, p)

        self.mode = mode
    
    
    #----------------------------------------------------------------------------
    def set_speed( self, speed ):
        p = pack("=I", speed)

        ioctl(self.handle, SPI_IOC_RD_MAX_SPEED_HZ, p)
        ioctl(self.handle, SPI_IOC_WR_MAX_SPEED_HZ, p)
        
        self.speed = speed
    
    
    #----------------------------------------------------------------------------
    def set_bpw( self, bpw ):
        p = pack("=B", bpw)

        ioctl(self.handle, SPI_IOC_RD_BITS_PER_WORD, p)
        ioctl(self.handle, SPI_IOC_WR_BITS_PER_WORD, p)

        self.bpw = bpw
    
    
    #----------------------------------------------------------------------------
    def transfer_byte_delay( self, data, byte_delay_ms = 0 ):
        if type(data) is list:
            data = pack( len( data ) * 'B', * data)
        
        txbuf = ctypes.create_string_buffer( data )
        rxbuf = ctypes.create_string_buffer( len( data ))
        
        for i in range( len( data )):
            
            p = pack("=QQIIHBBI", ctypes.addressof( txbuf ) + i,
                ctypes.addressof( rxbuf ) + i, 1,
                self.speed, self.delay, self.bpw,
                i < len( data ) - 1, 0)
            
            ioctl(self.handle, SPI_IOC_MESSAGE(1), p)
            
            if byte_delay_ms:
                time.sleep( byte_delay_ms * 0.001)
      
        return unpack( len( data ) * 'B', ctypes.string_at(rxbuf, len( data )))
    
    
    #----------------------------------------------------------------------------
    def transfer( self, data, cs_change = True ):
        
        if type(data) is list:
            data = pack( len( data ) * 'B', * data)
        
        txbuf = ctypes.create_string_buffer( data )
        rxbuf = ctypes.create_string_buffer( len( data))
        
        p = pack("=QQIIHBBI", ctypes.addressof( txbuf ),
                ctypes.addressof( rxbuf ), len( data ),
                self.speed, self.delay, self.bpw,
                not cs_change, 0)
    
        ioctl(self.handle, SPI_IOC_MESSAGE(1), p)

        return ctypes.string_at(rxbuf, len( data ))    