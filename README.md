# File Watcher

* 본 프로젝트는 지정한 디렉토리에 새로 생성되는 파일을 탐지하여 주어진 action (copy, move, delete)에 따라서 동작하도록 구현되어 있습니다.
* 본 프로젝트는 Python 3.9.18를 기반으로 하며, RHEL 9.4를 기반으로 테스트를 하였습니다.

## PyPi 패키지 설치

```
yum install -y krb5-devel
pip3 install pandas watchdog argparse lxml hdfs requests-kerberos
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
