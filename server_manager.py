import os
import struct

class ServerManager:
    @staticmethod
    def ensure_novamc_server(target_dir):
        """Ensures novamc.uz is configured as the #1 server in servers.dat"""
        try:
            os.makedirs(target_dir, exist_ok=True)
            servers_dat_path = os.path.join(target_dir, "servers.dat")

            # Check if servers.dat already exists and has novamc.uz
            if os.path.exists(servers_dat_path):
                try:
                    with open(servers_dat_path, 'rb') as f:
                        content = f.read()
                        if b"novamc.uz" in content:
                            return True
                except Exception:
                    pass

            # Generate binary NBT for servers.dat with novamc.uz as #1 server
            def pack_string(s):
                encoded = s.encode('utf-8')
                return struct.pack('>H', len(encoded)) + encoded

            data = bytearray()
            data.append(10)  # Root TAG_Compound
            data.extend(struct.pack('>H', 0))  # Empty root name

            data.append(9)  # TAG_List for 'servers'
            data.extend(pack_string("servers"))
            data.append(10)  # List element type = TAG_Compound
            data.extend(struct.pack('>i', 1))  # 1 server entry

            # Compound for novamc.uz server
            server_bytes = bytearray()
            server_bytes.append(8)  # TAG_String for 'name'
            server_bytes.extend(pack_string("name"))
            server_bytes.extend(pack_string("⭐ NovaMC Network (novamc.uz)"))

            server_bytes.append(8)  # TAG_String for 'ip'
            server_bytes.extend(pack_string("ip"))
            server_bytes.extend(pack_string("novamc.uz"))

            server_bytes.append(0)  # TAG_End of server compound

            data.extend(server_bytes)
            data.append(0)  # TAG_End of root compound

            with open(servers_dat_path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            print(f"servers.dat yaratishda xatolik: {e}")
            return False
