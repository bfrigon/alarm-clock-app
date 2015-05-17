import time

from spi import SPI
from timeit import timeit
from gpio import GPIO



#=========================================================================================
class AT42QT1085:
    obj_table = {}
    report_id = []


    #-----------------------------
    # Object types
    #-----------------------------
    OBJ_TYPE_MESSAGE = 5    
    OBJ_TYPE_COMMAND = 6
    OBJ_TYPE_KEY = 13
    OBJ_TYPE_GPIO = 29
    OBJ_TYPE_HAPTIC = 31
    
    
    #-----------------------------
    # Commands
    #-----------------------------
    COMMAND_RESET = 0
    COMMAND_BACKUP = 1
    COMMAND_CALIBRATE = 2
    COMMAND_REPORT = 3
    

    #-----------------------------
    # T13 : Key config
    #-----------------------------
    CONFIG_KEY_ENABLE = 0x01
    CONFIG_KEY_RPTEN = 0x02
    CONFIG_KEY_GUARD = 0x20
    CONFIG_KEY_DISREL = 0x40
    CONFIG_KEY_DISPRESS = 0x80
    
    CONFIG_KEY_HYST_50 = 0x00
    CONFIG_KEY_HYST_25 = 0x01
    CONFIG_KEY_HYST_12_5 = 0x02
    CONFIG_KEY_HYST_6_25 = 0x03
    
    
    #-----------------------------
    # T29 : GPIO
    #-----------------------------
    CONFIG_GPIO_ENABLE = 0x01
    CONFIG_GPIO_RPTEN = 0x02
    CONFIG_GPIO_FADE = 0x04
    CONFIG_GPIO_TOGGLE = 0x08
    CONFIG_GPIO_DRIVELVL_PUSH = 0x10
    CONFIG_GPIO_DISOFF = 0x20
    CONFIG_GPIO_INVERT = 0x40
    CONFIG_GPIO_OUTPUT = 0x80
    
    GPIO_SOURCE_HOST = 0
    GPIO_SOURCE_KEY = 1
    GPIO_SOURCE_GPIO = 4
    
    GPIO_DRIVELVL_PUSH = 1
    GPIO_DRIVELVL_DRAIN = 0

    
    #-----------------------------
    # T31 : Haptic event
    #-----------------------------
    CONFIG_HAPTIC_ENABLE = 0x01
    CONFIG_HAPTIC_RPTEN = 0x02
    CONFIG_HAPTIC_LOOP = 0x20
    CONFIG_HAPTIC_DISFINISH = 0x40
    CONFIG_HAPTIC_DISSTART = 0x80
    
    HAPTIC_EFFECT_STRONG_CLICK = 1
    HAPTIC_EFFECT_STRONG_CLICK_60 = 2
    HAPTIC_EFFECT_STRONG_CLICK_30 = 3
    HAPTIC_EFFECT_SHARP_CLICK = 4
    HAPTIC_EFFECT_SHARP_CLICK_60 = 5
    HAPTIC_EFFECT_SHARP_CLICK_30 = 6
    HAPTIC_EFFECT_SOFT_BUMP = 7
    HAPTIC_EFFECT_SOFT_BUMP_60 = 8
    HAPTIC_EFFECT_SOFT_BUMP_30 = 9
    HAPTIC_EFFECT_DOUBLE_CLICK = 10
    HAPTIC_EFFECT_DOUBLE_CLICK_60 = 11
    HAPTIC_EFFECT_TRIPLE_CLICK = 12
    HAPTIC_EFFECT_SOFT_BUZZ = 13
    HAPTIC_EFFECT_STRONG_BUZZ = 14
    
    HAPTIC_SOURCE_HOST = 0
    HAPTIC_SOURCE_KEY = 1
    HAPTIC_SOURCE_GPIO = 4
    
    
    
    
    
    
    #----------------------------------------------------------------------------
    def __init__( self, bus, client):
        
        self.spi = SPI( bus, client, SPI.SPI_MODE_3, 550000 )
        
        self.read_object_table()
    
    
    #----------------------------------------------------------------------------
    def __del__( self ):
        pass

        
    #----------------------------------------------------------------------------
    def read_object_table( self ):
        
        self.obj_table = {}
        self.report_id = []
        
        info = self.read_block( 0x00, 0x00, 7 )

        nobj = info[6]
        info = self.read_block( 0x00, 0x00, 10 + ( nobj * 6 ))
        
        crc = info[ -1 ] << 16 | info[ -2 ] << 8 | info[ -3 ]
        if not self.crc24( info[ :-3 ] ) == crc:
            raise IOError( "Invalid checksum for information block" )
        
        
        for i in range( nobj ):
            
            start = 7 + ( i * 6 )
            obj_type = info[ start ]
            
            ninst = info[ start + 4 ] + 1
            nreports = info[ start + 5 ]
            
            self.obj_table[obj_type] = {
                'lsb' : info[ start + 1 ],
                'msb' : info[ start + 2 ],
                'size' : info[ start + 3 ] + 1,
                'ninst' : ninst,
                'nreports' : nreports
            }
            
            for n in range( nreports * ninst ):
                self.report_id.append({
                    'type' : obj_type,
                    'inst' : n 
                })

        ## Send reset command ##
        self.send_command( self.COMMAND_RESET )
        time.sleep( 0.065 )


    #----------------------------------------------------------------------------
    def read_config_object( self, obj_type, instance = None ):
        
        if not obj_type in self.obj_table:
            raise ValueError( "Object (T%d) does not exists." % ( obj_type ))
        
        lsb = self.obj_table[ obj_type ][ 'lsb' ]
        msb = self.obj_table[ obj_type ][ 'msb' ]
        size = self.obj_table[ obj_type ][ 'size' ]
        ninst = self.obj_table[ obj_type ][ 'ninst' ]
        
        
        if instance is None:
            block = self.read_block( lsb, msb, size * ninst )
        
            obj = []
            for i in range( ninst ):
                obj.append( block[ i * size : ( i * size ) + size ] )
            
            return obj
        else:
            
            if ( instance < 0 ) or ( instance > ninst - 1 ):
                raise ValueError( "Invalid instance ID for this type of object (T%d@%d)" % ( obj_type, instance ))
            
            lsb += ( instance * size )
            msb += ( lsb & 0xFF00 ) >> 8 
            
            return self.read_block( lsb, msb, size )
    
    
    #----------------------------------------------------------------------------
    def write_config_object( self, obj_type, config, instance = None ):
        
        if not obj_type in self.obj_table:
            raise ValueError( "Object (T%d) does not exists." % ( obj_type ))
        
        lsb = self.obj_table[ obj_type ][ 'lsb' ]
        msb = self.obj_table[ obj_type ][ 'msb' ]
        size = self.obj_table[ obj_type ][ 'size' ]
        ninst = self.obj_table[ obj_type ][ 'ninst' ]        
        
        if instance is None:
            
            if len( config ) != ninst:
                raise ValueError( "Invalid number of blocks for object (T%d)" % ( obj_type ))
            
            data = []
            for i in range( ninst ):
                if len( config[ i ] ) != size:
                    raise ValueError( "Invalid block size for object (T%d@%d)" % ( obj_type, i ))
                
                data.extend( config[ i ] )
            
            
            return self.write_block( lsb, msb, data )
        
        else:
            
            if ( instance < 0 ) or ( instance > ninst - 1 ):
                raise ValueError( "Invalid instance ID for this type of object (T%d@%d)" % ( obj_type, instance ))
            
            if len( config ) != size:
                raise ValueError( "Invalid block size for object (T%d@%d)" % ( obj_type, instance ))
            
            lsb += ( instance * size )
            msb += ( lsb & 0xFF00 ) >> 8 
            
            return self.write_block( lsb, msb, config )


    #----------------------------------------------------------------------------
    def read_next_message( self ):
        
        msg = self.read_config_object( self.OBJ_TYPE_MESSAGE )
        
        idx = msg[0][0] - 1
        if idx == 254:
            return None
        
        report = self.report_id[ idx ]
        report['data'] = msg[0][1:-1]
        
        return report
    
    
    #----------------------------------------------------------------------------
    def read_block( self, addr_low, addr_hi, size ):
        addr_hi = (( addr_low & 0x80 ) >> 7 ) + ( addr_hi << 1 )
        addr_low = (( addr_low & 0x7f ) << 1 ) | 0x01
        
        data = [ addr_low, addr_hi, size]
        data.extend( [0x00] * size )
        
        received = self.spi.transfer_byte_delay( data )
        
        time.sleep ( 0.002 )
        
        return received[3:]


    #----------------------------------------------------------------------------
    def write_block( self, addr_low, addr_hi, block ):
        
        addr_hi = (( addr_low & 0x80 ) >> 7 ) + ( addr_hi << 1 )
        addr_low = (( addr_low & 0x7f ) << 1 )
        
        data = [ addr_low, addr_hi, len( block ) ]
        data.extend( block )
        
        received = self.spi.transfer_byte_delay( data )
        
        time.sleep( 0.010 )

        
        return sum( received[ 3: ] ) == ( 0xAA * len( block ))
    
    
    #----------------------------------------------------------------------------
    def crc24( self, block ):
        
        crc = 0x00
        crcpoly = 0x80001b
        
        for i in range( 0, len( block ), 2 ):
            
            if i + 1 < len( block ):
                data_word = ( block[ i + 1 ] << 8 ) | block[ i ]
            else:
                data_word = block[ i ]
                
            crc = (( crc << 1 ) ^ data_word )
        
            if crc & 0x1000000:
                crc ^= crcpoly
        
        return crc & 0xFFFFFF
    
    
    
    #----------------------------------------------------------------------------
    def send_command( self, command ):
        
        data = [ 0x00 ] * self.obj_table[ self.OBJ_TYPE_COMMAND]['size']
        
        if command > ( len( data ) - 1 ):
            raise ValueError( "Invalid command: %x (T6)" % ( command ))
    
        data[ command ] = 0x55
        
        return self.write_config_object( self.OBJ_TYPE_COMMAND, data, 0 )
    
    
    #----------------------------------------------------------------------------
    def gen_config_key( self, enabled = True, rpten = True, guard = False, dis_msg_rel = False,
                        dis_msg_press = False, hyst = CONFIG_KEY_HYST_25, aks_group = 1,
                        tchdi = 3, threshold = 0x10 ):
        
        config = [ 0x00 ] * self.obj_table[ self.OBJ_TYPE_KEY ]['size']
        
        if enabled:
            config[ 0 ] |= self.CONFIG_KEY_ENABLE
        
            if rpten:
                config[ 0 ] |= self.CONFIG_KEY_RPTEN
                
            if dis_msg_rel:
                config[ 0 ] |= self.CONFIG_KEY_DISREL
                
            if dis_msg_press:
                config[ 0 ] |= self.CONFIG_KEY_DISPRESS
            
            if guard:
                config[ 0 ] |= self.CONFIG_KEY_GUARD
            
            config[ 1 ] = ( hyst & 0x03 ) | (( aks_group & 0x07 ) << 2 ) | (( tchdi & 0x07 ) << 5 ) 
            config[ 2 ] = threshold
    
        return config
    
    
    #----------------------------------------------------------------------------
    def gen_config_haptic( self, enabled = True, rpten = True, loop = False, dis_msg_finish = False,
                           dis_msg_start = False, effect = HAPTIC_EFFECT_SHARP_CLICK, 
                           source = HAPTIC_SOURCE_KEY, instance = 0 ):
        
        config = [ 0x00 ] * self.obj_table[ self.OBJ_TYPE_HAPTIC ]['size']
        
        if enabled:
            config[ 0 ] |= self.CONFIG_HAPTIC_ENABLE
            
            if rpten:
                config[ 0 ] |= self.CONFIG_HAPTIC_RPTEN
            
            if loop:
                config[ 0 ] |= self.CONFIG_HAPTIC_LOOP
        
            if dis_msg_finish:
                config[ 0 ] |= self.CONFIG_HAPTIC_DISFINISH
                
            if dis_msg_start:
                config[ 0 ] |= self.CONFIG_HAPTIC_DISSTART
        
            config[ 1 ] = effect & 0x7F
            config[ 2 ] = ( instance & 0x1F ) | (( source & 0x07 ) << 5 )
        
        
        return config
    
    
    #----------------------------------------------------------------------------
    def gen_config_gpio( self, enabled = True, rpten = True, fade = False, 
                         toggle = False, drivelvl = GPIO_DRIVELVL_PUSH, disoff = False, 
                         invert = False, output = True, pwm_on = 15, pwm_off = 0,
                         source = GPIO_SOURCE_KEY, instance = 0):
        
        config = [ 0x00 ] * self.obj_table[ self.OBJ_TYPE_GPIO ]['size']
        
        if enabled:
            config[ 0 ] |= self.CONFIG_GPIO_ENABLE
            
            if rpten:
                config[ 0 ] |= self.CONFIG_GPIO_RPTEN
        
            if fade:
                config[ 0 ] |= self.CONFIG_GPIO_FADE
        
            if toggle:
                config[ 0 ] |= self.CONFIG_GPIO_TOGGLE
        
            if drivelvl:
                config[ 0 ] |= self.CONFIG_GPIO_DRIVELVL_PUSH
        
            if disoff:
                config[ 0 ] |= self.CONFIG_GPIO_DISOFF
        
            if invert:
                config[ 0 ] |= self.CONFIG_GPIO_INVERT
        
            if output:
                config[ 0 ] |= self.CONFIG_GPIO_OUTPUT
        
            config[ 1 ] = ( pwm_off & 0x0F ) | (( pwm_on & 0x0F ) << 4 )
            config[ 2 ] = ( instance & 0x1F ) | (( source & 0x07 ) << 5 )
        
        return config