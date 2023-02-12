# impuestos-mexico
Este programa simplica la labor de declaracion de impuestos para una persona fisica con inversiones

## Inverisiones en el sistema no financiero
Los impuestos que se pagan en inversiones en el sistema no finaciero son el IVA y el ISR, estos datos son guardados de manera diaria en la tabla `diario_no_finaciero` y los valores que se guardan dependen de la institucion:

### Prestadero
- `institucion_id`: `prestadero`
- `abono`: Monto invertido, esto es monto en invertido en un prestamo. Tipo de movimiento `FONDEO` campo importe.Suma al saldo.
- `comision`: Comisiones pagadas a prestadero sin iva. Suma de capital, interes, moratorio y recuperaciones, a la suma multiplicar por 0.01 . Resta al saldo
- `iva_comision`: Iva pagado de la comision cobrada.
- `interes`: Intereses nominales y moratorios. Tipo de movimiento `PAGOS`, En detalle es la suma de interes y moratorios. Suma al saldo
- `iva_interes`: Iva trasladado del interes nominal y moratorio.
- `recuperacion`: Retorno de capital extraordinario. Tipo de movimiento `RECUPERACION` campo inporte.Resta al saldo
- `capital`: Capital amortizado.  Tipo de movimiento `PAGOS`, En detalle es principal. Resta al saldo.

### Afluenta
Afluenta te proporcional cada mes un excel con los intereses he iva, pero no te muestran las comisiones ni el iva de las comsiones.
- `institucion_id`: `afluenta`
- `abono`: Diferencia positiva entre el saldo capital del dia contra el dia anterior
- `comision`: En movimientos es la suma de los debitos divido entre 1.16
- `iva_comision`: Es `comison` por 0.16
- `interes`: En movimientos es la suma de Creditos divida entre 1.16
- `iva_interes`: Es el `interes` multiplicado por 0.16.
- `recuperacion`: Para esta fuente es siempre cero.
- `capital`: Capital amortizado.  Diferencia negativa entre el saldo capital del dia contra el dia anterior