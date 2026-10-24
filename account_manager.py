import os
import json
import hashlib

# Akkauntlar bazasi DOIM bu yerda saqlanadi — game_dir o'zgarishidan mustaqil
_ACCOUNTS_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), '.novalauncher')

class AccountManager:
    ADMIN_CREDENTIALS = {
        "ergashev": "amirgey",
        "Zero_dev": "164813"
    }

    def __init__(self, game_dir=None):
        # game_dir argument qabul qilinadi lekin akkaunt bazasi uchun ishlatilmaydi
        self.game_dir = game_dir or _ACCOUNTS_DIR
        os.makedirs(_ACCOUNTS_DIR, exist_ok=True)
        self.db_path = os.path.join(_ACCOUNTS_DIR, 'accounts.json')
        self.accounts = {}
        self.active_username = ""
        self.load()


    def _hash_password(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def is_admin_account(self, username, password):
        for admin_user, admin_pass in self.ADMIN_CREDENTIALS.items():
            if admin_user.lower() == username.strip().lower() and admin_pass == password.strip():
                return True
        return False

    def load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = data.get("accounts", {})
                    self.active_username = data.get("active_username", "")
            except Exception as e:
                print(f"Akkauntlar bazasini o'qishda xatolik: {e}")
                self.accounts = {}
                self.active_username = ""
        else:
            self.accounts = {}
            self.active_username = ""

    def save(self):
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "accounts": self.accounts,
                    "active_username": self.active_username
                }, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Akkauntlar bazasini saqlashda xatolik: {e}")

    def register(self, username, password, is_alex=False):
        username = username.strip()
        if not username:
            return False, "Nikneym bo'sh bo'lishi mumkin emas!"
        if len(username) < 3:
            return False, "Nikneym kamida 3 ta belgidan iborat bo'lishi kerak!"
        if username.lower() in [u.lower() for u in self.accounts.keys()]:
            return False, "Ushbu nikneym bilan allaqachon ro'yxatdan o'tilgan!"
        if len(password) < 3:
            return False, "Parol kamida 3 ta belgidan iborat bo'lishi kerak!"

        is_admin = self.is_admin_account(username, password)
        role = "Admin" if is_admin else "User"
        display_role = "👑 Admin (Boshqaruvchi)" if is_admin else "🟢 Nova Akkaunt"
        cape_path = "preset_admin" if is_admin else "preset_nova"

        self.accounts[username] = {
            "username": username,
            "password_hash": self._hash_password(password),
            "role": role,
            "display_role": display_role,
            "skin_path": "",
            "cape_path": cape_path,
            "is_alex": is_alex
        }
        self.active_username = username
        self.save()
        return True, f"Xush kelibsiz, {username}! Ro'yxatdan o'tish muvaffaqiyatli yakunlandi."

    def authenticate(self, username, password):
        username = username.strip()
        if username not in self.accounts:
            if self.is_admin_account(username, password):
                self.register(username, password)
                self.active_username = username
                self.save()
                return True, f"Xush kelibsiz, Admin {username}!"
            return False, "Bunday foydalanuvchi topilmadi! Avval ro'yxatdan o'ting."

        acc = self.accounts[username]
        if acc.get("password_hash") == self._hash_password(password):
            if self.is_admin_account(username, password):
                acc["role"] = "Admin"
                acc["display_role"] = "👑 Admin (Boshqaruvchi)"
            self.active_username = username
            self.save()
            return True, f"Xush kelibsiz, {username}!"
        else:
            return False, "Parol noto'g'ri kiritildi!"

    def get_account(self, username):
        return self.accounts.get(username)

    def get_active_account(self):
        if self.active_username in self.accounts:
            return self.accounts[self.active_username]
        if self.accounts:
            first_user = list(self.accounts.keys())[0]
            self.active_username = first_user
            return self.accounts[first_user]
        return {
            "username": "O'yinchi",
            "role": "Offline",
            "display_role": "🔌 Offlayn Akkaunt",
            "skin_path": "",
            "cape_path": "",
            "is_alex": False
        }

    def set_active_username(self, username):
        if username in self.accounts or username == "O'yinchi":
            self.active_username = username
            self.save()

    def update_skin(self, username, skin_path, is_alex=False):
        if username in self.accounts:
            self.accounts[username]["skin_path"] = skin_path
            self.accounts[username]["is_alex"] = is_alex
            self.save()

    def update_cape(self, username, cape_path):
        if username in self.accounts:
            self.accounts[username]["cape_path"] = cape_path
            self.save()

    def get_all_accounts(self):
        return self.accounts

    def delete_account(self, username):
        if username in self.accounts:
            del self.accounts[username]
            if self.active_username == username:
                self.active_username = list(self.accounts.keys())[0] if self.accounts else ""
            self.save()
            return True, f"Foydalanuvchi '{username}' muvaffaqiyatli o'chirildi."
        return False, "Foydalanuvchi topilmadi."
