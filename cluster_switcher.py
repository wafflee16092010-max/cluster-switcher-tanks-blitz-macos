import os
import sys
import subprocess
import logging
import tempfile
import json
import webbrowser
import threading
import traceback
import urllib.request
import urllib.error
from logging.handlers import RotatingFileHandler

# логи с ротацией, чтобы файл не рос бесконечно
LOG_DIR = os.path.expanduser("~/.cluster_switcher")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.txt")
SETTINGS_FILE = os.path.join(LOG_DIR, "settings.json")

logger = logging.getLogger("cluster_switcher")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE, maxBytes=512000, backupCount=3, encoding="utf-8")
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
logger.addHandler(handler)
logger.info("=== Старт ===")

import tkinter as tk
from tkinter import ttk, messagebox

# цвета для crash-окна заданы заранее, на случай если краш до загрузки темы
CRASH_BG = "#1a1a1a"
CRASH_FG = "#ffffff"

# --- пути ---
HOSTS_PATH = "/etc/hosts"
HOSTS_BACKUP = "/etc/hosts.backup.cluster_switcher"

# кластеры и их адреса
CLUSTERS = {
    "RU_C0": "login0.tanksblitz.ru",
    "RU_C1": "login1.tanksblitz.ru",
    "RU_C2": "login2.tanksblitz.ru",
    "RU_C3": "login3.tanksblitz.ru",
    "RU_C4": "login4.tanksblitz.ru",
    "RU_C5": "login5.tanksblitz.ru",
}

# --- переводы ---
LANG = {
    "ru": {
        "title": "Tanks Blitz Cluster Switcher",
        "label": "Выбери кластеры для блокировки:",
        "apply": "Применить",
        "refresh": "Обновить статус",
        "blocked": "Заблокированы:",
        "none": "Ничего не заблокировано",
        "error_admin": "Ошибка прав администратора",
        "info_blocked": "Заблокированы: {}",
        "info_none": "Все разблокированы.",
        "info_done": "Готово",
        "clusters": {
            "RU_C0": "RU_C0 (Москва)",
            "RU_C1": "RU_C1 (Москва)",
            "RU_C2": "RU_C2 (Красноярск)",
            "RU_C3": "RU_C3 (Екатеринбург)",
            "RU_C4": "RU_C4 (не работает)",
            "RU_C5": "RU_C5 (не работает)",
        },
        "donate": "Поддержать разработчика",
        "contact": "Свяжись со мной:",
        "about": "О программе",
        "check_updates": "Проверить обновления",
        "select_all": "Выбрать все",
        "deselect_all": "Снять все",
        "open_folder": "Открыть папку",
        "about_desc": "Утилита для управления блокировкой кластеров Tanks Blitz",
        "about_features_list": ["Блокировка кластеров", "Переключение языков", "Автозапрос прав админа", "Очистка DNS-кэша", "Защита от сбоев"],
        "warn_all": "Стоп!",
        "warn_all_text": "Ты выбрал ВСЕ кластеры!\n\nЭто заблокирует все сервера Tanks Blitz — игра вообще не запустится.\n\nСними хотя бы один кластер, чтобы оставить доступ к игре.",
        "last_action_block": "Последнее: заблокированы {}",
        "last_action_unblock": "Последнее: все разблокированы",
        "about_title": "О программе",
        "about_features": "ФУНКЦИИ:",
        "about_contacts": "КОНТАКТЫ РАЗРАБОТЧИКА:",
        "about_close": "[ ЗАКРЫТЬ ]",
        "upd_title": "Проверка обновлений",
        "upd_checking": "Проверка обновлений...",
        "upd_found": "Обновление найдено!",
        "upd_new": "Новая версия: {}",
        "upd_current": "Текущая версия: {}",
        "upd_changes": "Изменения:",
        "upd_download": "Скачать",
        "upd_later": "Позже",
        "upd_latest": "Вы используете последнюю версию!",
        "upd_ok": "ОК",
        "upd_error": "Ошибка проверки",
        "restore_title": "Восстановление hosts",
        "restore_btn": "Восстановить hosts",
        "restore_no_backup": "Резервная копия не найдена.\n\nСначала заблокируй хотя бы один кластер — тогда создастся бэкап.",
        "restore_success": "Файл hosts восстановлен из резервной копии.\nDNS-кэш очищен.",
        "restore_confirm": "Восстановить hosts из последней резервной копии?\n\nЭто отменит все текущие блокировки.",
        "password_cancel": "Отмена",
        "password_cancel_text": "Ты отменил ввод пароля.\n\nИзменения не были применены.",
    },
    "en": {
        "title": "Tanks Blitz Cluster Switcher",
        "label": "Select clusters to block:",
        "apply": "Apply",
        "refresh": "Refresh status",
        "blocked": "Blocked:",
        "none": "Nothing is blocked",
        "error_admin": "Admin rights error",
        "info_blocked": "Blocked: {}",
        "info_none": "All unblocked.",
        "info_done": "Done",
        "clusters": {
            "RU_C0": "RU_C0 (Moscow)",
            "RU_C1": "RU_C1 (Moscow)",
            "RU_C2": "RU_C2 (Krasnoyarsk)",
            "RU_C3": "RU_C3 (Yekaterinburg)",
            "RU_C4": "RU_C4 (down)",
            "RU_C5": "RU_C5 (down)",
        },
        "donate": "Support the developer",
        "contact": "Contact me:",
        "about": "About",
        "check_updates": "Check for updates",
        "select_all": "Select all",
        "deselect_all": "Deselect all",
        "open_folder": "Open folder",
        "about_desc": "Utility for managing Tanks Blitz cluster blocking",
        "about_features_list": ["Cluster blocking", "Language switching", "Auto admin privileges", "DNS cache flush", "Crash protection"],
        "warn_all": "Stop!",
        "warn_all_text": "You selected ALL clusters!\n\nThis will block all Tanks Blitz servers — the game won't launch at all.\n\nUncheck at least one cluster to keep access to the game.",
        "last_action_block": "Last: blocked {}",
        "last_action_unblock": "Last: all unblocked",
        "about_title": "About",
        "about_features": "FEATURES:",
        "about_contacts": "DEVELOPER CONTACTS:",
        "about_close": "[ CLOSE ]",
        "upd_title": "Check for updates",
        "upd_checking": "Checking for updates...",
        "upd_found": "Update found!",
        "upd_new": "New version: {}",
        "upd_current": "Current version: {}",
        "upd_changes": "Changes:",
        "upd_download": "Download",
        "upd_later": "Later",
        "upd_latest": "You're using the latest version!",
        "upd_ok": "OK",
        "upd_error": "Check failed",
        "restore_title": "Restore hosts",
        "restore_btn": "Restore hosts",
        "restore_no_backup": "Backup not found.\n\nBlock at least one cluster first — a backup will be created then.",
        "restore_success": "Hosts file restored from backup.\nDNS cache flushed.",
        "restore_confirm": "Restore hosts from the last backup?\n\nThis will undo all current blocks.",
        "password_cancel": "Cancelled",
        "password_cancel_text": "You cancelled the password prompt.\n\nNo changes were made.",
    }
}

# --- ссылки и версия ---
DONATE_URL = "https://pay.cloudtips.ru/p/0733bd19"
APP_VERSION = "1.0.0"

def version_tuple(v):
    # "1.10.0" -> (1, 10, 0), чтобы сравнение работало нормально
    return tuple(int(x) for x in v.replace("v", "").split("."))

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Не загрузились настройки: {e}")
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
    except Exception as e:
        logger.error(f"Не сохранились настройки: {e}")

# --- открытие ссылок ---
def open_donate():
    webbrowser.open(DONATE_URL)

def open_telegram():
    webbrowser.open("https://t.me/waffleeb")

def open_github():
    webbrowser.open("https://github.com/wafflee16092010-max/cluster-switcher-tanks-blitz-macos")

def open_email():
    webbrowser.open("mailto:artemtkacev417@email.com")

def open_app_folder():
    # для .app надо подняться на 3 уровня от executable, чтобы найти папку с самим .app
    if getattr(sys, 'frozen', False):
        app_folder = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
    else:
        app_folder = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(["open", app_folder])

# --- crash handler ---
def show_crash_message(error_text):
    crash_window = tk.Toplevel()
    crash_window.title("Что-то пошло не так")
    crash_window.geometry("500x350")
    crash_window.configure(bg=CRASH_BG)
    crash_window.resizable(False, False)

    tk.Label(crash_window, text="Программа упала с ошибкой", bg=CRASH_BG, fg="#ff4444", font=("SF Pro Text", 14, "bold")).pack(pady=10)
    tk.Label(crash_window, text=error_text, bg=CRASH_BG, fg=CRASH_FG, font=("Helvetica Neue", 8), wraplength=460, justify="left").pack(pady=5, padx=15, fill="x")
    tk.Frame(crash_window, height=10, bg=CRASH_BG).pack()
    tk.Label(crash_window, text="Свяжись со мной, я помогу разобраться:", bg=CRASH_BG, fg=CRASH_FG, font=("SF Pro Text", 11)).pack()
    tk.Label(crash_window, text="Telegram: @waffleeb", bg=CRASH_BG, fg="#4fc3f7", font=("SF Pro Text", 10, "bold")).pack()
    tk.Label(crash_window, text="GitHub: github.com/wafflee16092010-max", bg=CRASH_BG, fg="#4fc3f7", font=("SF Pro Text", 10, "bold")).pack()
    tk.Label(crash_window, text="Почта: artemtkacev417@email.com", bg=CRASH_BG, fg="#4fc3f7", font=("SF Pro Text", 10, "bold")).pack()
    tk.Button(crash_window, text="Закрыть", command=crash_window.destroy, bg="#555", fg="white", font=("SF Pro Text", 10, "bold")).pack(pady=15)

def global_exception_handler(exc_type, exc_value, exc_tb):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    show_crash_message(error_msg)

sys.excepthook = global_exception_handler

# --- блокировка через osascript ---
def run_admin_script(commands):
    """Выполняет список shell-команд с правами админа через osascript.
    Возвращает (success, error_msg)."""
    script_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False, prefix='cluster_sw_') as f:
            for cmd in commands:
                f.write(cmd + "\n")
            script_path = f.name

        applescript = f'do shell script "sh {script_path}" with administrator privileges'
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)

        if result.returncode != 0:
            stderr = result.stderr or ""
            # юзер нажал "отмена" в окне пароля — проверяем на разных языках
            lower = stderr.lower()
            if "-128" in stderr or "cancel" in lower or "отмен" in lower:
                return False, None
            return False, stderr.strip()

        return True, None
    except Exception as e:
        logger.error(f"osascript упал: {e}")
        return False, str(e)
    finally:
        if script_path:
            try:
                os.unlink(script_path)
            except Exception:
                pass

def apply_blocking(selected_clusters):
    """Пишет блокировки в hosts через osascript."""
    logger.info(f"Запрос блокировки: {', '.join(selected_clusters) if selected_clusters else 'нет'}")

    commands = [
        f"cp '{HOSTS_PATH}' '{HOSTS_BACKUP}'",
        f"sed -i '' '/127.0.0.1 login/d' '{HOSTS_PATH}'",
    ]
    for key in selected_clusters:
        if key in CLUSTERS:
            commands.append(f"echo '127.0.0.1 {CLUSTERS[key]}' >> '{HOSTS_PATH}'")
    commands.append("dscacheutil -flushcache")
    commands.append("killall -HUP mDNSResponder")

    success, error_msg = run_admin_script(commands)
    lang = LANG[current_lang]

    if not success:
        if error_msg:
            logger.error(f"Ошибка osascript: {error_msg}")
            messagebox.showerror(lang["error_admin"], error_msg)
        else:
            logger.info("Юзер отменил ввод пароля")
            messagebox.showinfo(lang["password_cancel"], lang["password_cancel_text"])
        return False

    logger.info("Блокировка применена, DNS сброшен")
    if selected_clusters:
        names = [lang["clusters"][k] for k in selected_clusters if k in lang["clusters"]]
        messagebox.showinfo(lang["info_done"], lang["info_blocked"].format(', '.join(names)))
    else:
        messagebox.showinfo(lang["info_done"], lang["info_none"])
    return True

def restore_hosts_from_backup():
    """Откатывает hosts из бэкапа."""
    if not os.path.exists(HOSTS_BACKUP):
        lang = LANG[current_lang]
        messagebox.showwarning(lang["restore_title"], lang["restore_no_backup"])
        logger.warning("Восстановление — бэкап не найден")
        return

    success, error_msg = run_admin_script([
        f"cp '{HOSTS_BACKUP}' '{HOSTS_PATH}'",
        "dscacheutil -flushcache",
        "killall -HUP mDNSResponder",
    ])
    lang = LANG[current_lang]

    if not success:
        if error_msg:
            logger.error(f"Ошибка восстановления: {error_msg}")
            messagebox.showerror(lang["restore_title"], error_msg)
        else:
            logger.info("Юзер отменил восстановление")
            messagebox.showinfo(lang["password_cancel"], lang["password_cancel_text"])
        return

    logger.info("Hosts восстановлен из бэкапа")
    messagebox.showinfo(lang["info_done"], lang["restore_success"])
    update_status_text()

# --- обработчики кнопок ---
def on_apply():
    selected = [k for k in cluster_keys if checkboxes[k].get()]

    # если выбрал всё — не пускаем
    if len(selected) == len(cluster_keys):
        lang = LANG[current_lang]
        messagebox.showwarning(lang["warn_all"], lang["warn_all_text"])
        logger.warning("Попытка заблокировать все кластеры — заблокировано")
        return

    result = apply_blocking(selected)
    lang = LANG[current_lang]
    if result:
        btn_apply.config(bg=BTN_GREEN_BG, fg=BTN_FG)
        btn_apply._original_bg = BTN_GREEN_BG
        if selected:
            names = [lang["clusters"][k] for k in selected if k in lang["clusters"]]
            action_label.config(text=lang["last_action_block"].format(', '.join(names)))
        else:
            action_label.config(text=lang["last_action_unblock"])
    else:
        btn_apply.config(bg=BTN_GRAY_BG, fg=BTN_GRAY_FG)
        btn_apply._original_bg = BTN_GRAY_BG
    update_status_text()

def on_restore_hosts():
    lang = LANG[current_lang]
    if not os.path.exists(HOSTS_BACKUP):
        messagebox.showwarning(lang["restore_title"], lang["restore_no_backup"])
        return
    if messagebox.askyesno(lang["restore_title"], lang["restore_confirm"]):
        restore_hosts_from_backup()

def update_status_text():
    blocked = get_current_blocked()
    lang = LANG[current_lang]
    if blocked:
        names = [lang["clusters"][k] for k in blocked if k in lang["clusters"]]
        status_label.config(text=f"{lang['blocked']} {', '.join(names)}", fg="#ffaa00")
    else:
        status_label.config(text=lang["none"], fg="#88ff88")

def on_refresh():
    update_status_text()

def get_current_blocked():
    try:
        if not os.path.exists(HOSTS_PATH):
            return []
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Не удалось прочитать hosts: {e}")
        return []
    blocked = []
    for line in lines:
        for key, value in CLUSTERS.items():
            if f"127.0.0.1 {value}" in line and key not in blocked:
                blocked.append(key)
                break
    return blocked

# --- окно "О программе" ---
def show_about():
    lang = LANG[current_lang]
    about = tk.Toplevel(root)
    about.title(lang["about_title"])
    about.geometry("450x500")
    about.configure(bg="#1a1a1a")
    about.resizable(False, False)
    about.transient(root)

    # по центру относительно главного окна
    about.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - 450) // 2
    y = root.winfo_y() + (root.winfo_height() - 500) // 2
    about.geometry(f"+{x}+{y}")

    # скролл
    main_canvas = tk.Canvas(about, bg="#1a1a1a", highlightthickness=0)
    scrollbar = tk.Scrollbar(about, orient="vertical", command=main_canvas.yview)
    scrollable_frame = tk.Frame(main_canvas, bg="#1a1a1a")
    scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
    main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    main_canvas.configure(yscrollcommand=scrollbar.set)
    main_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    content = tk.Frame(scrollable_frame, bg="#1a1a1a", padx=20, pady=20)
    content.pack(fill="both", expand=True)

    tk.Label(content, text="TANKS BLITZ", bg="#1a1a1a", fg="#ff6600", font=("SF Pro Text", 22, "bold")).pack()
    tk.Label(content, text="CLUSTER SWITCHER", bg="#1a1a1a", fg="#ff6600", font=("SF Pro Text", 14, "bold")).pack()
    tk.Label(content, text=f"v{APP_VERSION}", bg="#1a1a1a", fg="#888888", font=("SF Pro Text", 10)).pack(pady=(0, 15))

    tk.Frame(content, height=2, bg="#ff6600").pack(fill="x", pady=5)
    tk.Label(content, text=lang["about_desc"], bg="#1a1a1a", fg="#cccccc", font=("SF Pro Text", 10), justify="center").pack(pady=10)
    tk.Frame(content, height=1, bg="#333333").pack(fill="x", pady=10)

    # функции
    tk.Label(content, text="▸ " + lang["about_features"], bg="#1a1a1a", fg="#ff6600", font=("SF Pro Text", 10, "bold")).pack(anchor="w", pady=(0, 5))
    for feature in lang["about_features_list"]:
        tk.Label(content, text=f"  ✓ {feature}", bg="#1a1a1a", fg="#44bb44", font=("SF Pro Text", 9, "bold")).pack(anchor="w", pady=1)

    tk.Frame(content, height=1, bg="#333333").pack(fill="x", pady=10)

    # контакты
    tk.Label(content, text="▸ " + lang["about_contacts"], bg="#1a1a1a", fg="#ff6600", font=("SF Pro Text", 10, "bold")).pack(anchor="w", pady=(0, 5))
    for name, text, cmd in [
        ("Telegram", "@waffleeb", open_telegram),
        ("GitHub", "wafflee16092010-max", open_github),
        ("Email", "artemtkacev417@email.com", open_email),
    ]:
        lbl = tk.Label(content, text=f"  {name}: {text}", bg="#1a1a1a", fg="#4fc3f7", font=("SF Pro Text", 9), cursor="hand2")
        lbl.pack(anchor="w", pady=2)
        lbl.bind("<Button-1>", lambda e, c=cmd: c())
        lbl.bind("<Enter>", lambda e: lbl.config(fg="#88ddff"))
        lbl.bind("<Leave>", lambda e: lbl.config(fg="#4fc3f7"))

    tk.Frame(content, height=1, bg="#333333").pack(fill="x", pady=15)

    def cleanup_and_close():
        main_canvas.unbind_all("<MouseWheel>")
        about.destroy()

    tk.Button(content, text=lang["about_close"], command=cleanup_and_close,
              bg="#333333", fg="#ff6600", font=("SF Pro Text", 10, "bold"),
              activebackground="#444444", activeforeground="#ff6600",
              relief="flat", borderwidth=2, highlightthickness=1, highlightbackground="#ff6600").pack(pady=(0, 10))

# --- проверка обновлений ---
def check_updates():
    lang = LANG[current_lang]

    update_window = tk.Toplevel(root)
    update_window.title(lang["upd_title"])
    update_window.geometry("400x250")
    update_window.configure(bg=BG_COLOR)
    update_window.transient(root)

    update_window.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - 400) // 2
    y = root.winfo_y() + (root.winfo_height() - 250) // 2
    update_window.geometry(f"+{x}+{y}")

    content_frame = tk.Frame(update_window, bg=BG_COLOR, padx=20, pady=20)
    content_frame.pack(fill="both", expand=True)

    tk.Label(content_frame, text=lang["upd_checking"], bg=BG_COLOR, fg=FG_COLOR, font=("SF Pro Text", 12)).pack(pady=20)

    def check():
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/wafflee16092010-max/cluster-switcher-tanks-blitz-macos/releases/latest",
                headers={"User-Agent": "Python"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest = data.get("tag_name", "0.0.0")

                for w in content_frame.winfo_children():
                    w.destroy()

                if version_tuple(latest) > version_tuple(APP_VERSION):
                    tk.Label(content_frame, text=lang["upd_found"], bg=BG_COLOR, fg="#88ff88", font=("SF Pro Text", 14, "bold")).pack(pady=10)
                    tk.Label(content_frame, text=lang["upd_new"].format(latest), bg=BG_COLOR, fg=FG_COLOR, font=("SF Pro Text", 11)).pack(pady=5)
                    tk.Label(content_frame, text=lang["upd_current"].format(APP_VERSION), bg=BG_COLOR, fg="#666666", font=("SF Pro Text", 10)).pack()

                    if data.get("body"):
                        tk.Label(content_frame, text=lang["upd_changes"], bg=BG_COLOR, fg=FG_COLOR, font=("SF Pro Text", 9, "bold")).pack(pady=(10, 2))
                        desc = data["body"][:300] + "..." if len(data["body"]) > 300 else data["body"]
                        tk.Label(content_frame, text=desc, bg=BG_COLOR, fg="#d4d4d4", font=("SF Pro Text", 9), justify="left").pack(pady=5)

                    btn_frame = tk.Frame(content_frame, bg=BG_COLOR)
                    btn_frame.pack(pady=10)
                    tk.Button(btn_frame, text=lang["upd_download"], command=lambda: [open_github(), update_window.destroy()],
                              bg="#2b7a2b", fg="white", font=("SF Pro Text", 10, "bold"), cursor="hand2",
                              activebackground="#3c9e3c", relief="flat").pack(side="left", padx=5)
                    tk.Button(btn_frame, text=lang["upd_later"], command=update_window.destroy,
                              bg="#555555", fg="white", font=("SF Pro Text", 10), cursor="hand2",
                              activebackground="#777777", relief="flat").pack(side="left", padx=5)
                else:
                    tk.Label(content_frame, text=lang["upd_latest"], bg=BG_COLOR, fg="#88ff88", font=("SF Pro Text", 12, "bold")).pack(pady=20)
                    tk.Label(content_frame, text=f"v{APP_VERSION}", bg=BG_COLOR, fg=FG_COLOR, font=("SF Pro Text", 10)).pack()
                    tk.Button(content_frame, text=lang["upd_ok"], command=update_window.destroy,
                              bg="#555555", fg="white", font=("SF Pro Text", 10), cursor="hand2",
                              activebackground="#777777", relief="flat").pack(pady=10)

        except urllib.error.HTTPError as e:
            for w in content_frame.winfo_children():
                w.destroy()
            tk.Label(content_frame, text=lang["upd_error"], bg=BG_COLOR, fg="#ff4444", font=("SF Pro Text", 12, "bold")).pack(pady=10)
            if e.code == 404:
                tk.Label(content_frame, text="GitHub repo not found", bg=BG_COLOR, fg=FG_COLOR, font=("SF Pro Text", 9)).pack(pady=5)
            else:
                tk.Label(content_frame, text=f"HTTP {e.code}", bg=BG_COLOR, fg=FG_COLOR, font=("SF Pro Text", 9)).pack(pady=5)
            tk.Button(content_frame, text=lang["upd_ok"], command=update_window.destroy,
                      bg="#555555", fg="white", font=("SF Pro Text", 10), cursor="hand2",
                      activebackground="#777777", relief="flat").pack(pady=10)
        except Exception as e:
            for w in content_frame.winfo_children():
                w.destroy()
            tk.Label(content_frame, text=lang["upd_error"], bg=BG_COLOR, fg="#ff4444", font=("SF Pro Text", 12, "bold")).pack(pady=10)
            tk.Label(content_frame, text=str(e), bg=BG_COLOR, fg=FG_COLOR, font=("SF Pro Text", 9)).pack(pady=5)
            tk.Button(content_frame, text=lang["upd_ok"], command=update_window.destroy,
                      bg="#555555", fg="white", font=("SF Pro Text", 10), cursor="hand2",
                      activebackground="#777777", relief="flat").pack(pady=10)

    root.after(100, check)

def quit_app():
    root.destroy()
    sys.exit(0)

# --- настройки и цвета ---
current_lang = load_settings().get("lang", "ru")

BG_COLOR = "#1a1a1a"
FG_COLOR = "#ffffff"
BTN_FG = "#ffffff"
BTN_GREEN_BG = "#2b7a2b"
BTN_GRAY_BG = "#333333"
BTN_GRAY_FG = "#ff6600"

# --- интерфейс ---
root = tk.Tk()
root.title(LANG[current_lang]["title"])
root.geometry("480x680")
root.resizable(False, False)
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("SF Pro Text", 10))
style.configure("TCheckbutton", background=BG_COLOR, foreground=FG_COLOR, font=("SF Pro Text", 10))
style.map("TCheckbutton", background=[("active", BG_COLOR)])

# кнопки через Label — на macOS tk.Button игнорит кастомные цвета
def create_custom_button(frame, text, command, bg_color, fg_color, font_config, width=18, height=2):
    btn = tk.Label(frame, text=text, bg=bg_color, fg=fg_color, font=font_config,
                   cursor="hand2", padx=width, pady=height, relief="flat")
    btn._original_bg = bg_color
    btn.bind("<Button-1>", lambda e: command())
    btn.bind("<Enter>", lambda e: btn.config(bg=lighten_color(btn._original_bg)))
    btn.bind("<Leave>", lambda e: btn.config(bg=btn._original_bg))
    return btn

def lighten_color(color):
    r = min(255, int(int(color[1:3], 16) * 1.15))
    g = min(255, int(int(color[3:5], 16) * 1.15))
    b = min(255, int(int(color[5:7], 16) * 1.15))
    return f"#{r:02x}{g:02x}{b:02x}"

label_main = tk.Label(root, text=LANG[current_lang]["label"], bg=BG_COLOR, fg="#ff6600", font=("SF Pro Text", 12, "bold"))
label_main.pack(pady=(20, 8))

# чекбоксы
cluster_keys = ["RU_C0", "RU_C1", "RU_C2", "RU_C3", "RU_C4", "RU_C5"]
checkboxes = {}
cb_widgets = {}
for key in cluster_keys:
    var = tk.BooleanVar(value=False)
    checkboxes[key] = var
    cb = tk.Checkbutton(root, text=LANG[current_lang]["clusters"][key], variable=var,
                        bg=BG_COLOR, fg="#ff6600", selectcolor="#2b7a2b",
                        activebackground=BG_COLOR, activeforeground="#ff6600", font=("SF Pro Text", 10))
    cb.pack(anchor="w", padx=30)
    cb_widgets[key] = cb

# выбрать/снять все
def select_all():
    for key in cluster_keys:
        checkboxes[key].set(True)

def deselect_all():
    for key in cluster_keys:
        checkboxes[key].set(False)

select_frame = tk.Frame(root, bg=BG_COLOR)
select_frame.pack(pady=(0, 5))

btn_select_all = create_custom_button(select_frame, "[ " + LANG[current_lang]["select_all"] + " ]",
                                      select_all, "#333333", "#ff6600", ("SF Pro Text", 9), width=10, height=1)
btn_select_all.pack(side="left", padx=5)

btn_deselect_all = create_custom_button(select_frame, "[ " + LANG[current_lang]["deselect_all"] + " ]",
                                        deselect_all, "#333333", "#ff6600", ("SF Pro Text", 9), width=10, height=1)
btn_deselect_all.pack(side="left", padx=5)

# кнопка применить
btn_apply_frame = tk.Frame(root, bg=BG_COLOR)
btn_apply_frame.pack(pady=(10, 15))

btn_apply = create_custom_button(btn_apply_frame, LANG[current_lang]["apply"], on_apply,
                                 "#333333", "#ff6600", ("SF Pro Text", 12, "bold"), width=18, height=2)
btn_apply.pack()

# статус
status_label = tk.Label(root, text="", bg=BG_COLOR, fg="#44bb44", font=("SF Pro Text", 10),
                        wraplength=440, justify="left")
status_label.pack(pady=(0, 5))

# последнее действие
action_label = tk.Label(root, text="", bg=BG_COLOR, fg="#666666", font=("SF Pro Text", 8),
                        wraplength=440, justify="left")
action_label.pack(pady=(0, 5))

# обновить статус
btn_refresh = create_custom_button(root, LANG[current_lang]["refresh"], on_refresh,
                                   "#333333", "#ff6600", ("SF Pro Text", 10), width=16, height=1)
btn_refresh.pack(pady=(0, 15))

# доп. кнопки — первая строка
extras_frame = tk.Frame(root, bg=BG_COLOR)
extras_frame.pack(pady=5)

btn_about = create_custom_button(extras_frame, "[ " + LANG[current_lang]["about"] + " ]",
                                 show_about, "#333333", "#ff6600", ("SF Pro Text", 9), width=12, height=1)
btn_about.pack(side="left", padx=5)

btn_updates = create_custom_button(extras_frame, "[ " + LANG[current_lang]["check_updates"] + " ]",
                                   check_updates, "#333333", "#ff6600", ("SF Pro Text", 9), width=16, height=1)
btn_updates.pack(side="left", padx=5)

# доп. кнопки — вторая строка
extras_frame2 = tk.Frame(root, bg=BG_COLOR)
extras_frame2.pack(pady=(0, 5))

btn_restore = create_custom_button(extras_frame2, "[ " + LANG[current_lang]["restore_btn"] + " ]",
                                   on_restore_hosts, "#333333", "#ff6600", ("SF Pro Text", 9), width=16, height=1)
btn_restore.pack()

# переключение языка
def update_ui():
    lang = LANG[current_lang]
    root.title(lang["title"])
    label_main.config(text=lang["label"])
    btn_apply.config(text=lang["apply"])
    btn_refresh.config(text=lang["refresh"])
    btn_select_all.config(text="[ " + lang["select_all"] + " ]")
    btn_deselect_all.config(text="[ " + lang["deselect_all"] + " ]")
    btn_about.config(text="[ " + lang["about"] + " ]")
    btn_updates.config(text="[ " + lang["check_updates"] + " ]")
    btn_restore.config(text="[ " + lang["restore_btn"] + " ]")
    donate_label.config(text=lang["donate"])
    contact_title.config(text=lang["contact"])
    folder_btn.config(text="[ " + lang["open_folder"] + " ]")
    update_status_text()
    for key in cluster_keys:
        if key in cb_widgets:
            cb_widgets[key].config(text=lang["clusters"][key])

def set_lang(lang):
    global current_lang
    current_lang = lang
    update_ui()
    settings = load_settings()
    settings["lang"] = lang
    save_settings(settings)
    logger.info(f"Язык: {lang}")

lang_buttons_frame = tk.Frame(root, bg=BG_COLOR)
lang_buttons_frame.pack(pady=5)

def create_lang_button(frame, text, lang_code):
    btn = tk.Label(frame, text=text, bg="#333333", fg="#ff6600", font=("SF Pro Text", 9, "bold"),
                   cursor="hand2", padx=15, pady=5, relief="flat", borderwidth=1,
                   highlightbackground="#ff6600", highlightthickness=1)
    btn.pack(side="left", padx=5)
    btn.bind("<Button-1>", lambda e: set_lang(lang_code))
    btn.bind("<Enter>", lambda e: btn.config(bg="#444444"))
    btn.bind("<Leave>", lambda e: btn.config(bg="#333333"))

create_lang_button(lang_buttons_frame, "🇷🇺 Русский", "ru")
create_lang_button(lang_buttons_frame, "🇬🇧 English", "en")

# контакты
donate_label = None
contact_title = None
folder_btn = None

def create_contact_button(frame, text, url_func, color="#4fc3f7"):
    lbl = tk.Label(frame, text=text, bg=BG_COLOR, fg=color, font=("SF Pro Text", 9), cursor="hand2")
    lbl.pack(side="left", padx=10, pady=5)
    lbl.bind("<Button-1>", lambda e: url_func())
    lbl.bind("<Enter>", lambda e: lbl.config(fg="#88ddff"))
    lbl.bind("<Leave>", lambda e: lbl.config(fg=color))
    return lbl

def create_contact_section():
    global contact_title, folder_btn
    contact_frame = tk.Frame(root, bg=BG_COLOR)
    contact_frame.pack(pady=10, fill="x")

    contact_title = tk.Label(contact_frame, text=LANG[current_lang]["contact"], bg=BG_COLOR,
                             fg="#ff6600", font=("SF Pro Text", 9, "bold"))
    contact_title.pack(pady=(0, 5))

    buttons_frame = tk.Frame(contact_frame, bg=BG_COLOR)
    buttons_frame.pack()

    create_contact_button(buttons_frame, "Telegram @waffleeb", open_telegram)
    create_contact_button(buttons_frame, "GitHub wafflee16092010-max", open_github)
    create_contact_button(buttons_frame, "Email artemtkacev417@email.com", open_email)
    folder_btn = create_contact_button(buttons_frame, "[ " + LANG[current_lang]["open_folder"] + " ]", open_app_folder, "#ff6600")

    tk.Label(contact_frame, text=f"v{APP_VERSION}", bg=BG_COLOR, fg="#666666", font=("SF Pro Text", 8)).pack(pady=5)

create_contact_section()

# донат
def create_donate_section():
    global donate_label
    donate_frame = tk.Frame(root, bg=BG_COLOR)
    donate_frame.pack(pady=5)

    donate_label = tk.Label(donate_frame, text=LANG[current_lang]["donate"], bg=BG_COLOR,
                            fg="#ff6600", font=("SF Pro Text", 10, "bold"), cursor="hand2")
    donate_label.pack()
    donate_label.bind("<Button-1>", lambda e: open_donate())
    donate_label.bind("<Enter>", lambda e: donate_label.config(fg="#ff8833"))
    donate_label.bind("<Leave>", lambda e: donate_label.config(fg="#ff6600"))

create_donate_section()

# трей
def setup_tray():
    try:
        import pystray
        from PIL import Image

        icon_image = Image.new('RGB', (64, 64), color=(43, 122, 43))

        def on_click(icon, item):
            if item.name == "Показать":
                root.deiconify()
            elif item.name == "Выход":
                icon.stop()
                root.destroy()
                sys.exit(0)

        tray_icon = pystray.Icon(
            "ClusterSwitcher", icon_image, "Tanks Blitz Cluster Switcher",
            menu=pystray.Menu(
                pystray.MenuItem("Показать", on_click, default=True),
                pystray.MenuSeparator(),
                pystray.MenuItem("Выход", on_click)
            )
        )

        tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
        tray_thread.start()
        root.protocol("WM_DELETE_WINDOW", quit_app)
    except ImportError:
        pass

try:
    setup_tray()
except Exception:
    pass

on_refresh()
root.mainloop()