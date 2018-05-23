doorStateMachine = {\
#	  current     key transition      other key    next        error                               \
	( 'CLOSED'  , 'CLOSED_KEY_UP'   , 'UP'   ) : ( 'CLOSED'  , True  , '')                        ,\
	( 'CLOSED'  , 'CLOSED_KEY_UP'   , 'DOWN' ) : ( 'CLOSED'  , False , '')                        ,\
	( 'CLOSED'  , 'CLOSED_KEY_DOWN' , 'UP'   ) : ( 'OPENING' , True  , '')                        ,\
	( 'CLOSED'  , 'CLOSED_KEY_DOWN' , 'DOWN' ) : ( 'OPENING' , False , 'door_is_opening_message') ,\
	( 'CLOSED'  , 'OPEN_KEY_UP'     , 'UP'   ) : ( 'CLOSED'  , True  , '')                        ,\
	( 'CLOSED'  , 'OPEN_KEY_UP'     , 'DOWN' ) : ( 'OPEN'    , True  , '')                        ,\
	( 'CLOSED'  , 'OPEN_KEY_DOWN'   , 'UP'   ) : ( 'CLOSED'  , True  , '')                        ,\
	( 'CLOSED'  , 'OPEN_KEY_DOWN'   , 'DOWN' ) : ( 'CLOSING' , True  , '')                        ,\
	( 'OPEN'    , 'CLOSED_KEY_UP'   , 'UP'   ) : ( 'OPEN'    , True  , '')                        ,\
	( 'OPEN'    , 'CLOSED_KEY_UP'   , 'DOWN' ) : ( 'CLOSED'  , True  , '')                        ,\
	( 'OPEN'    , 'CLOSED_KEY_DOWN' , 'UP'   ) : ( 'OPEN'    , True  , '')                        ,\
	( 'OPEN'    , 'CLOSED_KEY_DOWN' , 'DOWN' ) : ( 'OPENING' , True  , '')                        ,\
	( 'OPEN'    , 'OPEN_KEY_UP'     , 'UP'   ) : ( 'OPEN'    , True  , '')                        ,\
	( 'OPEN'    , 'OPEN_KEY_UP'     , 'DOWN' ) : ( 'OPEN'    , False , '')                        ,\
	( 'OPEN'    , 'OPEN_KEY_DOWN'   , 'UP'   ) : ( 'CLOSING' , True  , '')                        ,\
	( 'OPEN'    , 'OPEN_KEY_DOWN'   , 'DOWN' ) : ( 'CLOSING' , False , 'door_is_closing_message') ,\
	( 'CLOSING' , 'CLOSED_KEY_UP'   , 'UP'   ) : ( 'CLOSED'  , True  , '')                        ,\
	( 'CLOSING' , 'CLOSED_KEY_UP'   , 'DOWN' ) : ( 'CLOSED'  , False , 'door_is_closed_message')  ,\
	( 'CLOSING' , 'CLOSED_KEY_DOWN' , 'UP'   ) : ( 'CLOSED'  , True  , '')                        ,\
	( 'CLOSING' , 'CLOSED_KEY_DOWN' , 'DOWN' ) : ( 'CLOSED'  , True  , '')                        ,\
	( 'CLOSING' , 'OPEN_KEY_UP'     , 'UP'   ) : ( 'CLOSING' , True  , '')                        ,\
	( 'CLOSING' , 'OPEN_KEY_UP'     , 'DOWN' ) : ( 'OPEN'    , False , '')                        ,\
	( 'CLOSING' , 'OPEN_KEY_DOWN'   , 'UP'   ) : ( 'CLOSING' , True  , '')                        ,\
	( 'CLOSING' , 'OPEN_KEY_DOWN'   , 'DOWN' ) : ( 'CLOSING' , False , '')                        ,\
	( 'OPENING' , 'CLOSED_KEY_UP'   , 'UP'   ) : ( 'OPENING' , True  , '')                        ,\
	( 'OPENING' , 'CLOSED_KEY_UP'   , 'DOWN' ) : ( 'CLOSED'  , False , '')                        ,\
	( 'OPENING' , 'CLOSED_KEY_DOWN' , 'UP'   ) : ( 'OPENING' , True  , '')                        ,\
	( 'OPENING' , 'CLOSED_KEY_DOWN' , 'DOWN' ) : ( 'OPENING' , False , '')                        ,\
	( 'OPENING' , 'OPEN_KEY_UP'     , 'UP'   ) : ( 'OPEN'    , True  , '')                        ,\
	( 'OPENING' , 'OPEN_KEY_UP'     , 'DOWN' ) : ( 'OPEN'    , False , 'door_is_open_message')    ,\
	( 'OPENING' , 'OPEN_KEY_DOWN'   , 'UP'   ) : ( 'OPEN'    , True  , '')                        ,\
	( 'OPENING' , 'OPEN_KEY_DOWN'   , 'DOWN' ) : ( 'OPEN'    , True  , '')                         \
}

commandPermissions = {\
#	 command         admin   users   demands_password \
	'start'        : ( True  , True  , False )       ,\
	'open'         : ( True  , True  , True  )       ,\
	'close'        : ( True  , True  , True  )       ,\
	'activate'     : ( True  , False , True  )       ,\
	'status'       : ( True  , True  , True  )       ,\
	'stop'         : ( True  , False , True  )       ,\
	'def_password' : ( True  , False , False )       ,\
	'password_ck'  : ( True  , False , False )       ,\
	'put_password' : ( False , True  , False )       ,\
	'diagnosis'    : ( True  , False , False )        \
}
