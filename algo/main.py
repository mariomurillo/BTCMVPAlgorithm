from QuantConnect.Algorithm import QCAlgorithm
from QuantConnect.Indicators import EMA, ATR, MovingAverageType
from QuantConnect.Data.Slice import Slice
from datetime import timedelta
import numpy as np
import collections

from QuantConnect.Orders.Fees import ConstantFeeModel
from QuantConnect.Brokerages import BrokerageName
from QuantConnect.Securities import SecurityType
from QuantConnect.Orders import OrderStatus

class BTCMVPA_BTCUSD(QCAlgorithm): # Nombre de clase específico para indicar BTCUSD

    def Initialize(self):
        
        # 1. Configuración de Parámetros del Backtest
        self.set_start_date(2023, 1, 1) # Fecha de inicio del backtest
        self.set_end_date(2023, 12, 31) # Fecha de fin del backtest (cambiar para probar otros años)
        self.set_cash(1000)             # Capital inicial

        # Brokerage Model para BTCUSD (Bitfinex)
        self.set_brokerage_model(BrokerageName.BITFINEX, AccountType.CASH)
        self.set_security_initializer(self.SetCosts)

        # 2. Añadir el Activo: BTC/USD (Hardcodeado para esta versión)
        self.btc_security = self.add_crypto("BTCUSD", Resolution.MINUTE, Market.BITFINEX)
        self.btc_symbol = self.btc_security.symbol # Guardar el símbolo

        # Slippage en 0 (debido a los problemas de simulación real, se modela en SetCosts)
        self.btc_security.set_slippage_model(ConstantSlippageModel(0))

        # 3. Consolidación de Datos a 5 minutos
        self.consolidate(self.btc_symbol, timedelta(minutes=5), self.FiveMinuteHandler)

        # 4. **Lógica Condicional para EMA Horaria (basada en parámetro)**
        # Esta lógica es la que te dio los mejores resultados con ema_hourly_enable = False
        if bool(self.get_parameter("ema_hourly_enable")): # Si el parámetro es True
            self.consolidate(self.btc_symbol, timedelta(hours=1), self.HourlyHandler)
            self.hourly_ema = self.ema(self.btc_symbol, int(self.get_parameter("hourly_ema_period")), Resolution.HOUR)
        else: # Si el parámetro es False (como en tu backtest ganador)
            self.hourly_ema = None # No se inicializa, y las condiciones de entrada lo ignorarán
        
        # 5. Inicializar los Indicadores Principales (siempre activos)
        self.fast_ema = self.ema(self.btc_symbol, int(self.get_parameter("fast_ema_period")), Resolution.MINUTE)
        self.slow_ema = self.ema(self.btc_symbol, int(self.get_parameter("slow_ema_period")), Resolution.MINUTE)
        
        # Inicialización del ATR (siempre activo, aunque no se use como filtro de entrada si no es rentable)
        self.atr_5min = self.ATR(self.btc_symbol, 14, MovingAverageType.SIMPLE) 

        # 6. Configuración de Deques para Promedios (Volumen y ATR)
        self.volume_lookback = 5
        self.recent_volumes = collections.deque(maxlen=self.volume_lookback)
        self.sma_atr_period = int(self.get_parameter("sma_atr_period"))
        self.recent_atrs = collections.deque(maxlen=self.sma_atr_period)

        # 7. **NUEVO:** Obtener el tamaño de la posición desde los parámetros
        self.position_size_percent = float(self.get_parameter("position_size_percent")) / 100

        # 8. Establecer el período de calentamiento
        # El calentamiento debe ser el más largo de los periodos de los indicadores y lookbacks
        # Si hourly_ema es None, su warm_up_period no se usa.
        warm_up_periods = [
            self.fast_ema.warm_up_period,
            self.slow_ema.warm_up_period,
            self.atr_5min.warm_up_period,
            self.volume_lookback,
            self.sma_atr_period
        ]
        if self.hourly_ema: # Solo si hourly_ema fue inicializado
            warm_up_periods.append(self.hourly_ema.warm_up_period)

        self.set_warm_up(max(warm_up_periods))

        # 9. Configuración de Gestión de Riesgo (de parámetros)
        self.stop_loss_percent = float(self.get_parameter("stop_loss_percent")) / 100 
        self.take_profit_percent = float(self.get_parameter("take_profit_percent")) / 100
        self.trailing_stop_percent = float(self.get_parameter("trailing_stop_percent")) / 100

        # 10. Variables de estado del algoritmo
        # Estas variables rastrean el estado de la ÚNICA posición abierta en BTC/USD
        self.entry_price = 0
        self.entry_time = None
        self.out_by_time_minutes = int(self.get_parameter("out_by_time_minutes"))
        self.trade_duration = timedelta(minutes=self.out_by_time_minutes)
        # Banderas redundantes si se usa Portfolio.Invested, pero se mantienen si la lógica las espera
        # self.long_position_open = False
        # self.short_position_open = False
        self.highest_price_since_entry = 0 
        self.lowest_price_since_entry = 0 


        self.debug(f"Algoritmo inicializado para BTC/USD. Calentando por {self.warm_up_period} períodos.")


    def SetCosts(self, security):
        """ Configura fees y una aproximación de slippage. """
        if security.type == SecurityType.CRYPTO:
            broker_fee_percentage = float(self.get_parameter("broker_fee_percentage")) / 100
            estimated_slippage_percentage = float(self.get_parameter("estimated_slippage_percentage")) / 100
            total_transaction_cost_percentage = broker_fee_percentage + estimated_slippage_percentage
            security.set_fee_model(ConstantFeeModel(total_transaction_cost_percentage))

    # Handler para la EMA Horaria (solo se usará si hourly_ema_enable es True)
    def HourlyHandler(self, bar):
        pass # La EMA se actualiza automáticamente.
    
    def FiveMinuteHandler(self, bar):
        """ Handler principal para procesar barras de 5 minutos y ejecutar la lógica de trading. """
        
        # Acumular volúmenes y ATRs durante el calentamiento y después
        self.recent_volumes.append(bar.Volume) # bar.Volume existe para TradeBar (BTCUSD)
        if len(self.recent_volumes) > self.volume_lookback:
            self.recent_volumes.pop(0)

        if self.atr_5min.is_ready: # Acumular ATRs solo si el ATR está listo
            self.recent_atrs.append(self.atr_5min.current.value)
            if len(self.recent_atrs) > self.sma_atr_period:
                self.recent_atrs.pop(0)

        # Regresar si estamos en calentamiento o si los indicadores no están listos
        # Las verificaciones de is_ready para self.hourly_ema son condicionales
        if self.is_warming_up or \
           not (self.fast_ema.is_ready and self.slow_ema.is_ready and self.atr_5min.is_ready) or \
           (self.hourly_ema and not self.hourly_ema.is_ready): # Solo si hourly_ema está inicializado, debe estar listo
            return

        # Asegurarse de tener suficientes datos para promedios
        if len(self.recent_volumes) < self.volume_lookback or \
           len(self.recent_atrs) < self.sma_atr_period:
            return

        current_price = bar.Close
        current_time = self.time
        current_open = bar.Open
        current_volume = bar.Volume # bar.Volume existe para BTCUSD
        
        candle_body = current_price - current_open
        candle_range = bar.High - bar.Low

        min_candle_body_percentage_val = float(self.get_parameter("min_candle_body_percentage")) / 100


        # --- Lógica de Entrada ---
        # Usamos Portfolio.Invested para verificar si hay una posición abierta
        is_invested_long = self.Portfolio[self.symbol].IsLong
        is_invested_short = self.Portfolio[self.symbol].IsShort

        if not is_invested_long and not is_invested_short: # Si no tenemos ninguna posición abierta
            # Condición de Volumen
            volume_factor_val = 1 + float(self.get_parameter("volume_factor_percent")) / 100
            volume_condition = current_volume > average_volume * volume_factor_val

            # Condiciones de Vela
            bullish_candle_filter = (candle_body > 0 and (candle_range > 0 and candle_body >= candle_range * min_candle_body_percentage_val))
            bearish_candle_filter = (candle_body < 0 and (candle_range > 0 and abs(candle_body) >= candle_range * min_candle_body_percentage_val))

            # Cruce EMA de 5 minutos
            ema_bullish_cross = self.fast_ema.current.value > self.slow_ema.current.value and \
                                self.fast_ema.previous.value <= self.slow_ema.previous.value
            ema_bearish_cross = self.fast_ema.current.value < self.slow_ema.current.value and \
                                self.fast_ema.previous.value >= self.slow_ema.previous.value
            
            # **NUEVA LÓGICA DE ENTRADA CON EMA HORARIA CONDICIONAL**
            # Condición para entrada en largo
            can_enter_long = ema_bullish_cross and volume_condition and bullish_candle_filter

            if self.hourly_ema: # Si la EMA horaria está inicializada
                # Debe cumplir con el filtro de EMA horaria TAMBIÉN
                can_enter_long = can_enter_long and current_price > self.hourly_ema.current.value

            # 1. Entrada en Largo (Buy)
            if can_enter_long:
                self.set_holdings(self.symbol, self.position_size_percent)
                self.entry_price = current_price
                self.entry_time = current_time
                self.highest_price_since_entry = current_price # Reinicializar
                self.debug(f"COMPRA {self.symbol.ID} @ {current_time} - Precio: {current_price:.2f} | Posición: {self.position_size_percent * 100}%")
            
            # Condición para entrada en corto
            can_enter_short = ema_bearish_cross and volume_condition and bearish_candle_filter

            if self.hourly_ema: # Si la EMA horaria está inicializada
                # Debe cumplir con el filtro de EMA horaria TAMBIÉN
                can_enter_short = can_enter_short and current_price < self.hourly_ema.current.value

            # 2. Entrada en Corto (Sell)
            elif bool(self.get_parameter("short_enable")) and can_enter_short:
                self.set_holdings(self.symbol, -self.position_size_percent)
                self.entry_price = current_price
                self.entry_time = current_time
                self.lowest_price_since_entry = current_price # Reinicializar
                self.debug(f"VENTA CORTO {self.symbol.ID} @ {current_time} - Precio: {current_price:.2f} | Posición: {self.position_size_percent * 100}%")
        
        # --- Lógica de SALIDA ---
        # Se usan Portfolio.IsLong/IsShort, como es más robusto.

        if self.Portfolio[self.symbol].IsLong:
            if current_price > self.highest_price_since_entry:
                self.highest_price_since_entry = current_price
            
            trailing_stop_price = self.highest_price_since_entry * (1 - self.trailing_stop_percent)

            if current_price <= trailing_stop_price:
                self.liquidate(self.symbol)
                self.debug(f"SL Dinamico {self.symbol.ID} @ {current_time}")

            elif current_price >= self.entry_price * (1 + self.take_profit_percent):
                self.liquidate(self.symbol)
                self.debug(f"TP {self.symbol.ID} @ {current_time}")

            # Salida por Cruce de EMA Opuesto (no se había añadido aún en tu versión final)
            # Descomentar si quieres añadir este filtro de salida
            # elif self.fast_ema.current.value < self.slow_ema.current.value and \
            #      self.fast_ema.previous.value >= self.slow_ema.previous.value:
            #     self.liquidate(self.symbol)
            #     self.debug(f"SALIDA POR CRUCE EMA (Largo) {self.symbol.ID} @ {current_time}")

            elif self.entry_time and (current_time - self.entry_time) >= self.trade_duration:
                self.liquidate(self.symbol)
                self.debug(f"SALIDA POR TIEMPO {self.symbol.ID} @ {current_time}")
        
        elif self.Portfolio[self.symbol].IsShort:
            if current_price < self.lowest_price_since_entry:
                self.lowest_price_since_entry = current_price
            
            trailing_stop_price_short = self.lowest_price_since_entry * (1 + self.trailing_stop_percent)

            if current_price >= trailing_stop_price_short:
                self.liquidate(self.symbol)
                self.debug(f"SL DINÁMICO (Corto) {self.symbol.ID} @ {current_time}")

            elif current_price <= self.entry_price * (1 - self.take_profit_percent):
                self.liquidate(self.symbol)
                self.debug(f"TP (Corto) {self.symbol.ID} @ {current_time}")

            # Salida por Cruce de EMA Opuesto (no se había añadido aún en tu versión final)
            # Descomentar si quieres añadir este filtro de salida
            # elif self.fast_ema.current.value > self.slow_ema.current.value and \
            #      self.fast_ema.previous.value <= self.slow_ema.previous.value:
            #     self.liquidate(self.symbol)
            #     self.debug(f"SALIDA POR CRUCE EMA (Corto) {self.symbol.ID} @ {current_time}")

            elif self.entry_time and (current_time - self.entry_time) >= self.trade_duration:
                self.liquidate(self.symbol)
                self.debug(f"SALIDA POR TIEMPO (Corto) {self.symbol.ID} @ {current_time}")


    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.FILLED:
            self.debug(f"Orden LLENA: {orderEvent.Symbol.ID} - Cantidad: {orderEvent.FillQuantity} - Precio de llenado: {orderEvent.FillPrice}")
            # Al abrir una posición, inicializamos highest/lowest price
            # Esto se hace ya en la lógica de entrada dentro de FiveMinuteHandler
            pass
