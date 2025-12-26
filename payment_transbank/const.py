PAYMENT_TYPE_CODES = {
    'VN': 'Venta Normal',
    'S2': '2 Cuotas sin interés',
    'SI': '3 Cuotas sin interés',
    'NC': 'N Cuotas sin interés',
    'VC': 'Cuotas normales',
    'VD': 'Venta débito Redcompra',
    'VP': 'Venta Prepago',
}

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
