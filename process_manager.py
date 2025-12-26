#!/usr/bin/env python3
"""
Flask 앱 프로세스 관리자
- 백그라운드에서 Flask 앱 실행
- 프로세스 상태 모니터링
- 자동 재시작 기능
- 로그 관리
- 가상환경 지원
"""

import subprocess
import psutil
import os
import signal
import time
import json
from datetime import datetime
from pathlib import Path

class ProcessManager:
    def __init__(self):
        self.pid_file = "/tmp/frameflow_app.pid"
        self.log_file = "/tmp/frameflow_app.log"
        self.error_log_file = "/tmp/frameflow_error.log"
        self.app_script = "app.py"
        
        # 가상환경 Python 경로 확인
        self.python_path = self._get_python_path()
        
    def _get_python_path(self):
        """가상환경 Python 경로 찾기"""
        # 1. 저장된 경로 확인
        if os.path.exists("/tmp/frameflow_python_path"):
            try:
                with open("/tmp/frameflow_python_path", 'r') as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        return path
            except:
                pass
        
        # 2. 현재 디렉토리의 가상환경 확인
        venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")
        if os.path.exists(venv_python):
            return venv_python
        
        # 3. 기본 python3 사용
        return "python3"
        
    def is_running(self):
        """프로세스가 실행 중인지 확인"""
        if not os.path.exists(self.pid_file):
            return False
            
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # PID가 실제로 존재하고 우리 앱인지 확인
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                if "python" in proc.name().lower() and "app.py" in " ".join(proc.cmdline()):
                    return True
            
            # PID 파일이 있지만 프로세스가 없으면 파일 삭제
            os.remove(self.pid_file)
            return False
            
        except (ValueError, psutil.NoSuchProcess, FileNotFoundError):
            return False
    
    def start(self):
        """Flask 앱 시작"""
        if self.is_running():
            return {"status": "already_running", "message": "앱이 이미 실행 중입니다."}
        
        try:
            # 로그 파일 초기화
            with open(self.log_file, 'w') as f:
                f.write(f"=== FrameFlow 시작: {datetime.now()} ===\n")
                f.write(f"Python 경로: {self.python_path}\n")
            
            # Flask 앱 백그라운드 실행
            process = subprocess.Popen(
                [self.python_path, self.app_script],
                stdout=open(self.log_file, 'a'),
                stderr=open(self.error_log_file, 'a'),
                preexec_fn=os.setsid  # 새로운 세션 그룹 생성
            )
            
            # PID 저장
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # 잠시 대기 후 실제로 시작되었는지 확인
            time.sleep(2)
            if self.is_running():
                return {
                    "status": "started", 
                    "message": "FrameFlow가 성공적으로 시작되었습니다.",
                    "pid": process.pid,
                    "python_path": self.python_path
                }
            else:
                return {"status": "failed", "message": "앱 시작에 실패했습니다. 로그를 확인하세요."}
                
        except Exception as e:
            return {"status": "error", "message": f"시작 중 오류: {str(e)}"}
    
    def stop(self):
        """Flask 앱 중지"""
        if not self.is_running():
            return {"status": "not_running", "message": "앱이 실행되고 있지 않습니다."}
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 프로세스 그룹 전체 종료 (자식 프로세스도 함께)
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            
            # 5초 대기 후 강제 종료
            time.sleep(5)
            if psutil.pid_exists(pid):
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            
            # PID 파일 삭제
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            return {"status": "stopped", "message": "FrameFlow가 중지되었습니다."}
            
        except Exception as e:
            return {"status": "error", "message": f"중지 중 오류: {str(e)}"}
    
    def restart(self):
        """Flask 앱 재시작"""
        stop_result = self.stop()
        time.sleep(2)
        start_result = self.start()
        
        return {
            "status": "restarted",
            "message": f"재시작 완료. 중지: {stop_result['message']}, 시작: {start_result['message']}"
        }
    
    def get_status(self):
        """상태 정보 반환"""
        if not self.is_running():
            return {
                "status": "stopped",
                "message": "FrameFlow가 중지되어 있습니다.",
                "uptime": None,
                "memory": None,
                "python_path": self.python_path
            }
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            proc = psutil.Process(pid)
            uptime = time.time() - proc.create_time()
            memory = proc.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "status": "running",
                "message": "FrameFlow가 실행 중입니다.",
                "pid": pid,
                "uptime": f"{int(uptime//3600)}시간 {int((uptime%3600)//60)}분",
                "memory": f"{memory:.1f}MB",
                "python_path": self.python_path
            }
            
        except Exception as e:
            return {"status": "error", "message": f"상태 확인 오류: {str(e)}"}
    
    def get_logs(self, lines=50, error_only=False):
        """로그 반환"""
        try:
            log_file = self.error_log_file if error_only else self.log_file
            
            if not os.path.exists(log_file):
                return "로그 파일이 없습니다."
            
            # 마지막 N줄 읽기
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
                
        except Exception as e:
            return f"로그 읽기 오류: {str(e)}"
    
    def monitor_errors(self):
        """에러 로그 모니터링 (새로운 에러만 반환)"""
        try:
            if not os.path.exists(self.error_log_file):
                return None
            
            # 마지막 체크 시간 파일
            last_check_file = "/tmp/frameflow_last_check.txt"
            
            # 현재 시간
            current_time = time.time()
            
            # 마지막 체크 시간 읽기
            last_check_time = 0
            if os.path.exists(last_check_file):
                try:
                    with open(last_check_file, 'r') as f:
                        last_check_time = float(f.read().strip())
                except:
                    pass
            
            # 에러 로그에서 새로운 내용만 찾기
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_errors = []
            for line in lines:
                if "ERROR" in line or "Exception" in line or "Traceback" in line:
                    new_errors.append(line.strip())
            
            # 마지막 체크 시간 업데이트
            with open(last_check_file, 'w') as f:
                f.write(str(current_time))
            
            if new_errors:
                return '\n'.join(new_errors[-10:])  # 최근 10개 에러만
            
            return None
            
        except Exception as e:
            return f"에러 모니터링 실패: {str(e)}"


if __name__ == "__main__":
    import sys
    
    manager = ProcessManager()
    
    if len(sys.argv) < 2:
        print("사용법: python process_manager.py [start|stop|restart|status|logs]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start":
        result = manager.start()
    elif command == "stop":
        result = manager.stop()
    elif command == "restart":
        result = manager.restart()
    elif command == "status":
        result = manager.get_status()
    elif command == "logs":
        print(manager.get_logs())
        sys.exit(0)
    else:
        print("알 수 없는 명령어")
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))