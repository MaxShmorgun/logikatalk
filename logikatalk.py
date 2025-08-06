import customtkinter as ctk
from tkinter import messagebox, filedialog, Text
import threading
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, error as socket_error

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class LogiTalkApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LogiTalk")
        self.geometry("700x500")
        self.minsize(500, 300)

       
        self.username = None
        self.host = None
        self.port = None
        self.sock = None
        self.connected = False

        
        self.chat_box = None
        self.reg_win = None
        self.name_entry = None
        self.host_entry = None
        self.port_entry = None
        self.msg_entry = None
        self._current_color_index = 0

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.open_registration_form()

    def open_registration_form(self):
        """ Створює та відображає вікно реєстрації/входу згідно з наданим зображенням. """
        self.reg_win = ctk.CTkToplevel(self)
        self.reg_win.title("Вхід в LogiTalk")
        self.reg_win.geometry("350x220")
        self.reg_win.grab_set()
        self.reg_win.protocol("WM_DELETE_WINDOW", self.on_closing_reg_window)

       
        form_frame = ctk.CTkFrame(self.reg_win, fg_color="transparent")
        form_frame.pack(pady=(20, 10), padx=20, fill="x")

       
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Введіть ім'я")
        self.name_entry.pack(pady=5, fill="x")
        self.name_entry.focus()

        
        self.host_entry = ctk.CTkEntry(form_frame, placeholder_text="Введіть ХОСТ сервера")
        self.host_entry.pack(pady=5, fill="x")
       
       
        self.port_entry = ctk.CTkEntry(form_frame, placeholder_text="Введіть порт сервера")
        self.port_entry.pack(pady=5, fill="x")
        

        
        ctk.CTkButton(self.reg_win, text="Зареєструватися", command=self.register_user).pack(pady=10, padx=20, fill="x")
        
        
        self.name_entry.bind("<Return>", lambda e: self.host_entry.focus())
        self.host_entry.bind("<Return>", lambda e: self.port_entry.focus())
        self.port_entry.bind("<Return>", lambda e: self.register_user())


    def on_closing_reg_window(self):
        if not self.username:
            print("Реєстрацію скасовано. Закриття програми.")
            self.destroy()
        elif self.reg_win:
            self.reg_win.destroy()
            self.reg_win = None

    def register_user(self):
        """ Зчитує дані з форми, перевіряє їх і запускає основний інтерфейс. """
        name = self.name_entry.get().strip()
        host = self.host_entry.get().strip()
        port_str = self.port_entry.get().strip()

        if not name or not host or not port_str:
            messagebox.showwarning("Помилка вводу", "Всі поля повинні бути заповнені.", parent=self.reg_win)
            return

        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Помилка вводу", "Порт має бути числом від 1 до 65535.", parent=self.reg_win)
            return

        self.username = name
        self.host = host
        self.port = port

        if self.reg_win:
            self.reg_win.destroy()
            self.reg_win = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing_main_window)
        self.build_main_ui()
        self.connect_to_server()

    def build_main_ui(self):
        sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="Налаштування", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkButton(sidebar, text="Змінити тему", command=self.toggle_theme).pack(pady=5, fill="x", padx=5)
        ctk.CTkButton(sidebar, text="Змінити колір", command=self.toggle_color).pack(pady=5, fill="x", padx=5)
        ctk.CTkButton(sidebar, text="Про програму", command=self.show_about).pack(pady=(15,5), fill="x", padx=5)

        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main_area.grid_rowconfigure(0, weight=1)
        main_area.grid_columnconfigure(0, weight=1)

        chat_frame = ctk.CTkFrame(main_area)
        chat_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        ctk_theme = ctk.ThemeManager.theme
        text_bg_color = ctk_theme["CTkFrame"]["fg_color"]
        text_fg_color = ctk_theme["CTkLabel"]["text_color"]

        self.chat_box = Text(chat_frame, state="disabled", wrap="word", font=("Arial", 11),
                             bg=self._apply_appearance_mode(text_bg_color),
                             fg=self._apply_appearance_mode(text_fg_color),
                             relief="sunken", borderwidth=1)
        self.chat_box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(chat_frame, command=self.chat_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_box.configure(yscrollcommand=scrollbar.set)

        self.chat_box.tag_config("system", foreground="gray")
        user_message_color_tuple = ctk_theme["CTkButton"]["fg_color"]
        user_message_color = self._apply_appearance_mode(user_message_color_tuple)
        self.chat_box.tag_config("user", foreground=user_message_color)
        self.chat_box.tag_config("other", foreground="#00A000")

        bottom_frame = ctk.CTkFrame(main_area)
        bottom_frame.grid(row=1, column=0, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.msg_entry = ctk.CTkEntry(bottom_frame, placeholder_text="Введіть повідомлення...")
        self.msg_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())

        ctk.CTkButton(bottom_frame, text="Надіслати", command=self.send_message).grid(row=0, column=1, pady=5, padx=(0,5))


        self._append_message("", f"Ласкаво просимо, {self.username}!", "system")

    def connect_to_server(self):
        """ Підключається до сервера, використовуючи дані, введені користувачем. """
        if not self.host or not self.port:
            self._append_message("", "Хост або порт не вказано.", "system")
            self.connected = False
            return
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)

            self._append_message("", f"Підключення до {self.host}:{self.port}...", "system")
            self.sock.connect((self.host, self.port))
            self.connected = True

            connect_msg = f"Приєднався: {self.username} \n"
            self.sock.send(connect_msg.encode('utf-8'))

            threading.Thread(target=self.recv_message, daemon=True).start()
        except socket_error as e:
            self._append_message("", f"Помилка підключення сокета: {str(e)}.", "system")
            self.connected = False
        except Exception as e:
            self._append_message("", f"Загальна помилка підключення: {str(e)}.", "system")
            self.connected = False

    def _append_message(self, prefix_text: str, main_text: str, tag: str):
        if not self.chat_box: return
        self.chat_box.configure(state="normal")
        if prefix_text:
            self.chat_box.insert("end", prefix_text, tag)
        self.chat_box.insert("end", main_text, tag)
        self.chat_box.insert("end", "\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg: return
        if not self.connected:
            self._append_message("", "Немає з'єднання з сервером.", "system")
            return

        try:
            message_payload = f"{self.username}: {msg}\n"
            self.sock.send(message_payload.encode('utf-8'))
            self._append_message(f"{self.username}: ", msg, "user")
            self.msg_entry.delete(0, "end")
        except Exception as e:
            self._append_message("", f"Помилка відправки: {str(e)}", "system")
            self.connected = False

    def recv_message(self):
        buffer = ""
        while True:
            if not self.connected:
                break
            try:
                data = self.sock.recv(1024)
                if not data:
                    if self.connected:
                        self._append_message("", "Сервер розірвав з'єднання.", "system")
                        self.connected = False
                    break

                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self.process_server_message(line)
            except ConnectionResetError:
                if self.connected:
                    self._append_message("", "З'єднання з сервером було раптово розірвано.", "system")
                self.connected = False
                break
            except UnicodeDecodeError:
                self._append_message("", "Помилка декодування отриманих даних (не UTF-8).", "system")
                buffer = ""
                continue
            except socket_error as e:
                if self.connected:
                    self._append_message("", f"Помилка сокета при отриманні даних: {str(e)}", "system")
                self.connected = False
                break
            except Exception as e:
                if self.connected:
                    self._append_message("", f"Помилка отримання даних: {str(e)}", "system")
                self.connected = False
                break

    def process_server_message(self, message_str: str):
        server_prefix = "Сервер: "
        if message_str.startswith(server_prefix):
            message_str = message_str[len(server_prefix):].strip()

        message_str = message_str.strip()

        try:
            if '::' in message_str:
                parts = message_str.split('::', 2)
                msg_type = parts[0].upper()
                sender = parts[1]
                content = parts[2] if len(parts) > 2 else ""

                if msg_type == "MSG":
                    if sender != self.username:
                        self._append_message(f"{sender}: ", content, "other")
                elif msg_type == "NOTIF":
                    if sender.upper() == "SERVER":
                        self._append_message("", content, "system")
                    else:
                        self._append_message("", f"{sender} {content}", "system")
                elif msg_type == "CONN_ACK":
                    self._append_message("", content, "system")
                else:
                    self._append_message("", f"Невідомий тип '::' ({message_str})", "system")
                return

            parts_at = message_str.split('@')
            if len(parts_at) == 3 and parts_at[0].upper() == "ТЕКСТ":
                sender = parts_at[1]
                content = parts_at[2]
                if sender.upper() == "СИСТЕМА" or sender.upper() == "SERVER":
                    self._append_message("", content, "system")
                elif sender != self.username:
                    self._append_message(f"{sender}: ", content, "other")
                return

            if len(parts_at) == 2 :
                sender = parts_at[0]
                content = parts_at[1]
                if sender.upper() == "СИСТЕМА" or sender.upper() == "SERVER":
                    self._append_message("", content, "system")
                elif sender != self.username:
                    self._append_message(f"{sender}: ", content, "other")
                return

            self._append_message("", message_str, "system")

        except IndexError:
            self._append_message("", f"Пошкоджене повідомлення від сервера: {message_str}", "system")
        except Exception as e:
            self._append_message("", f"Помилка обробки повідомлення '{message_str}': {e}", "system")

    def _apply_appearance_mode(self, color):
        if isinstance(color, (list, tuple)) and len(color) == 2:
            return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]
        return color

    def _update_widget_colors(self):
        if self.chat_box:
            ctk_theme = ctk.ThemeManager.theme
            text_bg_color = self._apply_appearance_mode(ctk_theme["CTkFrame"]["fg_color"])
            text_fg_color = self._apply_appearance_mode(ctk_theme["CTkLabel"]["text_color"])
            user_message_color_tuple = ctk_theme["CTkButton"]["fg_color"]
            user_message_color = self._apply_appearance_mode(user_message_color_tuple)

            self.chat_box.configure(bg=text_bg_color, fg=text_fg_color)
            self.chat_box.tag_config("user", foreground=user_message_color)

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Dark" if current_mode == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self._update_widget_colors()

    def toggle_color(self):
        colors = ["blue", "green", "dark-blue"]
        self._current_color_index = (self._current_color_index + 1) % len(colors)
        new_color_theme_name = colors[self._current_color_index]

        try:
            ctk.set_default_color_theme(new_color_theme_name)
            self._update_widget_colors()
            messagebox.showinfo("Зміна кольору", f"Колірну тему змінено на '{new_color_theme_name}'. "
                                              "Для деяких елементів може знадобитися перезапуск програми.", parent=self)
        except Exception as e:
            messagebox.showerror("Помилка зміни кольору", f"Не вдалося повністю застосувати тему '{new_color_theme_name}': {e}", parent=self)

    def show_about(self):
        messagebox.showinfo("Про програму", "LogiTalk v1.3 (Simple Text)\nПростий текстовий чат-клієнт.")

    def on_closing_main_window(self):
        if self.username and self.sock:
            if self.connected:
                try:
                    disconnect_msg = f"Відключився: {self.username} \n"
                    self.sock.send(disconnect_msg.encode('utf-8'))
                except socket_error:
                    pass
                except Exception:
                    pass

                try:
                    self.sock.shutdown(SHUT_RDWR)
                except socket_error as e:
                    if hasattr(e, 'errno') and (e.errno == 10057 or e.errno == 107): # Not connected
                        pass
                    else:
                        pass
                except Exception:
                    pass

            try:
                self.sock.close()
            except socket_error:
                pass
            except Exception:
                pass

        self.connected = False
        self.destroy()

if __name__ == "__main__":
    app = LogiTalkApp()
    app.mainloop()
