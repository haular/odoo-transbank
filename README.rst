=======================================
Integración Transbank WebPay para Odoo
=======================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: Licencia: LGPL-3
.. |badge3| image:: https://raster.shields.io/badge/website-BMYA-lightgreen.png
    :target: https://github.com/haular/odoo-transbank
    :alt: BMYA
.. |badge4| image:: https://img.shields.io/badge/profile-Me-white.png?logo=github
    :target: https://github.com/haular
    :alt: haular

|badge1| |badge2| |badge3| |badge4|

Este proyecto ofrece una integración entre **Odoo** y **Transbank**, permitiendo el procesamiento de pagos para empresas.

Incluye soporte para:

* **Webpay Plus**: Flujo de pago estándar con redirección.

**Tabla de Contenidos**

.. contents::
   :local:

Instalación
===========

Dependencias
------------
Este módulo requiere la librería oficial de Transbank para Python.

.. code-block:: bash

    pip install transbank-sdk==6.1.0

Módulos de Odoo
---------------
Instale los siguientes módulos ubicados en este repositorio:

1.  ``payment_transbank`` (Librería base y lógica central)
2.  ``payment_transbank_webpay`` (Implementación Webpay Plus)

Configuración
=============

Credenciales
------------
Para configurar el proveedor de pagos:

1.  Navegue a **Contabilidad** > **Configuración** > **Proveedores de Pago**.
2.  Seleccione **Transbank**.
3.  Establezca el estado en **Prueba (Test)** o **Habilitado (Producción)**.
4.  Ingrese las credenciales proporcionadas por Transbank:

    * **Código de Comercio (Commerce Code)**
    * **API Key**

Uso
===

Webpay Plus
-----------
En el checkout, los usuarios verán "Webpay Plus" como opción de pago. Serán redirigidos al portal seguro de Transbank para completar la transacción usando tarjetas de Crédito o Débito.

Problemas Conocidos / Roadmap
=============================

* El soporte para "Webpay Modal" aún no está implementado.
* Los reembolsos (refunds) deben gestionarse directamente en el portal de Transbank.

Bug Tracker
===========

Los errores se rastrean en los Issues de GitHub. En caso de problemas, por favor verifique allí si su incidencia ya ha sido reportada.

Créditos
========

Autor
-----

* **Héctor Aular** <aular.hector.dev@gmail.com>

Colaboradores
-------------

*   Blanco Martín & Asociados <odoocl@bmya.cl>
*   Héctor Aular <aular.hector.dev@gmail.com>

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