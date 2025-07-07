# Nemucast 関数一覧

## main.py

### 設定・初期化関数

#### `parse_args(args=None)`
コマンドライン引数を解析する
- 音量調整間隔、Chromecast名、音量ステップ、最小音量レベルを設定

#### `setup_logging() -> None`
ロギングの設定を行う
- ログファイルの保存先設定
- 環境変数によるログレベル設定

### Chromecast検索・接続関数

#### `discover_chromecasts(target_name: str) -> Tuple[Optional[pychromecast.Chromecast], Optional[pychromecast.discovery.CastBrowser]]`
Chromecastデバイスを検索し、指定された名前のデバイスを返す
- ネットワーク上のChromecastを検索
- 指定された名前のデバイスを特定

### 状態確認・表示関数

#### `log_chromecast_status(cast) -> None`
Chromecastの現在の状態をログ出力する
- アクティブ/アイドル状態の表示
- メディアの再生状態を表示

#### `log_active_app_status(cast) -> None`
アクティブなアプリの状態をログ出力する
- メディアの再生状態を表示

#### `is_chromecast_active(cast) -> bool`
Chromecastが実際にアクティブかどうかを確認する
- アプリIDによる判定
- メディアプレイヤーの状態確認

### 音量制御関数

#### `get_initial_volume(cast) -> float`
起動時の音量を取得する
- 現在の音量レベルを保存

#### `adjust_volume(cast, current_volume: float, step: float, min_level: float) -> Optional[float]`
音量を調整する
- 指定されたステップで音量を下げる
- 最小レベルに達した場合はNoneを返す

#### `restore_volume_and_standby(cast, initial_volume: float) -> None`
音量を初期値に戻してスタンバイモードにする
- 音量を起動時の値に復元
- Chromecastをスタンバイモードに移行

### メインループ関数

#### `volume_control_loop(cast, interval_sec: int, step: float, min_level: float, initial_volume: float) -> None`
メインの音量制御ループ
- 定期的に音量を調整
- アイドル状態の場合はスキップ
- 最小音量到達時に終了処理

#### `main() -> None`
メインエントリーポイント
- 全体の処理フローを制御
- エラーハンドリングとクリーンアップ