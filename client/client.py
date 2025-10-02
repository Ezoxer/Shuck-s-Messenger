import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
import uuid

class MessengerClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.current_room = None
        self.username = f"User_{uuid.uuid4().hex[:6]}"
        self.peer_connection = None
        
        self.setup_ui()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.root = tk.Tk()
        self.root.title("Локальный Мессенджер")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        self.setup_connection_frame()
        self.setup_chat_frame()
        self.setup_call_frame()
        
        self.show_connection_frame()

    def setup_connection_frame(self):
        """Фрейм подключения"""
        self.connection_frame = ttk.Frame(self.root)
        self.connection_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Заголовок
        title_label = ttk.Label(
            self.connection_frame, 
            text="Локальный Мессенджер", 
            font=('Arial', 20, 'bold'),
            foreground='white'
        )
        title_label.pack(pady=20)
        
        # Фрейм создания комнаты
        create_frame = ttk.LabelFrame(self.connection_frame, text="Создать комнату")
        create_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            create_frame, 
            text="Создать новую комнату", 
            command=self.create_room,
            style='Accent.TButton'
        ).pack(pady=10)
        
        # Разделитель
        separator = ttk.Separator(self.connection_frame, orient='horizontal')
        separator.pack(fill='x', pady=20)
        
        # Фрейм присоединения к комнате
        join_frame = ttk.LabelFrame(self.connection_frame, text="Присоединиться к комнате")
        join_frame.pack(fill='x', pady=10)
        
        ttk.Label(join_frame, text="Имя:").pack(anchor='w')
        self.name_entry = ttk.Entry(join_frame)
        self.name_entry.insert(0, self.username)
        self.name_entry.pack(fill='x', pady=5)
        
        ttk.Label(join_frame, text="Код комнаты:").pack(anchor='w')
        self.room_code_entry = ttk.Entry(join_frame)
        self.room_code_entry.pack(fill='x', pady=5)
        
        ttk.Button(
            join_frame, 
            text="Присоединиться", 
            command=self.join_room
        ).pack(pady=10)
        
        # Статус
        self.status_label = ttk.Label(
            self.connection_frame, 
            text="Не подключен", 
            foreground='red'
        )
        self.status_label.pack(pady=10)

    def setup_chat_frame(self):
        """Фрейм чата"""
        self.chat_frame = ttk.Frame(self.root)
        
        # Панель информации о комнате
        info_frame = ttk.Frame(self.chat_frame)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.room_info_label = ttk.Label(
            info_frame, 
            text="Комната: Не подключен", 
            font=('Arial', 12, 'bold')
        )
        self.room_info_label.pack(side='left')
        
        ttk.Button(
            info_frame, 
            text="Отключиться", 
            command=self.disconnect
        ).pack(side='right')
        
        # Окно чата
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            width=60,
            height=20,
            state='disabled'
        )
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=5)
        self.chat_display.configure(font=('Arial', 10))
        
        # Панель ввода сообщения
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        ttk.Button(
            input_frame, 
            text="Отправить", 
            command=self.send_message
        ).pack(side='right')

    def setup_call_frame(self):
        """Фрейм звонков"""
        self.call_frame = ttk.LabelFrame(self.chat_frame, text="Видеозвонок")
        self.call_frame.pack(fill='x', padx=10, pady=5)
        
        call_buttons_frame = ttk.Frame(self.call_frame)
        call_buttons_frame.pack(fill='x', pady=5)
        
        ttk.Button(
            call_buttons_frame, 
            text="📞 Начать звонок", 
            command=self.start_call,
            style='Accent.TButton'
        ).pack(side='left', padx=5)
        
        ttk.Button(
            call_buttons_frame, 
            text="📹 Показать видео", 
            command=self.toggle_video
        ).pack(side='left', padx=5)
        
        ttk.Button(
            call_buttons_frame, 
            text="🎤 Вкл/Выкл звук", 
            command=self.toggle_audio
        ).pack(side='left', padx=5)
        
        ttk.Button(
            call_buttons_frame, 
            text="🔊 Вкл/Выкл динамик", 
            command=self.toggle_speaker
        ).pack(side='left', padx=5)
        
        # Статус звонка
        self.call_status_label = ttk.Label(
            self.call_frame, 
            text="Готов к звонку", 
            foreground='green'
        )
        self.call_status_label.pack(pady=5)

    def show_connection_frame(self):
        """Показать фрейм подключения"""
        self.chat_frame.pack_forget()
        self.connection_frame.pack(fill='both', expand=True)

    def show_chat_frame(self):
        """Показать фрейм чата"""
        self.connection_frame.pack_forget()
        self.chat_frame.pack(fill='both', expand=True)

    def connect_to_server(self, host='localhost', port=8888):
        """Подключение к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            
            # Запуск потока для прослушивания сообщений
            self.listener_thread = threading.Thread(target=self.listen_to_server)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            self.update_status("Подключен к серверу", 'green')
            return True
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
            return False

    def listen_to_server(self):
        """Прослушивание сообщений от сервера"""
        while self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                messages = data.split('}{')
                for i, msg in enumerate(messages):
                    if i > 0:
                        msg = '{' + msg
                    if i < len(messages) - 1:
                        msg = msg + '}'
                    
                    try:
                        message = json.loads(msg)
                        self.handle_server_message(message)
                    except json.JSONDecodeError:
                        continue
                        
            except Exception as e:
                if self.connected:
                    self.logger.error(f"Ошибка получения данных: {e}")
                break
        
        if self.connected:
            self.disconnect()

    def handle_server_message(self, message):
        """Обработка сообщений от сервера"""
        msg_type = message.get('type')
        
        if msg_type == 'room_created':
            self.current_room = message['room_code']
            self.update_room_info()
            self.show_chat_frame()
            self.add_chat_message("Система", message['message'])
            
        elif msg_type == 'room_joined':
            self.current_room = message['room_code']
            self.update_room_info()
            self.show_chat_frame()
            self.add_chat_message("Система", message['message'])
            
        elif msg_type == 'user_joined':
            self.add_chat_message("Система", message['message'])
            self.update_room_info(f"Участников: {message['users_count']}")
            
        elif msg_type == 'user_left':
            self.add_chat_message("Система", message['message'])
            self.update_room_info(f"Участников: {message['users_count']}")
            
        elif msg_type == 'chat_message':
            self.add_chat_message(
                message['username'], 
                message['message'],
                message.get('timestamp')
            )
            
        elif msg_type == 'webrtc_signal':
            # Обработка WebRTC сигналов (заглушка)
            self.handle_webrtc_signal(message)
            
        elif msg_type == 'error':
            messagebox.showerror("Ошибка", message['message'])

    def create_room(self):
        """Создание новой комнаты"""
        if not self.connected and not self.connect_to_server():
            return
            
        message = {
            'type': 'create_room',
            'username': self.username
        }
        self.send_json(message)

    def join_room(self):
        """Присоединение к комнате"""
        room_code = self.room_code_entry.get().strip().upper()
        self.username = self.name_entry.get().strip() or self.username
        
        if not room_code:
            messagebox.showerror("Ошибка", "Введите код комнаты")
            return
            
        if not self.connected and not self.connect_to_server():
            return
            
        message = {
            'type': 'join_room',
            'room_code': room_code,
            'username': self.username
        }
        self.send_json(message)

    def send_message(self):
        """Отправка сообщения в чат"""
        message = self.message_entry.get().strip()
        if message and self.connected:
            chat_message = {
                'type': 'chat_message',
                'message': message
            }
            self.send_json(chat_message)
            self.message_entry.delete(0, tk.END)

    def send_json(self, data):
        """Отправка JSON данных"""
        try:
            self.socket.send(json.dumps(data).encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Ошибка отправки: {e}")

    def add_chat_message(self, username, message, timestamp=None):
        """Добавление сообщения в чат"""
        self.chat_display.config(state='normal')
        
        if timestamp:
            time_str = f"[{timestamp}] "
        else:
            time_str = ""
            
        if username == "Система":
            tag = "system"
            prefix = "🔔 "
        else:
            tag = "user"
            prefix = f"{username}: "
            
        self.chat_display.insert(tk.END, f"{time_str}{prefix}{message}\n", tag)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
        # Настройка тегов для цветов
        self.chat_display.tag_config("system", foreground="blue")
        self.chat_display.tag_config("user", foreground="black")

    def update_status(self, text, color='black'):
        """Обновление статуса"""
        self.status_label.config(text=text, foreground=color)

    def update_room_info(self, additional_info=""):
        """Обновление информации о комнате"""
        info = f"Комната: {self.current_room}"
        if additional_info:
            info += f" | {additional_info}"
        self.room_info_label.config(text=info)

    def disconnect(self):
        """Отключение от сервера"""
        self.connected = False
        if self.socket:
            self.socket.close()
            self.socket = None
        
        self.current_room = None
        self.show_connection_frame()
        self.update_status("Не подключен", 'red')
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')

    # WebRTC методы (заглушки для реализации)
    def start_call(self):
        """Начать звонок"""
        self.add_chat_message("Система", "Функция звонка активирована (WebRTC)")
        self.call_status_label.config(text="Звонок активен", foreground='red')

    def toggle_video(self):
        """Включить/выключить видео"""
        self.add_chat_message("Система", "Переключение видео")

    def toggle_audio(self):
        """Включить/выключить аудио"""
        self.add_chat_message("Система", "Переключение аудио")

    def toggle_speaker(self):
        """Включить/выключить динамик"""
        self.add_chat_message("Система", "Переключение динамика")

    def handle_webrtc_signal(self, signal):
        """Обработка WebRTC сигналов"""
        # Здесь будет реализация обработки WebRTC сигналов
        pass

    def run(self):
        """Запуск клиента"""
        # Настройка стилей
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка цветовой схемы
        self.root.configure(bg='#2b2b2b')
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.disconnect()

if __name__ == "__main__":
    client = MessengerClient()
    client.run()