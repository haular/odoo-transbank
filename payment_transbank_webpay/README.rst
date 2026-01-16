===========================
Transbank Webpay Plus
===========================

.. |badge1| image:: https://raster.shields.io/badge/website-BMYA-lightgreen.png
    :target: https://github.com/haular/odoo-transbank
    :alt: BMYA
.. |badge2| image:: https://img.shields.io/badge/profile-Me-white.png?logo=github
    :target: https://github.com/haular
    :alt: haular
Este módulo habilita el método de pago **Webpay Plus** dentro del proveedor Transbank en Odoo. Permite a los clientes pagar utilizando tarjetas de crédito y débito a través del formulario de redirección seguro de Transbank.

|badge1| |badge2|

**Tabla de Contenidos**

.. contents::
   :local:

Instalación
===========

1.  Asegúrese de que el módulo base ``payment_transbank`` esté instalado.
2.  Instale este módulo ``payment_transbank_webpay``.
3.  La librería python ``transbank-sdk`` debe estar instalada en su entorno.

Configuración
=============

Para habilitar Webpay Plus:

1.  Vaya a **Contabilidad** > **Configuración** > **Proveedores de Pago**.
2.  Seleccione el proveedor **Transbank**.
3.  En la pestaña **Credenciales**, busque la sección **Webpay Plus Credentials**.
4.  Ingrese sus credenciales entregadas por Transbank:
    *   **Webpay Commerce Code** (Código de Comercio)
    *   **Webpay API Key**
5.  Configure el estado a **Prueba** (para integración) o **Habilitado** (para producción).
6.  Asegúrese de "Publicar" el proveedor para que esté disponible en el sitio web.

Uso
===

Flujo de Pago
-------------
1.  El cliente selecciona "Webpay Plus" al finalizar la compra en el eCommerce o al pagar una factura online.
2.  Odoo redirige al usuario al formulario seguro de Webpay (Transbank).
3.  El usuario ingresa sus datos bancarios y confirma la transacción.
4.  Al finalizar, es redirigido de vuelta a Odoo, donde la transacción queda confirmada automáticamente si el pago fue exitoso.


Autor
-----

* **Héctor Aular**

Colaboradores
-------------

*   Héctor Aular <aular.hector.dev @gmail.com>
*   Blanco Martín & Asociados <odoocl@bmya.cl>

Afiliación y Soporte Profesional
--------------------------------

Si bien este repositorio es un esfuerzo para la comunidad, **BMYA** ofrece soluciones avanzadas y servicios de consultoría para Odoo en Chile.

Si tu empresa requiere características adicionales, soporte garantizado o integraciones complejas, BMYA cuenta con:

* **Conector OneClick:** Con soporte para **Webpay OneClick** (pagos recurrentes y en un click).
* **Asesoría Técnica:** Implementación y personalización de flujos de pago.
* **Soporte Especializado:** Mantenimiento preventivo y correctivo de la plataforma Odoo.

Para más información sobre estos servicios profesionales, puedes visitar:
`www.bmya.cl <https://www.bmya.cl>`_

.. image:: https://www.bmya.cl/web/image/website/1/logo/Blanco%20Martin%20y%20Asociados?unique=42c8824
   :alt: BMYA - Consulting & Integration
   :target: https://bmya.cl

---

*Nota: Se comparte bajo licencia LGPL-3 como contribución a la comunidad de Odoo.*
