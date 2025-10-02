#!/usr/bin/env python3
"""
Локальный мессенджер - запускающий скрипт
"""

import subprocess
import sys
import os
import threading
import time

def start_server():
    """Запуск сервера"""
    server_dir = os.path.join(os.path.dirname(__file__), 'server')
    server_script = os.path.join(server_dir, 'server.py')
    
    if os.path.exists(server_script):
        print("Запуск сервера...")
        subprocess.run([sys.executable, server_script])
    else:
        print("Ошибка: серверный скрипт не найден")

def start_client():
    """Запуск клиента"""
    client_dir = os.path.join(os.path.dirname(__file__), 'client')
    client_script = os.path.join(client_dir, 'client.py')
    
    if os.path.exists(client_script):
        print("Запуск клиента...")
        subprocess.run([sys.executable, client_script])
    else:
        print("Ошибка: клиентский скрипт не найден")

def main():
    print("=== Локальный Мессенджер ===")
    print("1. Запустить сервер (создать комнату)")
    print("2. Запустить клиент (присоединиться)")
    print("3. Запустить сервер и клиент")
    print("4. Выход")
    
    choice = input("\nВыберите опцию (1-4): ").strip()
    
    if choice == '1':
        start_server()
    elif choice == '2':
        start_client()
    elif choice == '3':
        # Запуск сервера в отдельном потоке
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Даем серверу время на запуск
        time.sleep(2)
        
        # Запуск клиента
        start_client()
    elif choice == '4':
        print("Выход...")
    else:
        print("Неверный выбор")

if __name__ == "__main__":
    main()