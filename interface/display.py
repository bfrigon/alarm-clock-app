import time

from pca9634 import PCA9634
from pca9634 import Digit

from pca9634 import STATE_ON
from pca9634 import STATE_OFF
from pca9634 import STATE_PWM
from pca9634 import STATE_PWM_GLOBAL

ADDR_DIGIT_1 = 0x68
ADDR_DIGIT_2 = 0x69
ADDR_DIGIT_3 = 0x6a
ADDR_DIGIT_4 = 0x6b
ADDR_DIGIT_BASE = 0x51

ADDR_ALLCALL = 0x70
ADDR_SUB_1 = 0x71
ADDR_SUB_2 = 0x72

LED_ID_ALARM = 0 
LED_ID_PM = 3
LED_ID_DOTS = 4
LED_ID_LIGHT_RED = 5
LED_ID_LIGHT_GREEN = 6
LED_ID_LIGHT_BLUE = 7



#=========================================================================================
class Display:
    
    
    #----------------------------------------------------------------------------
    def __init__( self, bus = 0):
        
        self.bus = 0
        self.alarm_on = False
        
        
        self.base = PCA9634( bus, ADDR_DIGIT_BASE )
        self.group_hour = PCA9634( bus, ADDR_SUB_1 )
        self.group_min = PCA9634( bus, ADDR_SUB_2 )
        
        
        ## Initalize digits ##
        self.digits = [
            Digit( bus, ADDR_DIGIT_1, logic_inverted = True, def_led_state = STATE_PWM ),
            Digit( bus, ADDR_DIGIT_2, logic_inverted = True, def_led_state = STATE_PWM ),
            Digit( bus, ADDR_DIGIT_3, logic_inverted = True, def_led_state = STATE_PWM ),
            Digit( bus, ADDR_DIGIT_4, logic_inverted = True, def_led_state = STATE_PWM ),
        ]
        
        self.digits[0].enable_sub1 = True
        self.digits[1].enable_sub1 = True
        self.digits[2].enable_sub2 = True
        self.digits[3].enable_sub2 = True
        
        for digit in self.digits:
            digit.set_mode()
        

        ## Initalize base PCA9634 ##
        self.base.set_mode()
        
        self.set_rgb( 0, 0, 0 )
        self.base.set_led_state( LED_ID_LIGHT_RED, STATE_PWM )
        self.base.set_led_state( LED_ID_LIGHT_GREEN, STATE_PWM )
        self.base.set_led_state( LED_ID_LIGHT_BLUE, STATE_PWM )

        
        ## Set default text ##
        self.text = "--:--"
        self.set_display( self.text, True)
        
        
        self.set_digit_brightness( 0x01 )
        
        
    
    
    #----------------------------------------------------------------------------
    def set_display( self, text, force = False ):
        
        text = text[ :5 ].ljust( 5 )

        ## Update first two digits ##
        if ( text[0] != self.text[0] ) or force:
            self.digits[0].set_digit( text[0] )
        
        if ( text[1] != self.text[1] ) or force:
            self.digits[1].set_digit( text[1] )
        
        ## Update dots ##
        if ( text[2] != self.text[2] ) or force:
            if text[2] == ":":
                self.base.set_led_state( 4, STATE_PWM )
            else:
                self.base.set_led_state( 4, STATE_OFF )
        
        ## Update last two digits ##
        if ( text[3] != self.text[3] ) or force:
            self.digits[2].set_digit( text[3] )
        
        if ( text[4] != self.text[4] ) or force:
            self.digits[3].set_digit( text[4] )

        self.text = text
    
    
    #----------------------------------------------------------------------------
    def set_digit_brightness( self, value ):
        
        self.group_hour.set_all_led_pwm( value )
        self.group_min.set_all_led_pwm( value )
        self.base.set_led_pwm( LED_ID_DOTS, value )
        
        self.base.set_led_pwm( LED_ID_PM, value )
        self.base.set_led_pwm( LED_ID_ALARM, value )

        
    #----------------------------------------------------------------------------
    def set_rgb( self, red, green, blue ):

        if red > 0:
            red = 89 + ( red * 167 / 256 )
        
        if green > 0:
            green = 84 + ( green * 172 / 256 )
            
        if blue > 0:
            blue = 95 + ( blue * 161 / 256 )
        
        
        self.base.set_led_pwm( LED_ID_LIGHT_RED, red )
        self.base.set_led_pwm( LED_ID_LIGHT_GREEN, green )
        self.base.set_led_pwm( LED_ID_LIGHT_BLUE, blue )
    
    
    #----------------------------------------------------------------------------
    def print_time( self, ts = None ):
        
        if ts is None:
            ts = time.localtime()
        
        
        pm = ts.tm_hour >= 12
        hr = ts.tm_hour
        
        if hr == 0:
            hr = 12
            
        if hr > 12:
            hr = hr % 12
        
        
        self.set_display( str( hr ).rjust( 2 ) + ":" + str( ts.tm_min ).zfill( 2 ) )
        
        self.base.set_led_state( LED_ID_PM, STATE_PWM if pm else STATE_OFF )
        
        