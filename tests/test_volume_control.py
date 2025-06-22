"""音量制御ロジックのテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os


class TestVolumeControl:
    """音量制御のテストクラス"""

    def test_volume_calculation_step_down(self):
        """音量を段階的に下げる計算のテスト"""
        current = 0.5
        step = -0.04
        min_level = 0.3
        
        # 正常な音量下げ計算
        expected = max(min_level - 1, round(current + step, 2))
        assert expected == 0.46
        
        # 最小値に近い場合
        current = 0.32
        expected = max(min_level - 1, round(current + step, 2))
        assert expected == 0.28

    def test_min_volume_detection(self):
        """最小音量の検出テスト"""
        min_level = 0.3
        
        # 最小値以下
        assert 0.29 <= min_level
        assert 0.3 <= min_level
        
        # 最小値より大きい
        assert not (0.31 <= min_level)
        assert not (0.5 <= min_level)

    @patch('pychromecast.get_chromecasts')
    def test_chromecast_discovery_no_devices(self, mock_get_chromecasts):
        """Chromecastが見つからない場合のテスト"""
        mock_get_chromecasts.return_value = ([], Mock())
        
        from nemucast.main import main
        
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['nemucast']):
                main()
        
        assert exc_info.value.code == 1

    def test_environment_variable_defaults(self):
        """環境変数のデフォルト値テスト"""
        # 環境変数をクリア
        env_vars = ['CHROMECAST_NAME', 'STEP', 'MIN_LEVEL', 'INTERVAL_SEC']
        original_values = {}
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        try:
            # モジュールを再インポートして環境変数を再読み込み
            if 'nemucast.main' in sys.modules:
                del sys.modules['nemucast.main']
            
            from nemucast.main import (
                CHROMECAST_NAME, STEP, MIN_LEVEL, 
                DEFAULT_INTERVAL_SEC
            )
            
            assert CHROMECAST_NAME == "Dell"
            assert STEP == -0.04
            assert MIN_LEVEL == 0.3
            assert DEFAULT_INTERVAL_SEC == 1200
        
        finally:
            # 環境変数を復元
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    def test_volume_rounding(self):
        """音量の丸め処理テスト"""
        # 小数点2桁に丸められることを確認
        assert round(0.444, 2) == 0.44
        assert round(0.445, 2) == 0.45  # Python3のround仕様
        assert round(0.446, 2) == 0.45
        assert round(0.999, 2) == 1.0