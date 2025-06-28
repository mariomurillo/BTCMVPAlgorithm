from unittest import TestCase
from algo.main import BTCMVPA_BTCUSD
from QuantConnect import Resolution, Market
import yaml
import os

class BasicStrategyTest(TestCase):
    def setUp(self):
        self.algorithm = BTCMVPA_BTCUSD()
        self.algorithm.set_start_date(2023, 1, 1)
        self.algorithm.set_end_date(2023, 1, 10)
        self.algorithm.set_cash(100000)
        
        # Load parameters
        param_path = os.path.join(os.path.dirname(__file__), '../config/parameters.yml')
        with open(param_path) as f:
            self.params = yaml.safe_load(f)
            
        self.algorithm.Initialize()

    def test_algorithm_initialization(self):
        """Verify core algorithm configuration"""
        self.assertEqual(self.algorithm.StartDate.year, 2023)
        self.assertEqual(self.algorithm.Portfolio.Cash, 100000)
        self.assertEqual(self.algorithm.btc_symbol.Value, "BTCUSD")

    def test_parameter_loading(self):
        """Ensure parameters are loaded correctly from YAML"""
        self.assertEqual(self.algorithm.fast_ema.period, self.params['fast_ema_period'])
        self.assertEqual(self.algorithm.slow_ema.period, self.params['slow_ema_period'])
        self.assertEqual(self.algorithm.stop_loss_percent, self.params['stop_loss_percent']/100)

    def test_indicator_initialization(self):
        """Validate technical indicator setup"""
        self.assertTrue(self.algorithm.fast_ema.IsReady)
        self.assertTrue(self.algorithm.slow_ema.IsReady)
        self.assertTrue(self.algorithm.atr_5min.IsReady)

    def test_brokerage_model(self):
        """Verify exchange fee structure"""
        security = self.algorithm.btc_security
        self.assertAlmostEqual(
            security.FeeModel.GetOrderFee(security, 100).value, 
            100 * security.Price * (self.params['broker_fee_percentage'] + self.params['estimated_slippage_percentage'])/100,
            places=2
        )

    def test_warmup_period(self):
        """Ensure sufficient data initialization"""
        required_warmup = max(
            self.params['fast_ema_period'],
            self.params['slow_ema_period'],
            14,  # ATR period
            5,    # Volume lookback
            self.params['sma_atr_period']
        )
        self.assertEqual(self.algorithm.warm_up_period, required_warmup)
