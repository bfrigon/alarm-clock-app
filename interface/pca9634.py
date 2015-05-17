import smbus


#----------------------------------------------------------------------------
# PCA9634 Registers
#----------------------------------------------------------------------------
REG_MODE_1      = 0x00
REG_MODE_2      = 0x01
REG_PWM0        = 0x02
REG_PWM1        = 0x03
REG_PWM2        = 0x04
REG_PWM3        = 0x05
REG_PWM4        = 0x06
REG_PWM5        = 0x07
REG_PWM6        = 0x08
REG_PWM7        = 0x09
REG_GRPPWM      = 0x0A
REG_GRPFREQ     = 0x0B
REG_LEDOUT0     = 0x0C
REG_LEDOUT1     = 0x0D
REG_SUBADR1     = 0x0E
REG_SUBADR2     = 0x0F
REG_SUBADR3     = 0x10
REG_ALLCALLADDR = 0x11

REG_AUTOINCREMENT = 0x80


#----------------------------------------------------------------------------
# Mode register 1 options
#----------------------------------------------------------------------------
MODE_NO_AUTOINCREMENT = 0x00
MODE_AUTOINCREMENT_ALL = 0x80
MODE_AUTOINCREMENT_PWM = 0xA0
MODE_AUTOINCREMENT_GLOBAL = 0xC0
MODE_AUTOINCREMENT_PWM_GLOBAL = 0xE0

MODE_LOW_POWER = 0x10
MODE_NORMAL = 0x00

MODE_SUB1 = 0x08
MODE_NO_SUB1 = 0x00

MODE_SUB2 = 0x04
MODE_NO_SUB2 = 0x00

MODE_SUB3 = 0x02
MODE_NO_SUB3 = 0x00

MODE_ALLCALL = 0x01
MODE_NO_ALLCALL = 0x00


#----------------------------------------------------------------------------
# Mode register 2 options
#----------------------------------------------------------------------------

MODE_GROUP_DIMMING = 0x00
MODE_GROUP_BLINKING = 0x20

MODE_INVRT = 0x10

MODE_CHANGE_ON_STOP = 0x00
MODE_CHANGE_ON_ACK = 0x08

MODE_OUTDRV_OD = 0x00
MODE_OUTDRV_TOTEM = 0x04


#----------------------------------------------------------------------------
# Led states
#----------------------------------------------------------------------------
STATE_OFF = 0x00
STATE_ON = 0x01
STATE_PWM = 0x02
STATE_PWM_GLOBAL = 0x03


#=========================================================================================
class PCA9634:

    #----------------------------------------------------------------------------
    def __init__( self, bus, address, initialize = False, logic_inverted = False, 
                  outdrv_totem = True, low_power = False, 
                  def_led_state = STATE_ON ):
        
        
        self.led_state = [ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ]
        
        self.address = address
        self.smbus = smbus.SMBus( bus )
        
        self.def_led_state = def_led_state
        self.low_power = low_power
        self.logic_inverted = logic_inverted
        self.change_on_ack = False
        self.group_blinking = False
        self.outdrv_totem = outdrv_totem
        
        self.enable_sub1 = False
        self.enable_sub2 = False
        self.enable_sub3 = False
        self.enable_allcall = True
        
        
        if initialize:
            self.set_mode()
        
            self.update_led_state()


    #----------------------------------------------------------------------------
    def set_mode( self ):
        
        mode1 = 0x80
        mode2 = 0x01
        
        
        if self.enable_allcall:
            mode1 |= MODE_ALLCALL
        
        if self.enable_sub1:
            mode1 |= MODE_SUB1
        
        if self.enable_sub2:
            mode1 |= MODE_SUB2
            
        if self.enable_sub3:
            mode1 |= MODE_SUB3
        
        if self.low_power:
            mode1 |= MODE_LOW_POWER
        
        if self.logic_inverted:
            mode2 |= MODE_INVRT
        
        if self.outdrv_totem:
            mode2 |= MODE_OUTDRV_TOTEM
            
        if self.change_on_ack:
            mode2 |= MODE_CHANGE_ON_ACK
            
        if self.group_blinking:
            mode2 |= MODE_GROUP_BLINKING
        
        self.smbus.write_byte_data( self.address, REG_MODE_1, mode1 )
        self.smbus.write_byte_data( self.address, REG_MODE_2, mode2 )
        
    #----------------------------------------------------------------------------
    def set_led_pwm( self, id, value ):
        
        if id < 0 or id > 7:
            raise ValueError('PCA9634:set_led_pwm: Invalid led ID')
        
        self.smbus.write_byte_data( self.address, REG_PWM0 + id, value )


    #----------------------------------------------------------------------------
    def set_all_led_pwm( self, value ):
        self.smbus.write_i2c_block_data( self.address, REG_PWM0 | REG_AUTOINCREMENT, [value] * 8 )


    #----------------------------------------------------------------------------
    def set_led_state( self, id, state, update=True ):
        if id < 0 or id > 7:
            raise ValueError('PCA9634:set_led_state: Invalid led ID')
            
        self.led_state[id] = state
        
        if update:
            self.update_led_state()


    #----------------------------------------------------------------------------
    def set_group_pwm( self, value ):
        
        if value < 0 or value > 255:
            raise ValueError('PCA9634:set_group_pwm: Invalid pwm value (0-255)')
        
        # Set the group control to dimming mode
        if self.group_blinking:
            self.group_blinking = False
            self.set_mode()
        
        self.smbus.write_byte_data( self.address, REG_GRPPWM, value )

    #----------------------------------------------------------------------------
    def set_group_blink( self, period, duty ):
        
        if duty < 0 or duty > 255:
            raise ValueError('PCA9634:set_group_blink: Invalid duty value (0-255)')
        
        if period < 0 or period > 255:
            raise ValueError('PCA9634:set_group_blink: Invalid period value (0-255)')
        
        # Set the group control to blinking mode
        if not self.group_blinking:
            self.group_blinking = True
            self.set_mode()
        
        self.smbus.write_byte_data( self.address, REG_GRPFREQ, period )
        self.smbus.write_byte_data( self.address, REG_GRPPWM, duty )


    #----------------------------------------------------------------------------
    def update_led_state( self ):
        reg0 = self.led_state[0] & 0x3 | \
               ( self.led_state[1] & 0x3 ) << 2 | \
               ( self.led_state[2] & 0x3 ) << 4 | \
               ( self.led_state[3] & 0x3 ) << 6
        
        reg1 = self.led_state[4] & 0x3 | \
               ( self.led_state[5] & 0x3 ) << 2 | \
               ( self.led_state[6] & 0x3 ) << 4 | \
               ( self.led_state[7] & 0x3 ) << 6
        
        self.smbus.write_i2c_block_data( self.address, 
                                         REG_LEDOUT0 | REG_AUTOINCREMENT, 
                                         [ reg0, reg1 ])



#=========================================================================================
class Digit( PCA9634 ):
    
    char_table = {
        " " : [ 0, 0, 0, 0, 0, 0, 0, 0 ],
        "0" : [ 0, 1, 1, 1, 1, 1, 1, 0 ],
        "1" : [ 0, 0, 1, 1, 0, 0, 0, 0 ],
        "2" : [ 0, 1, 1, 0, 1, 1, 0, 1 ],
        "3" : [ 0, 1, 1, 1, 1, 0, 0, 1 ],
        "4" : [ 0, 0, 1, 1, 0, 0, 1, 1 ],
        "5" : [ 0, 1, 0, 1, 1, 0, 1, 1 ],
        "6" : [ 0, 1, 0, 1, 1, 1, 1, 1 ],
        "7" : [ 0, 1, 1, 1, 0, 0, 0, 0 ],
        "8" : [ 0, 1, 1, 1, 1, 1, 1, 1 ],
        "9" : [ 0, 1, 1, 1, 1, 0, 1, 1 ],
        "-" : [ 0, 0, 0, 0, 0, 0, 0, 1 ],
        "_" : [ 0, 0, 0, 0, 1, 0, 0, 0 ],
        "A" : [ 0, 1, 1, 1, 0, 1, 1, 1 ],
        "B" : [ 0, 1, 1, 1, 1, 1, 1, 1 ],
        "C" : [ 0, 1, 0, 0, 1, 1, 1, 0 ],
        "D" : [ 0, 1, 1, 1, 1, 1, 1, 0 ],
        "E" : [ 0, 1, 0, 0, 1, 1, 1, 1 ],
        "F" : [ 0, 1, 0, 0, 0, 1, 1, 1 ],
        "H" : [ 0, 0, 1, 1, 0, 1, 1, 1 ],
        "L" : [ 0, 0, 0, 0, 1, 1, 1, 0 ],
        "U" : [ 0, 1, 1, 1, 1, 1, 1, 0 ],
    }
    
    #----------------------------------------------------------------------------
    def set_digit( self, character ):
        
        if not character in self.char_table:
            character = " "
        
        states = self.char_table[ character ]
        
        for index, item in enumerate(states):
            if item:
                self.led_state[index] = self.def_led_state
            else:
                self.led_state[index] = STATE_OFF
        
        self.update_led_state()