import re

from odoo.addons.payment.const import SENSITIVE_KEYS as PAYMENT_SENSITIVE_KEYS

# Transbank tokens must never reach the logs in clear text.
SENSITIVE_KEYS = {'token_ws', 'TBK_TOKEN', 'token'}
PAYMENT_SENSITIVE_KEYS.update(SENSITIVE_KEYS)

# The SDK rejects a longer buy_order before any HTTP call.
BUY_ORDER_MAX_LENGTH = 26
BUY_ORDER_PATTERN = re.compile(r'^[A-Za-z0-9|_=&%.,~:/?\[+!@()>-]+$')

# Seconds before giving up on a Transbank API call (the SDK default is 600).
API_TIMEOUT = 30

PAYMENT_TYPE_CODES = {
    'VN': 'Venta Normal',
    'S2': '2 Cuotas sin interés',
    'SI': '3 Cuotas sin interés',
    'NC': 'N Cuotas sin interés',
    'VC': 'Cuotas normales',
    'VD': 'Venta débito Redcompra',
    'VP': 'Venta Prepago',
}

# Level 1 authorization response codes (Transbank's default). Level 2 reuses the same numbers
# with other meanings: never show these texts to the customer without knowing the level.
RESPONSE_CODES = {
    0: 'Transacción Aprobada',
    -1: 'Rechazo - Posible error en el ingreso de datos de la transacción',
    -2: 'Rechazo - Se produjo fallo al procesar la transacción (parámetros de tarjeta/cuenta)',
    -3: 'Rechazo - Error en Transacción',
    -4: 'Rechazo - Rechazada por parte del emisor',
    -5: 'Rechazo - Transacción con riesgo de posible fraude',
}

# Webpay statuses mapping
# Note: These are for display/logging, Odoo uses its own state machine.
TRANSBANK_STATUSES = {
    'INITIALIZED': 'Inicializada',
    'AUTHORIZED': 'Autorizada',
    'REVERSED': 'Reversada',
    'FAILED': 'Fallida',
    'NULLIFIED': 'Anulada',
    'PARTIALLY_NULLIFIED': 'Anulada parcialmente',
    'CAPTURED': 'Capturada',
}
