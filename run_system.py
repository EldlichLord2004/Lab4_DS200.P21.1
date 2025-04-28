import os
import sys
import time
import signal
import socket
import subprocess
import threading
import argparse

# Thiết lập mã hóa đầu ra cho console Windows
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # Mã UTF-8
    except:
        pass

def find_file(filename):
    """Tim file trong thu muc hien tai va cac thu muc con"""
    for root, dirs, files in os.walk('.'):
        if filename in files:
            return os.path.abspath(os.path.join(root, filename))
    return None

def is_port_in_use(port):
    """Kiem tra xem cong da duoc su dung chua"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_process(cmd, prefix, resources):
    """Chay mot tien trinh va ghi log output"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Them process vao resources
    if prefix == "IMAGE_MODEL_TRAINER":
        resources['client_process'] = process
    elif prefix == "IMAGE_STREAM":
        resources['server_process'] = process
    
    # Bat dau thread doc output
    def read_output(stream, prefix):
        for line in stream:
            try:
                print(f"{prefix}: {line.strip()}")
            except UnicodeEncodeError:
                # Thay the cac ky tu khong hien thi duoc
                print(f"{prefix}: {line.encode('ascii', 'replace').decode('ascii').strip()}")
    
    # Bat dau thread doc stdout
    stdout_thread = threading.Thread(
        target=read_output,
        args=(process.stdout, prefix),
        daemon=True
    )
    stdout_thread.start()
    
    # Bat dau thread doc stderr
    stderr_thread = threading.Thread(
        target=read_output,
        args=(process.stderr, f"{prefix} ERROR"),
        daemon=True
    )
    stderr_thread.start()
    
    return process

def cleanup_resources(resources):
    """Don dep tai nguyen khi ket thuc chuong trinh"""
    print("\nDang don dep tai nguyen...")
    
    # Dung server process
    if resources.get('server_process') and resources['server_process'].poll() is None:
        try:
            print("Dang dung server...")
            resources['server_process'].terminate()
            try:
                resources['server_process'].wait(timeout=5)
                print("server da dung")
            except subprocess.TimeoutExpired:
                print("server khong dung, buoc kill...")
                resources['server_process'].kill()
                resources['server_process'].wait()
                print("server da bi kill")
        except Exception as e:
            print(f"Loi khi dung server: {e}")
    
    # Dung client process
    if resources.get('client_process') and resources['client_process'].poll() is None:
        try:
            print("Dang dung client...")
            resources['client_process'].terminate()
            try:
                resources['client_process'].wait(timeout=5)
                print("client da dung")
            except subprocess.TimeoutExpired:
                print("client khong dung, buoc kill...")
                resources['client_process'].kill()
                resources['client_process'].wait()
                print("client da bi kill")
        except Exception as e:
            print(f"Loi khi dung client: {e}")

def signal_handler(sig, frame, resources):
    """Xu ly khi nguoi dung nhan Ctrl+C"""
    print("\nDang dung he thong...")
    cleanup_resources(resources)
    sys.exit(0)

def monitor_processes(resources):
    """Theo doi cac tien trinh va dung he thong khi can thiet"""
    client_process = resources.get('client_process')
    server_process = resources.get('server_process')
    
    while True:
        # Kiem tra client
        if client_process and client_process.poll() is not None:
            print("Client da ket thuc. Dang dung server...")
            cleanup_resources(resources)
            break
        
        # Kiem tra server
        if server_process and server_process.poll() is not None:
            print("Server da ket thuc. Dang dung client...")
            cleanup_resources(resources)
            break
        
        time.sleep(1)

def parse_arguments():
    """Phan tich tham so dong lenh"""
    parser = argparse.ArgumentParser(description='Chay he thong phan loai anh')
    parser.add_argument('--folder', type=str, 
                        default="D:/file_ht/PTDLL/ThucHanh_22521522/Lab_4/Anh_batch",
                        help='Duong dan den thu muc anh')
    parser.add_argument('--port', type=int, default=6100,
                        help='Cong ket noi')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Kich thuoc batch')
    parser.add_argument('--dummy', action='store_true',
                        help='Su dung du lieu gia thay vi anh that')
    
    return parser.parse_args()

def main():
    # Phan tich tham so
    args = parse_arguments()
    
    # Kiem tra xem cong da duoc su dung chua
    if is_port_in_use(args.port):
        print(f"Cong {args.port} da duoc su dung. Vui long dong ung dung dang su dung cong nay.")
        sys.exit(1)
    
    # Tim cac file can thiet
    trainer_path = find_file('image_model_trainer.py')
    stream_path = find_file('image_stream.py')
    
    if not trainer_path:
        print("Khong tim thay file image_model_trainer.py")
        sys.exit(1)
    
    if not stream_path:
        print("Khong tim thay file image_stream.py")
        sys.exit(1)
    
    print(f"Da tim thay image_model_trainer.py tai: {trainer_path}")
    print(f"Da tim thay image_stream.py tai: {stream_path}")
    
    # Kiem tra thu muc anh neu khong su dung du lieu gia
    if not args.dummy and not os.path.exists(args.folder):
        print(f"Thu muc anh khong ton tai: {args.folder}")
        print("Ban co muon su dung du lieu gia thay the? (y/n)")
        choice = input().lower()
        if choice == 'y':
            args.dummy = True
        else:
            print("Dang thoat...")
            sys.exit(1)
    
    # Tao resources dict de quan ly tai nguyen
    resources = {
        'client_process': None,
        'server_process': None
    }
    
    # Dang ky handler cho Ctrl+C
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, resources))
    
    # Khoi dong client (image_model_trainer.py)
    print("Dang khoi dong IMAGE_MODEL_TRAINER...")
    client_cmd = [sys.executable, trainer_path]
    print(f"Lenh: {' '.join(client_cmd)}")
    resources['client_process'] = run_process(client_cmd, "IMAGE_MODEL_TRAINER", resources)
    
    # Doi 5 giay de client khoi dong
    print("Doi 5 giay de client khoi dong...")
    time.sleep(5)
    
    # Khoi dong server (image_stream.py)
    print("Dang khoi dong IMAGE_STREAM...")
    server_cmd = [
        sys.executable,
        stream_path,
        "--folder", args.folder,
        "--batch-size", str(args.batch_size),
        "--port", str(args.port)
    ]
    
    # Them tham so --dummy neu can
    if args.dummy:
        server_cmd.append("--dummy")
        print("Su dung du lieu gia thay vi anh that")
    
    print(f"Lenh: {' '.join(server_cmd)}")
    resources['server_process'] = run_process(server_cmd, "IMAGE_STREAM", resources)
    
    print("He thong dang chay. Nhan Ctrl+C de dung.")
    
    # Theo doi cac tien trinh
    monitor_thread = threading.Thread(
        target=monitor_processes,
        args=(resources,),
        daemon=True
    )
    monitor_thread.start()
    
    try:
        # Cho den khi nguoi dung nhan Ctrl+C
        while True:
            time.sleep(1)
            
            # Kiem tra xem thread monitor co con chay khong
            if not monitor_thread.is_alive():
                break
    except KeyboardInterrupt:
        print("\nChuong trinh bi dung boi nguoi dung")
    finally:
        cleanup_resources(resources)

if __name__ == "__main__":
    main()