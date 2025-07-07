#!/usr/bin/env python3
"""
lower_cast_volume.py
--------------------
指定した Chromecast / Google TV の音量を 20 分ごとに 1 ステップ下げ続ける
* pychromecast 10.4.0 以上推奨
* Python 3.9+
"""

import os
import time
import logging
import sys
import argparse
from pathlib import Path

import pychromecast
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# ========= 設定 =========
CHROMECAST_NAME = os.getenv("CHROMECAST_NAME", "Dell")
STEP = float(os.getenv("STEP", "-0.04"))
MIN_LEVEL = float(os.getenv("MIN_LEVEL", "0.3"))
DEFAULT_INTERVAL_SEC = int(os.getenv("INTERVAL_SEC", "1200"))
# ========================


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Chromecast / Google TV の音量を定期的に下げるスクリプト"
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SEC,
        help=f"音量調整の間隔（秒）。デフォルト: {DEFAULT_INTERVAL_SEC}秒"
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default=CHROMECAST_NAME,
        help=f"Chromecastの名前。デフォルト: {CHROMECAST_NAME}"
    )
    parser.add_argument(
        "-s", "--step",
        type=float,
        default=STEP,
        help=f"音量調整のステップ（負の値）。デフォルト: {STEP}"
    )
    parser.add_argument(
        "-m", "--min-level",
        type=float,
        default=MIN_LEVEL,
        help=f"最小音量レベル。デフォルト: {MIN_LEVEL}"
    )
    return parser.parse_args(args)


def is_chromecast_active(cast) -> bool:
    """
    Chromecastが実際にアクティブかどうかを確認する
    
    Returns:
        bool: アクティブならTrue、アイドル/スタンバイ状態ならFalse
    """
    try:
        # デバッグ情報を表示
        logging.debug(f"Cast status - app_id: {cast.status.app_id}, "
                     f"display_name: {cast.status.display_name}, "
                     f"is_active_input: {cast.status.is_active_input}, "
                     f"is_stand_by: {cast.status.is_stand_by}")
        
        # app_idがNoneの場合はアイドル状態
        if cast.status.app_id is None:
            logging.debug("Chromecast is idle (no app running)")
            return False
            
        # IDLE_APP_IDまたはBackdropアプリの場合はアイドル状態
        if cast.status.app_id in [pychromecast.IDLE_APP_ID, 'E8C28D3C', 'Backdrop']:
            logging.debug(f"Chromecast is idle (app_id: {cast.status.app_id})")
            return False
        
        # メディアコントローラーの状態も確認
        try:
            cast.media_controller.update_status()
            if hasattr(cast.media_controller, 'status') and cast.media_controller.status:
                player_state = cast.media_controller.status.player_state
                logging.debug(f"Media player state: {player_state}")
                # メディアが再生中または一時停止中の場合はアクティブ
                if player_state in ['PLAYING', 'PAUSED', 'BUFFERING']:
                    return True
        except:
            pass
        
        # 何かアプリが起動している（AndroidNativeApp、YouTube、Netflixなど）
        logging.debug(f"Chromecast is active - app: {cast.status.display_name} ({cast.status.app_id})")
        return True
        
    except Exception as e:
        logging.warning(f"Chromecastの状態確認に失敗しました: {e}")
        # エラーの場合は動作を継続するためTrueを返す
        return True


def main() -> None:
    # コマンドライン引数を解析
    args = parse_args()
    interval_sec = args.interval
    chromecast_name = args.name
    step = args.step
    min_level = args.min_level
    
    # logs ディレクトリにファイルとしてログを出力する設定
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "lower_cast_volume.log"

    # 環境変数でログレベルを設定可能にする
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    logging.info(f"音量調整間隔: {interval_sec}秒")
    logging.info(f"Chromecast名: {chromecast_name}")
    logging.info(f"音量調整ステップ: {step}")
    logging.info(f"最小音量レベル: {min_level}")

    logging.info("Chromecast デバイスを検索しています...")
    
    # pychromecastの簡潔なデバイス検索方法
    chromecasts, browser = pychromecast.get_chromecasts()
    
    if not chromecasts:
        logging.error("ネットワーク上で Chromecast が見つかりませんでした。")
        pychromecast.stop_discovery(browser)
        sys.exit(1)

    logging.info("発見したデバイス: %s", [cc.cast_info.friendly_name for cc in chromecasts])

    # friendly_name で目的のデバイスを探す
    cast = None
    for cc in chromecasts:
        logging.info(f'キャスト名: {cc.cast_info.friendly_name}')
        if cc.cast_info.friendly_name == chromecast_name:
            cast = cc
            break

    if cast is None:
        logging.error("目的の Chromecast '%s' が見つかりませんでした。", chromecast_name)
        pychromecast.stop_discovery(browser)
        sys.exit(1)

    logging.info("接続完了: %s (%s)", cast.cast_info.friendly_name, cast.cast_info.host)
    cast.wait()  # ソケット接続確立を待つ
    
    # 起動時の音量を保存
    cast.media_controller.update_status()
    initial_volume = cast.status.volume_level
    if initial_volume is None:
        logging.warning("起動時の音量を取得できませんでした。0.5を使用します。")
        initial_volume = 0.5
    else:
        logging.info("起動時の音量を保存しました: %.2f", initial_volume)

    try:
        while True:
            # Chromecastがアクティブかどうかチェック
            if not is_chromecast_active(cast):
                logging.info("Chromecastはスタンバイ状態です。音量調整をスキップします。")
                time.sleep(interval_sec)
                continue
            
            # 最新のステータスを更新して取得
            cast.media_controller.update_status()
            cur = cast.status.volume_level
            if cur is None:
                logging.warning("音量レベルを取得できませんでした。再試行します。")
                time.sleep(5)
                continue
                
            logging.info("現在の音量: %.2f", cur)
            
            if cur <= min_level:
                logging.info("最小音量に到達 (%.2f)。", cur)
                # ボリュームを初期値に戻す
                cast.set_volume(initial_volume)
                logging.info("音量を初期値 %.2f に戻しました。", initial_volume)
                time.sleep(2)  # 音量設定が反映されるまで待機
                
                # Chromecastの電源を切る（スタンバイモードにする）
                # 既にスタンバイ状態でないかチェック
                if is_chromecast_active(cast):
                    logging.info("Chromecastをスタンバイモードにします。")
                    cast.quit_app()
                    time.sleep(2)  # 処理が完了するまで待機
                    logging.info("Chromecastがスタンバイモードになりました。")
                else:
                    logging.info("Chromecastは既にスタンバイ状態です。")
                
                logging.info("プログラムを終了します。")
                break

            new_level = max(min_level-1, round(cur + step, 2))
            cast.set_volume(new_level)
            logging.info("音量を %.2f → %.2f へ変更しました", cur, new_level)

            time.sleep(interval_sec)
    except KeyboardInterrupt:
        logging.info("\n中断されました。音量を初期値に戻します...")
        try:
            cast.set_volume(initial_volume)
            logging.info("音量を初期値 %.2f に戻しました。", initial_volume)
            time.sleep(1)  # 音量設定が反映されるまで待機
        except Exception as e:
            logging.error("音量の復元に失敗しました: %s", e)
        raise
    finally:
        # Discoveryを適切に停止
        pychromecast.stop_discovery(browser)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
