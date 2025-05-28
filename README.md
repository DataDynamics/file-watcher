# File Watcher

* 본 프로젝트는 지정한 디렉토리에 새로 생성되는 파일을 탐지하여 주어진 action (copy, move, delete)에 따라서 동작하도록 구현되어 있습니다.
* 본 프로젝트는 Python 3.9.18를 기반으로 하며, RHEL 9.4를 기반으로 테스트를 하였습니다.

## PyPi 패키지 설치

```
yum install -y krb5-devel krb5-workstation
pip3 install pandas watchdog argparse lxml hdfs requests-kerberos --no-index --find-links file://`pwd`/pip
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

## HDFS Kerberos

```python
from hdfs.ext.kerberos import KerberosClient
import subprocess
import os


# 환경변수
os.environ["KRB5_CONFIG"] = "/custom/path/to/krb5.conf"
os.environ["KRB5CCNAME"] = "FILE:/tmp/krb5cc_hdfs"

# WebHDFS 주소
HDFS_URL = 'http://namenode-host:9870'  # or active RM HA address
hdfs_client = KerberosClient(url=HDFS_URL)

def hdfs_copy_api(local_path, hdfs_path):
    try:
        hdfs_client.upload(hdfs_path, local_path, overwrite=True)
        logging.info(f"[HDFS API COPY] {local_path} → {hdfs_path}")
    except Exception as e:
        logging.error(f"[ERROR] Failed to copy via Kerberos HDFS API: {e}")

def hdfs_move_api(local_path, hdfs_path):
    try:
        hdfs_client.upload(hdfs_path, local_path, overwrite=True)
        os.remove(local_path)
        logging.info(f"[HDFS API MOVE] {local_path} → {hdfs_path}")
    except Exception as e:
        logging.error(f"[ERROR] Failed to move via Kerberos HDFS API: {e}")

def kinit_with_keytab(principal, keytab_path):
    """
    Kerberos keytab을 이용하여 인증을 수행하는 함수.
    :param principal: 예) 'hdfs@YOUR.REALM'
    :param keytab_path: 예) '/etc/security/keytabs/hdfs.keytab'
    """
    try:
        subprocess.run(["kinit", "-kt", keytab_path, principal], check=True)
        logging.info(f"[KERBEROS] Authenticated as {principal}")
    except subprocess.CalledProcessError as e:
        logging.error(f"[ERROR] Kerberos authentication failed: {e}")
        raise

def get_kerberos_expiry():
    try:
        output = subprocess.check_output(["klist"], encoding="utf-8")
        for line in output.splitlines():
            if line.strip().startswith("Expires"):
                # Format: Expires               Service principal
                continue
            if "/" in line and ":" in line:  # heuristic
                expires_str = line.split()[0] + " " + line.split()[1]
                return datetime.datetime.strptime(expires_str, "%m/%d/%Y %H:%M:%S")
    except Exception as e:
        logging.warning(f"[KERBEROS] Cannot get expiry: {e}")
    return None


def ensure_valid_kerberos_ticket(threshold_minutes=5):
    expiry = get_kerberos_expiry()
    now = datetime.datetime.now()
    if not expiry or (expiry - now).total_seconds() < threshold_minutes * 60:
        logging.info("[KERBEROS] Ticket missing or about to expire. Re-authenticating...")
        kinit_with_keytab("hdfs@YOUR.REALM", "/path/to/hdfs.keytab")
    else:
        logging.debug(f"[KERBEROS] Ticket valid until: {expiry}")

# 사용 예시
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_valid_kerberos_ticket()
    # → 그 다음 HDFS 작업 수행 (예: hdfs_client.upload(...))
```