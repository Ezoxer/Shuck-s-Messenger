import socket
import threading
import json
import random
import string
import logging
from datetime import datetime

class ChatServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.clients = {}
        self.rooms = {}
        self.running = False
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def generate_room_code(self):
        """Генерация уникального кода комнаты"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.rooms:
                return code

    def handle_client(self, client_socket, address):
        """Обработка клиентского соединения"""
        self.logger.info(f"Новое подключение: {address}")
        
        try:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    message = json.loads(data)
                    self.process_message(client_socket, message)
                except json.JSONDecodeError:
                    self.logger.error("Ошибка декодирования JSON")

        except Exception as e:
            self.logger.error(f"Ошибка с клиентом {address}: {e}")
        finally:
            self.remove_client(client_socket)

    def process_message(self, client_socket, message):
        """Обработка входящих сообщений"""
        msg_type = message.get('type')
        
        if msg_type == 'create_room':
            # Создание новой комнаты
            room_code = self.generate_room_code()
            self.rooms[room_code] = {
                'host': client_socket,
                'clients': [client_socket],
                'created_at': datetime.now()
            }
            self.clients[client_socket] = {'room': room_code, 'username': 'Хост'}
            
            response = {
                'type': 'room_created',
                'room_code': room_code,
                'message': f'Комната создана! Код: {room_code}'
            }
            client_socket.send(json.dumps(response).encode('utf-8'))
            
        elif msg_type == 'join_room':
            # Присоединение к комнате
            room_code = message.get('room_code')
            username = message.get('username', 'Участник')
            
            if room_code in self.rooms:
                room = self.rooms[room_code]
                if len(room['clients']) < 10:  # Максимум 10 участников
                    room['clients'].append(client_socket)
                    self.clients[client_socket] = {'room': room_code, 'username': username}
                    
                    # Уведомление всех в комнате
                    join_message = {
                        'type': 'user_joined',
                        'username': username,
                        'message': f'{username} присоединился к чату',
                        'users_count': len(room['clients'])
                    }
                    self.broadcast_to_room(room_code, join_message, exclude=client_socket)
                    
                    # Ответ новому участнику
                    response = {
                        'type': 'room_joined',
                        'room_code': room_code,
                        'message': f'Вы присоединились к комнате {room_code}',
                        'users_count': len(room['clients'])
                    }
                    client_socket.send(json.dumps(response).encode('utf-8'))
                else:
                    response = {'type': 'error', 'message': 'Комната заполнена'}
                    client_socket.send(json.dumps(response).encode('utf-8'))
            else:
                response = {'type': 'error', 'message': 'Комната не найдена'}
                client_socket.send(json.dumps(response).encode('utf-8'))
                
        elif msg_type == 'chat_message':
            # Отправка сообщения в чат
            if client_socket in self.clients:
                room_code = self.clients[client_socket]['room']
                username = self.clients[client_socket]['username']
                
                chat_message = {
                    'type': 'chat_message',
                    'username': username,
                    'message': message.get('message'),
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                self.broadcast_to_room(room_code, chat_message)
                
        elif msg_type == 'webrtc_signal':
            # Пересылка WebRTC сигналов
            if client_socket in self.clients:
                room_code = self.clients[client_socket]['room']
                signal_message = {
                    'type': 'webrtc_signal',
                    'signal': message.get('signal'),
                    'target': message.get('target'),
                    'sender': id(client_socket)
                }
                self.broadcast_to_room(room_code, signal_message, exclude=client_socket)

    def broadcast_to_room(self, room_code, message, exclude=None):
        """Отправка сообщения всем в комнате"""
        if room_code in self.rooms:
            for client in self.rooms[room_code]['clients']:
                if client != exclude:
                    try:
                        client.send(json.dumps(message).encode('utf-8'))
                    except:
                        self.remove_client(client)

    def remove_client(self, client_socket):
        """Удаление клиента"""
        if client_socket in self.clients:
            client_info = self.clients[client_socket]
            room_code = client_info['room']
            username = client_info['username']
            
            if room_code in self.rooms:
                room = self.rooms[room_code]
                if client_socket in room['clients']:
                    room['clients'].remove(client_socket)
                    
                    # Уведомление о выходе пользователя
                    if room['clients']:
                        leave_message = {
                            'type': 'user_left',
                            'username': username,
                            'message': f'{username} покинул чат',
                            'users_count': len(room['clients'])
                        }
                        self.broadcast_to_room(room_code, leave_message)
                    else:
                        # Удаление пустой комнаты
                        del self.rooms[room_code]
            
            del self.clients[client_socket]
            client_socket.close()
            self.logger.info(f"Клиент отключен: {username}")

    def start(self):
        """Запуск сервера"""
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            self.logger.info(f"Сервер запущен на {self.host}:{self.port}")
            self.logger.info("Ожидание подключений...")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.error:
                    break
                    
        except Exception as e:
            self.logger.error(f"Ошибка сервера: {e}")
        finally:
            self.stop()

    def stop(self):
        """Остановка сервера"""
        self.running = False
        for client in list(self.clients.keys()):
            self.remove_client(client)
        self.socket.close()
        self.logger.info("Сервер остановлен")

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()