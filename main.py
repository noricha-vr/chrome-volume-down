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
DEFAULT_VOLUME = float(os.getenv("DEFAULT_VOLUME", "0.5"))
# ========================


def parse_args():
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
    parser.add_argument(
        "-d", "--default-volume",
        type=float,
        default=DEFAULT_VOLUME,
        help=f"リセット時のデフォルト音量。デフォルト: {DEFAULT_VOLUME}"
    )
    return parser.parse_args()


def main() -> None:
    # コマンドライン引数を解析
    args = parse_args()
    interval_sec = args.interval
    chromecast_name = args.name
    step = args.step
    min_level = args.min_level
    default_volume = args.default_volume
    
    # logs ディレクトリにファイルとしてログを出力する設定
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "lower_cast_volume.log"

    logging.basicConfig(
        level=logging.INFO,
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
    logging.info(f"デフォルト音量: {default_volume}")

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

    try:
        while True:
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
                # ボリュームを0に設定
                cast.set_volume(default_volume)
                logging.info("音量を%sに設定しました。", default_volume)
                time.sleep(2)  # 音量設定が反映されるまで待機
                
                # Chromecastの電源を切る（スタンバイモードにする）
                logging.info("Chromecastをスタンバイモードにします。")
                cast.quit_app()
                time.sleep(2)  # 処理が完了するまで待機
                logging.info("Chromecastがスタンバイモードになりました。プログラムを終了します。")
                break

            new_level = max(min_level-1, round(cur + step, 2))
            cast.set_volume(new_level)
            logging.info("音量を %.2f → %.2f へ変更しました", cur, new_level)

            time.sleep(interval_sec)
    finally:
        # Discoveryを適切に停止
        pychromecast.stop_discovery(browser)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
