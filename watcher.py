import time
import shutil
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
from lxml import etree
import logging
from logging.handlers import TimedRotatingFileHandler
import yaml
import fnmatch


# YAML 설정 파일 로드 함수
def load_config(path='config.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


# argparse를 사용해 커맨드라인 인자 처리
def parse_args():
    parser = argparse.ArgumentParser(description="File Watcher with YAML config")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to the config YAML file')
    return parser.parse_args()

#  YAML 파싱
args = parse_args()
config = load_config(args.config)
app_config = config['app']

# 주요 설정값
directories_path = app_config['directories-path']

STABLE_WAIT = app_config['stable-wait-seconds']
STABILITY_CHECK_INTERVAL = app_config['stable-wait-seconds']

# Logger 설정
log_file = app_config['logfile-path']
logger = logging.getLogger("daily_logger")
logger.setLevel(logging.INFO)

handler = TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',     # 자정 기준 롤링
    interval=1,          # 매 1일마다
    backupCount=14,      # 최근 14일치만 보관
    encoding='utf-8',
    utc=False            # 로컬 시간 기준 (True면 UTC 기준)
)

formatter = logging.Formatter('%(asctime)s - [%(levelname)s] %(filename)s:%(lineno)d - %(message)s')  # Formatter
handler.setFormatter(formatter)

logger.addHandler(handler)  # Log Handler
logger.addHandler(logging.StreamHandler())  # 콘솔 출력도 가능하게 설정

class DirectoryConfig:
    def __init__(self, source_path, file_pattern, target_path, action):
        self.source_path = source_path
        self.file_pattern = file_pattern
        self.target_path = target_path
        self.action = action


def load_config_xml():
    configs = []
    tree = etree.parse(directories_path)
    for dir_node in tree.xpath("//directory"):
        source = dir_node.findtext("source-path")
        pattern = dir_node.findtext("file-pattern")
        target = dir_node.findtext("target-path")
        action = dir_node.findtext("action")
        configs.append(DirectoryConfig(source, pattern, target, action))
    return configs


class StableFileHandler(FileSystemEventHandler):
    def __init__(self, config: DirectoryConfig, tracked_files):
        self.config = config
        self.tracked_files = tracked_files

    def on_created(self, event):
        self._track(event)

    def on_modified(self, event):
        self._track(event)

    def _track(self, event):
        if not event.is_directory and fnmatch.fnmatch(os.path.basename(event.src_path), self.config.file_pattern):
            logger.info(f"[DETECTED] {event.src_path}")
            self.tracked_files[event.src_path] = (time.time(), self.config)


def is_file_stable(path):
    try:
        size1 = os.path.getsize(path)
        time.sleep(STABILITY_CHECK_INTERVAL)
        size2 = os.path.getsize(path)
        return size1 == size2
    except Exception:
        return False


def process_file(path, config: DirectoryConfig):
    filename = os.path.basename(path)
    dest_path = os.path.join(config.target_path, filename)
    if config.action == "copy":
        logger.info(f"[COPY] {path} → {dest_path}")
        shutil.copy2(path, dest_path)
    elif config.action == "move":
        logger.info(f"[MOVE] {path} → {dest_path}")
        shutil.move(path, dest_path)
    elif config.action == "delete":
        logger.info(f"[DELETE] {path} → {dest_path}")
        os.remove(path)
    else:
        logger.info(f"[SKIP] Unsupported action: {config.action}")


def main():
    tracked_files = {}
    observers = []

    configs = load_config_xml()

    for config in configs:
        os.makedirs(config.target_path, exist_ok=True)
        handler = StableFileHandler(config, tracked_files)
        observer = Observer()
        observer.schedule(handler, config.source_path, recursive=False)
        observer.start()
        observers.append(observer)
        logger.info(f"Started watching: {config.source_path} with pattern {config.file_pattern}")

    try:
        while True:
            now = time.time()
            for path in list(tracked_files.keys()):
                last_event_time, config = tracked_files[path]
                if now - last_event_time >= STABLE_WAIT:
                    if is_file_stable(path):
                        process_file(path, config)
                        del tracked_files[path]
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watchers...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()


if __name__ == "__main__":
    main()
