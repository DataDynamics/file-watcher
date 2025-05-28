# File Watcher

## PyPi 패키지 설치

```
pip3 install pandas watchdog argparse lxml
```

## Configuration

### `config.yaml`

```yaml
app:
  logfile-path: app.log
  directories-path: directories.xml
  # 안정 상태 판단 시간 (초)
  stable-wait-seconds: 10
  # 크기 변화 체크 간격 (초)
  stability-check-interval-seconds: 2
```

### `directories.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<directories>
    <directory>
        <source-path>/home/tester/file-watch/1</source-path>
        <file-pattern>*.log</file-pattern>
        <target-path>/home/tester/file-watch/2</target-path>
        <action>copy</action>
    </directory>
</directories>
```

## Run

```
python3 watcher.py --config config.yaml
```
