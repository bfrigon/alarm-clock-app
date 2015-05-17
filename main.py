from interface import Display
from interface import AT42QT1085
from interface import GPIO

import time
import Queue
from threading import Thread



class Application:
    
    
    #----------------------------------------------------------------------------
    def init_keypad( self ):
        self.keypad = AT42QT1085( 32766, 0 )
        
        self.gpio_kpd_ch = GPIO( 83, GPIO.PIN_INPUT )
        self.gpio_kpd_ch.set_edge( GPIO.EDGE_FALLING )


        ## Disable haptic events (T31) ##
        haptic_config = [ self.keypad.gen_config_haptic( enabled = False ) ] * 8
        self.keypad.write_config_object( AT42QT1085.OBJ_TYPE_HAPTIC, haptic_config )

        
        ## Configure touch keys (T13) ##
        key_config = [
            self.keypad.gen_config_key( threshold = 16 ),   # Time set
            self.keypad.gen_config_key( threshold = 11 ),   # Right arrow
            self.keypad.gen_config_key( threshold = 12 ),   # Snooze
            self.keypad.gen_config_key( threshold = 11 ),   # Left arrow
            self.keypad.gen_config_key( threshold = 12 ),   # Hour
            self.keypad.gen_config_key( threshold = 13 ),   # Min   
            self.keypad.gen_config_key( threshold = 13 ),   # Alarm set
            self.keypad.gen_config_key( enabled = False ),
        ]
        self.keypad.write_config_object( AT42QT1085.OBJ_TYPE_KEY, key_config )
        
        
        ## Configure GPIO (T29) ##
        gpio_config = [
            self.keypad.gen_config_gpio( enabled = False ), 
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( rpten = False, instance = 6 ),
            self.keypad.gen_config_gpio( rpten = False, instance = 2 ),
            self.keypad.gen_config_gpio( rpten = False, instance = 0 ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
            self.keypad.gen_config_gpio( enabled = False ),
        ]
        self.keypad.write_config_object( AT42QT1085.OBJ_TYPE_GPIO, gpio_config )
        
        
        
    #----------------------------------------------------------------------------
    def process_keypad( self, msg ):
        
        
        key = msg['inst']
        state = msg['data'][0]
        
        print key, state
    
    
    #----------------------------------------------------------------------------
    def worker_keypad( self ):
        
        while True:
            if self.gpio_kpd_ch.read() == 0:
                msg = self.keypad.read_next_message()
                
                if msg is None:
                    continue
                
                if msg['type'] == AT42QT1085.OBJ_TYPE_KEY:
                    self.process_keypad( msg )
                else:
                    print msg
            
            self.gpio_kpd_ch.wait_edge()
            
           

    #----------------------------------------------------------------------------
    def init_display( self ):
        self.disp = Display( 0 )
    
    
    #----------------------------------------------------------------------------
    def run( self ):
        
        self.kpd_queue = Queue.Queue()
        
        self.init_keypad()
        self.init_display()
        
        
        t = Thread( target = self.worker_keypad )
        t.daemon = True
        t.start()
        
        
        
        while True:
            self.disp.print_time()
            
            try:
                key = self.kpd_queue.get( timeout = 1 )
                
                print key
                
                
            except Queue.Empty:
                pass
            
            time.sleep(1)
        
        


if __name__=="__main__":
    app = Application()
    app.run()        