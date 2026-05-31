"""
Multi-Robot Warehouse 2.5D İzometrik Simülasyonu
Görev Paylaşımı (Task Allocation) & Çarpışma Önleme (Collision Avoidance) Görselleştirmesi
"""

import pygame
import math
import sys
import random

# ============================================================
# 1. SABİTLER VE PENCERE AYARLARI
# ============================================================
W, H = 1280, 720
HUD_W = 320             # Bilgi paneli genişliği
REND_W = W - HUD_W      # Simülasyon çizim alanı genişliği
FPS_HEDEF = 60

# İzometrik Projeksiyon Katsayıları (Yakınlaştırılmış depo görünümü için ISO = 28)
ISO = 28
CA = math.cos(math.radians(30))   # cos(30) = 0.866
SA = 0.5                          # sin(30) = 0.50
ZS = 0.75                         # Yükseklik çarpanı

# Kamera ve Merkez Konumu
RCX = 520
RCY = 320

# Dünya Sınırları
DUNYA_X_MIN, DUNYA_X_MAX = -16.0, 10.0
DUNYA_Y_MIN, DUNYA_Y_MAX = -8.0, 8.0

# ============================================================
# 2. RENK PALETİ (Premium Koyu Tema ve Canlı Uyarı Renkleri)
# ============================================================
C_BG        = (15, 16, 26)        # Koyu Uzay Grisi Arka Plan
C_FLOOR     = (44, 48, 60)        # Depo Epoksi Zemin Rengi
C_GRID      = (55, 60, 75)        # Zemin Izgarası
C_ROAD      = (34, 37, 48)        # Robot Şeritleri
C_SAFE_LINE = (235, 185, 25)      # Sarı/Siyah Güvenlik Şerit Rengi
C_WALL      = (70, 75, 90)        # Duvarlar
C_WALL_TOP  = (90, 95, 115)       # Duvar Üst Yüzeyi
C_WHITE     = (240, 240, 245)     # Yumuşak Beyaz
C_GRAY      = (140, 145, 160)     # Açıklama Metni Grisi
C_COLL_ZONE = (230, 50, 50, 40)   # Çarpışma Önleme Radarı Rengi (Yarı Saydam Kırmızı)
C_RADAR_OK  = (50, 220, 100, 30)  # Güvenli Alan Radarı Rengi (Yarı Saydam Yeşil)

ROBOT_RENKLER = {
    "rob_v1": (240, 70, 70),      # Kırmızı
    "rob_v2": (60, 140, 240),     # Mavi
    "rob_v3": (70, 220, 100),     # Yeşil
    "rob_v4": (180, 70, 240),     # Mor
    "rob_v5": (240, 150, 50),     # Turuncu
}

# ============================================================
# 3. YOL VE HEDEF TANIMLARI (Waypoints)
# ============================================================
WP = {
    "WP1":   (-3.00, -4.50),
    "WP5-1": (-1.00,  5.25),
    "WP5-2": ( 1.00,  5.25),
    "WP5-3": ( 5.00,  5.25),
    "WP5-4": ( 6.80,  5.25),
    "WP5-5": ( 8.20,  5.25),
    
    # Ortak şerit giriş/çıkış geçiş noktaları
    "WP_GO_START": (-3.00, -5.40),
    "WP_RET_END":  (-1.00, -4.80),
    
    # Robot 1 Özel Dikey Şerit Geçişleri (x = -3.75)
    "WP_GO_1":   (-3.75, -5.40),
    "WP_RET_1":  (-3.75, -4.80),
    "WP_TOP_1":  (-3.75,  5.25),
    
    # Robot 2 Özel Dikey Şerit Geçişleri (x = 2.25)
    "WP_GO_2":   ( 2.25, -5.40),
    "WP_RET_2":  ( 2.25, -4.80),
    "WP_TOP_2":  ( 2.25,  5.25),
    
    # Robot 3 Özel Dikey Şerit Geçişleri (x = 3.75)
    "WP_GO_3":   ( 3.75, -5.40),
    "WP_RET_3":  ( 3.75, -4.80),
    "WP_TOP_3":  ( 3.75,  5.25),
    
    # Robot 4 Özel Dikey Şerit Geçişleri (x = 6.00)
    "WP_GO_4":   ( 6.00, -5.40),
    "WP_RET_4":  ( 6.00, -4.80),
    "WP_TOP_4":  ( 6.00,  5.25),
    
    # Robot 5 Özel Dikey Şerit Geçişleri (x = 8.75)
    "WP_GO_5":   ( 8.75, -5.40),
    "WP_RET_5":  ( 8.75, -4.80),
    "WP_TOP_5":  ( 8.75,  5.25),
}

ROBOT_TANIMLARI = [
    {"isim": "rob_v1", "baslangic": (-7.0,  -4.8), "gecikme": 0.0,  "wp5": "WP5-1"},
    {"isim": "rob_v2", "baslangic": (-9.0,  -4.8), "gecikme": 3.0,  "wp5": "WP5-2"},
    {"isim": "rob_v3", "baslangic": (-11.0, -4.8), "gecikme": 6.0,  "wp5": "WP5-3"},
    {"isim": "rob_v4", "baslangic": (-13.0, -4.8), "gecikme": 9.0,  "wp5": "WP5-4"},
    {"isim": "rob_v5", "baslangic": (-15.0, -4.8), "gecikme": 12.0, "wp5": "WP5-5"},
]

# Çarpışma Önleme Parametreleri
RADAR_MESAFE = 1.55     # Çarpışma önleme radar algılama mesafesi (dünya birimi)
CRITICAL_DIST = 0.75    # Acil yavaşlama/kaçış mesafesi (dünya birimi)

# Depo Rafları Konumları (Orta raflar ve fütüristik B grubu üst raflar)
RAFLAR = [
    # Orta Bölge Rafları (A Grubu - Optimize Edilmiş 4 Sütun Düzeni)
    (-1.50, -2.05), (-1.50, 0.05), 
    ( 1.00, -2.05), ( 1.00, 0.05),
    ( 5.00, -2.05), ( 5.00, 0.05),
    ( 7.50, -2.05), ( 7.50, 0.05),
    
    # Üst Bölge Rafları (B Grubu - Her biri bir WP5'in arkasında)
    (-1.00,  6.05),
    ( 1.00,  6.05),
    ( 5.00,  6.05),
    ( 6.80,  6.05),
    ( 8.20,  6.05),
]

# Statik Engeller (Ad, x, y, genişlik, derinlik, yükseklik, renk)
ENGELLER = [
    ("Kamyon",     0.0,  -4.00, 2.2, 1.1, 0.95, (120, 85, 45))
]

# ============================================================
# 4. KOORDİNAT DÖNÜŞÜMLERİ VE YARDIMCI METOTLAR
# ============================================================
def world_to_screen(wx, wy, wz=0):
    """Dünya koordinatlarını izometrik ekran koordinatına çevirir."""
    ix = (wx - wy) * ISO * CA
    iy = -(wx + wy) * ISO * SA - wz * ISO * ZS
    return int(RCX + ix), int(RCY + iy)

def sh(color, factor):
    """Renk tonunu gölgeleme için koyulaştırır veya açar."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)

def normalize_aci(a):
    """Açıyı [-pi, pi] aralığında tutar."""
    while a > math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a

# ============================================================
# 5. İZOMETRİK ÇİZİM YARDIMCILARI
# ============================================================
def draw_iso_polygon(surf, pts_world, color, border_color=None, border_width=1):
    """Dünya koordinatlı noktaları izometrik poligona çevirip çizer."""
    pts_screen = [world_to_screen(x, y) for x, y in pts_world]
    pygame.draw.polygon(surf, color, pts_screen)
    if border_color:
        pygame.draw.polygon(surf, border_color, pts_screen, border_width)

def draw_iso_box(surf, wx, wy, wz, ww, wd, wh, color, edge_color=None):
    """İzometrik 3D Kutu çizer. Gölgeli yüzeyler ile derinlik hissi verir."""
    def p(x, y, z): return world_to_screen(x, y, z)
    
    top_c   = sh(color, 1.05)
    front_c = sh(color, 0.70)
    left_c  = sh(color, 0.50)
    ec      = edge_color if edge_color else sh(color, 0.30)
    
    # 1. Sol Yüzey (West)
    left_pts = [p(wx, wy, wz), p(wx, wy + wd, wz), p(wx, wy + wd, wz + wh), p(wx, wy, wz + wh)]
    pygame.draw.polygon(surf, left_c, left_pts)
    pygame.draw.polygon(surf, ec, left_pts, 1)
    
    # 2. Ön Yüzey (South)
    front_pts = [p(wx, wy, wz), p(wx + ww, wy, wz), p(wx + ww, wy, wz + wh), p(wx, wy, wz + wh)]
    pygame.draw.polygon(surf, front_c, front_pts)
    pygame.draw.polygon(surf, ec, front_pts, 1)
    
    # 3. Üst Yüzey (Top)
    top_pts = [p(wx, wy, wz + wh), p(wx + ww, wy, wz + wh), p(wx + ww, wy + wd, wz + wh), p(wx, wy + wd, wz + wh)]
    pygame.draw.polygon(surf, top_c, top_pts)
    pygame.draw.polygon(surf, ec, top_pts, 1)

def draw_iso_ellipse(surf, wx, wy, wz, rx_world, ry_world, color):
    """İzometrik düzlemde elips/halka çizer (Radarlar ve gölgeler için)."""
    # Ekran boyutuna çevirme
    sx, sy = world_to_screen(wx, wy, wz)
    rx_px = int(rx_world * ISO * CA)
    ry_px = int(ry_world * ISO * SA)
    
    # Yarı saydam çizim için geçici yüzey oluşturma
    temp_surf = pygame.Surface((rx_px * 2, ry_px * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(temp_surf, color, (0, 0, rx_px * 2, ry_px * 2))
    surf.blit(temp_surf, (sx - rx_px, sy - ry_px))

def draw_iso_ellipse_border(surf, wx, wy, wz, rx_world, ry_world, color, width=2):
    """İzometrik düzlemde elips çerçevesi çizer."""
    sx, sy = world_to_screen(wx, wy, wz)
    rx_px = int(rx_world * ISO * CA)
    ry_px = int(ry_world * ISO * SA)
    
    temp_surf = pygame.Surface((rx_px * 2, ry_px * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(temp_surf, color, (0, 0, rx_px * 2, ry_px * 2), width)
    surf.blit(temp_surf, (sx - rx_px, sy - ry_px))

# ============================================================
# 6. GÖREV PANELİ VE TASK ALLOCATION SINIFI (Görev Paylaşımı)
# ============================================================
class Task:
    def __init__(self, id_num, source, target, color):
        self.id_num = id_num
        self.source = source
        self.target = target
        self.color = color
        self.status = "Beklemede"      # "Beklemede", "Taşınıyor", "Tamamlandı"
        self.assigned_robot = None

class TaskManager:
    """Simülasyondaki iş yükünün dağıtılması ve izlenmesini yönetir."""
    def __init__(self):
        self.active_tasks = []
        self.completed_count = 0
        self._generate_initial_tasks()
        
    def _generate_initial_tasks(self):
        for i in range(1, 6):
            target = f"WP5-{i}"
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(50, 150))
            self.active_tasks.append(Task(i, "WP1", target, color))
            
    def get_task_for_robot(self, robot_name, target_wp):
        """Robota uygun bir görev tahsis eder."""
        for t in self.active_tasks:
            if t.status == "Beklemede" and t.target == target_wp:
                t.status = "Taşınıyor"
                t.assigned_robot = robot_name
                return t
        # Eğer uygun görev kalmadıysa yeni bir tane oluştur
        new_id = len(self.active_tasks) + 1
        color = (random.randint(100, 255), random.randint(100, 255), random.randint(50, 150))
        t = Task(new_id, "WP1", target_wp, color)
        t.status = "Taşınıyor"
        t.assigned_robot = robot_name
        self.active_tasks.append(t)
        return t

    def complete_task(self, task):
        if task:
            task.status = "Tamamlandı"
            self.completed_count += 1

# ============================================================
# 7. ROBOT SINIFI (Fizik, P-Kontrolcü ve Çarpışma Önleme Mantığı)
# ============================================================
class Robot:
    def __init__(self, tanim, tum_robotlar_ref, task_manager):
        self.isim        = tanim["isim"]
        self.baslangic_x = tanim["baslangic"][0]
        self.baslangic_y = tanim["baslangic"][1]
        self.gecikme     = tanim["gecikme"]
        self.wp5_key     = tanim["wp5"]
        self.renk        = ROBOT_RENKLER[self.isim]
        self.tum_robotlar = tum_robotlar_ref
        self.task_manager = task_manager

        # Rota Waypointleri (Her Robota Özel Kişisel Otoyol Şeridi)
        r_idx = self.isim[-1] # "1", "2", "3", "4", veya "5"
        self.gidis_rotasi = ["WP1", "WP_GO_START", f"WP_GO_{r_idx}", f"WP_TOP_{r_idx}", self.wp5_key]
        self.donus_rotasi = [self.wp5_key, f"WP_TOP_{r_idx}", f"WP_RET_{r_idx}", "WP_RET_END", "WP1"]

        self.stuck_time = 0.0
        self.last_x = self.baslangic_x
        self.last_y = self.baslangic_y

        self._sifirla()

    def _sifirla(self):
        self.x        = self.baslangic_x
        self.y        = self.baslangic_y
        self.aci      = 0.0
        self.aktif    = False
        self.bekliyor = False
        self.bekleme_kalan = 0.0
        self.gidis   = True        # True = WP1'den WP5'e (Yük almaya gidiyor), False = WP5'den WP1'e (Yük taşıyor)
        self.rota_idx = 0
        self.sim_sure = 0.0
        self.tamamlanan_tur = 0
        self.durum   = "Bekliyor"
        
        # Görev Paylaşımı Değişkenleri
        self.aktif_gorev = None
        self.yuk_tasiniyor = False
        self.yuk_renk = (200, 200, 200)
        
        self.stuck_time = 0.0
        self.last_x = self.baslangic_x
        self.last_y = self.baslangic_y
        
        # Çarpışma Önleme Durum Bilgileri (Görsel Efektler İçin)
        self.avoiding = False
        self.avoid_reason = ""
        self.avoid_vector = (0, 0)
        self.radar_renk = C_RADAR_OK
        self.hiz_orani = 1.0

    def hedef_wp(self):
        rota = self.gidis_rotasi if self.gidis else self.donus_rotasi
        if self.rota_idx >= len(rota):
            return None
        return rota[self.rota_idx]

    def hedef_konum(self):
        key = self.hedef_wp()
        if key is None:
            return None
        return WP[key]

    def guncelle(self, dt, sim_sure_toplam):
        self.sim_sure = sim_sure_toplam

        # Başlangıç Gecikmesi Kontrolü
        if sim_sure_toplam < self.gecikme:
            self.durum = "Gecikme Süresinde"
            return
        if not self.aktif:
            self.aktif = True

        # Görev Atama Mantığı (Görev Paylaşımı)
        if self.aktif and self.aktif_gorev is None:
            # Robota yeni bir görev verilir
            self.aktif_gorev = self.task_manager.get_task_for_robot(self.isim, self.wp5_key)

        # Duraklama / Yükleme / Boşaltma Süresi Beklemesi
        if self.bekliyor:
            self.bekleme_kalan -= dt
            
            # Robotun duruş açısını hedefe (kamyona veya rafa) bakacak şekilde sabitleyelim
            hedef_wp = self.hedef_wp()
            if hedef_wp == "WP1":
                self.durum = f"Kamyondan Alınıyor ({self.bekleme_kalan:.1f}s)"
                self.aci = math.pi  # Kamyona doğru baksın (sola)
            elif hedef_wp and "WP5" in hedef_wp:
                self.durum = f"Rafa Yerleştiriliyor ({self.bekleme_kalan:.1f}s)"
                self.aci = math.pi / 2  # Rafa doğru baksın (yukarı)
            else:
                self.durum = f"İşlem Yapılıyor ({self.bekleme_kalan:.1f}s)"
                
            if self.bekleme_kalan <= 0:
                self.bekliyor = False
                
                # Neredeyiz?
                if hedef_wp == "WP1":
                    # Kamyondan alım bitti, artık taşıyoruz
                    self.yuk_tasiniyor = True
                    if self.aktif_gorev:
                        self.yuk_renk = self.aktif_gorev.color
                    self.gidis = True
                    self.rota_idx = 1  # Rota üzerindeki WP2'ye yönlen
                elif hedef_wp and "WP5" in hedef_wp:
                    # Rafa ürün yerleştirme bitti!
                    self.yuk_tasiniyor = False
                    if self.aktif_gorev:
                        self.task_manager.complete_task(self.aktif_gorev)
                        self.aktif_gorev = None
                    self.tamamlanan_tur += 1
                    self.gidis = False
                    self.rota_idx = 1  # Dönüş rotasındaki WP4-2'ye yönlen
            return

        hedef = self.hedef_konum()
        if hedef is None:
            return

        dx = hedef[0] - self.x
        dy = hedef[1] - self.y
        mesafe = math.hypot(dx, dy)

        # Hedefe Ulaşıldı Mı?
        if mesafe < 0.2:
            wp = self.hedef_wp()
            rota = self.gidis_rotasi if self.gidis else self.donus_rotasi
            
            # Kamyon Giriş Semaforu (Mutex) - Sadece tek bir robotun koridora girmesine izin verir
            if wp == "WP_RET_END":
                wp1_dolu = False
                for r in self.tum_robotlar:
                    if r is self or not r.aktif:
                        continue
                    # Başka bir robot WP1'e yakınsa veya yük alıyorsa burada bekle
                    if math.hypot(r.x - WP["WP1"][0], r.y - WP["WP1"][1]) < 0.85:
                        wp1_dolu = True
                        break
                if wp1_dolu:
                    self.durum = "Kamyon Alanı Dolu, Bekliyor"
                    # Kilitleyip tam hedefin üstünde bekletelim
                    self.x = hedef[0]
                    self.y = hedef[1]
                    return

            if wp == "WP1" and not self.yuk_tasiniyor:
                # Kamyondan yükleme için dur
                self.bekliyor = True
                self.bekleme_kalan = 3.0
            elif wp == rota[-1] and self.gidis:
                # Rafa ulaştık, yerleştirme için dur
                self.bekliyor = True
                self.bekleme_kalan = 3.0
            else:
                self.rota_idx += 1
            return

        # 1. Önce Çarpışma Önleme Hesaplanır (Radar her zaman aktiftir)
        baz_hiz = 0.65
        guvenli_hiz = self._carpismo_onleme(baz_hiz)

        # 2. Hedef Yön Belirleme (Virtual Force Field Yaklaşımı)
        hedef_dx = hedef[0] - self.x
        hedef_dy = hedef[1] - self.y
        hedef_dist = math.hypot(hedef_dx, hedef_dy)
        
        if hedef_dist > 0:
            hedef_ux = hedef_dx / hedef_dist
            hedef_uy = hedef_dy / hedef_dist
        else:
            hedef_ux, hedef_uy = 0.0, 0.0

        # Eğer çarpışma önleme aktifse, asıl hedef yönü kaçınma teğeti ile birleştirilir
        if self.avoiding:
            en_yakin_dist = 999.0
            for r in self.tum_robotlar:
                if r is self or not r.aktif: continue
                d = math.hypot(r.x - self.x, r.y - self.y)
                if d < en_yakin_dist: en_yakin_dist = d
            
            # Engel ne kadar yakınsa kaçış yönü o kadar baskın olur
            etki_gucu = 1.0 - min(1.0, en_yakin_dist / RADAR_MESAFE)
            yon_x = hedef_ux * (1.0 - etki_gucu * 0.7) + self.avoid_vector[0] * (etki_gucu * 0.7)
            yon_y = hedef_uy * (1.0 - etki_gucu * 0.7) + self.avoid_vector[1] * (etki_gucu * 0.7)
        else:
            yon_x = hedef_ux
            yon_y = hedef_uy

        # Sonuç hedef açı
        hedef_aci = math.atan2(yon_y, yon_x)
        aci_farki = normalize_aci(hedef_aci - self.aci)

        # 3. Sürekli Yönelme ve Dönüş Kontrolü (P-Kontrolcü)
        self.aci += 3.2 * aci_farki * dt
        self.aci = normalize_aci(self.aci)

        # 4. İlerleme Hızı Açı Farkına Göre Ölçeklenir
        # Eğer robot çok ters bir yöne bakıyorsa yavaşlar, önü hedefe dönükse tam hız gider
        if abs(aci_farki) < 0.25:
            hiz_aci_carpani = 1.0
        elif abs(aci_farki) > 1.2:
            hiz_aci_carpani = 0.05  # Neredeyse durur ve hızlıca döner
        else:
            hiz_aci_carpani = max(0.1, math.cos(aci_farki))

        # İlerleme hareketinin uygulanması
        ileri_hiz = guvenli_hiz * hiz_aci_carpani
        
        # Eğer yanal kaçış yapılıyorsa ve robot hareket halindeyse yanal kayma eklenir (dururken kayması önlenir)
        if self.avoiding and self.hiz_orani > 0.05:
            # Yanal gücü daha agresif hale getirdik (0.14 -> 0.32)
            yanal_guc = (1.0 - self.hiz_orani) * 0.32
            self.x += self.avoid_vector[0] * yanal_guc * dt
            self.y += self.avoid_vector[1] * yanal_guc * dt

        self.x += math.cos(self.aci) * ileri_hiz * dt
        self.y += math.sin(self.aci) * ileri_hiz * dt

        # --- RAFLARLA VE STATİK ENGELLERLE FİZİKSEL ÇARPIŞMA ÇÖZÜMÜ (AABB) ---
        rob_r = 0.28  # Robot fiziksel koruma yarıçapı
        
        # 1. Depo Rafları AABB Sınır Kontrolü (ww = 1.25, wd = 0.55)
        for rx, ry in RAFLAR:
            min_x, max_x = rx - 0.625 - rob_r, rx + 0.625 + rob_r
            min_y, max_y = ry - 0.275 - rob_r, ry + 0.275 + rob_r
            if min_x < self.x < max_x and min_y < self.y < max_y:
                # Robotun kutunun içine girmesini önlemek için en yakın kenara geri itelim
                dx_min, dx_max = self.x - min_x, max_x - self.x
                dy_min, dy_max = self.y - min_y, max_y - self.y
                min_dist = min(dx_min, dx_max, dy_min, dy_max)
                if min_dist == dx_min: self.x = min_x
                elif min_dist == dx_max: self.x = max_x
                elif min_dist == dy_min: self.y = min_y
                else: self.y = max_y

        # 2. Diğer Statik Engeller AABB Sınır Kontrolü
        for ad, ox, oy, ow, od, oh, col in ENGELLER:
            min_x, max_x = ox - ow/2 - rob_r, ox + ow/2 + rob_r
            min_y, max_y = oy - od/2 - rob_r, oy + od/2 + rob_r
            if min_x < self.x < max_x and min_y < self.y < max_y:
                dx_min, dx_max = self.x - min_x, max_x - self.x
                dy_min, dy_max = self.y - min_y, max_y - self.y
                min_dist = min(dx_min, dx_max, dy_min, dy_max)
                if min_dist == dx_min: self.x = min_x
                elif min_dist == dx_max: self.x = max_x
                elif min_dist == dy_min: self.y = min_y
                else: self.y = max_y

        # 3. Robot-Robot Fiziksel Daire-Daire Çarpışma Çözümü (İç içe geçmeyi ve itişmeyi kesin olarak engeller)
        for r in self.tum_robotlar:
            if r is self or not r.aktif or (self.sim_sure < self.gecikme) or (r.sim_sure < r.gecikme):
                continue
            r_dist = math.hypot(r.x - self.x, r.y - self.y)
            limit = 0.56  # 2 * rob_r (0.28 + 0.28)
            if r_dist < limit:
                overlap = limit - r_dist
                if r_dist > 0:
                    # Birbirini zıt yönlerde iterek çakışmayı giderirler (yarı yarıya itiş gücü)
                    push_x = ((self.x - r.x) / r_dist) * overlap * 0.5
                    push_y = ((self.y - r.y) / r_dist) * overlap * 0.5
                    self.x += push_x
                    self.y += push_y
                    r.x -= push_x
                    r.y -= push_y

        # --- SIKIŞMA (DEADLOCK) ALGILAMA VE AKTİF ÇÖZÜM ---
        d_moved = math.hypot(self.x - self.last_x, self.y - self.last_y)
        self.last_x = self.x
        self.last_y = self.y
        
        if not self.bekliyor and self.aktif:
            # Robot hareket etmeye çalışıyor ama milim kımıldamıyorsa
            if d_moved < 0.05 * dt:
                self.stuck_time += dt
            else:
                self.stuck_time = max(0.0, self.stuck_time - dt * 2.0)
        else:
            self.stuck_time = 0.0
            
        # Eğer 1.0 saniyeden uzun süredir sıkışmışsa, aktif kurtulma itmesi uygula
        if self.stuck_time > 1.0:
            self.durum = "Sıkışma Çözülüyor..."
            self.radar_renk = (255, 100, 255, 60) # Mor renkli sıkışma çözme radarı
            
            # En yakın engeli veya rafı bul
            nearest_center = None
            min_dist_to_center = 999.0
            for rx, ry in RAFLAR:
                d = math.hypot(rx - self.x, ry - self.y)
                if d < min_dist_to_center:
                    min_dist_to_center = d
                    nearest_center = (rx, ry)
            for ad, ox, oy, ow, od, oh, col in ENGELLER:
                d = math.hypot(ox - self.x, oy - self.y)
                if d < min_dist_to_center:
                    min_dist_to_center = d
                    nearest_center = (ox, oy)
            
            # Eğer yakında (2.0 birim) bir engel varsa, engelden UZAĞA doğru güçlü bir itiş uygula!
            if nearest_center and min_dist_to_center < 2.0:
                nudge_dx = self.x - nearest_center[0]
                nudge_dy = self.y - nearest_center[1]
                nudge_len = math.hypot(nudge_dx, nudge_dy)
                if nudge_len > 0:
                    self.x += (nudge_dx / nudge_len) * 0.95 * dt
                    self.y += (nudge_dy / nudge_len) * 0.95 * dt
            else:
                # Engel yakınında değilse (robot robotla sıkışmışsa), simetri kırıcı teğetsel itiş
                nudge_dir = 1.0 if (hash(self.isim) % 2 == 0) else -1.0
                nudge_aci = self.aci + nudge_dir * (math.pi / 2)
                self.x += math.cos(nudge_aci) * 0.65 * dt
                self.y += math.sin(nudge_aci) * 0.65 * dt

    def _carpismo_onleme(self, baz_hiz):
        """
        Diğer robotlarla olan mesafeleri tarayarak çarpışmayı engeller.
        Takip mesafesi, karşı karşıya kalma ve kuyruğa girme durumlarını yönetir.
        """
        self.avoiding = False
        self.avoid_reason = ""
        self.radar_renk = C_RADAR_OK
        self.hiz_orani = 1.0
        self.avoid_vector = (0, 0)
        
        en_yakin_dist = 999.0
        en_yakin_robot = None

        # 1. En yakın robotu bulma
        for r in self.tum_robotlar:
            if r is self or not r.aktif:
                continue
            
            # Yanal şerit koruması: Farklı paralel şeritlerdeki robotlar birbirinin radarını etkilemez
            dx = r.x - self.x
            dy = r.y - self.y
            
            # Hareket yönü dikey mi yatay mı?
            aci_deg = math.degrees(self.aci) % 180
            dikey_hareket = 45.0 < aci_deg < 135.0
            
            if dikey_hareket:
                # Dikey şeritteyken yanal mesafe (X farkı) 0.50'den büyükse yollarımız çakışmıyordur
                if abs(dx) > 0.50:
                    continue
            else:
                # Yatay şeritteyken yanal mesafe (Y farkı) 0.50'den büyükse yollarımız çakışmıyordur
                if abs(dy) > 0.50:
                    continue

            dist = math.hypot(dx, dy)
            if dist < en_yakin_dist:
                en_yakin_dist = dist
                en_yakin_robot = r

        # 2. Çarpışma ve Güvenli Takip/Bekleme Kuralları
        r_dist = RADAR_MESAFE
        # Ramp yükleme bölgesinde (y < -3.5) algılama mesafesini daraltalım ki
        # yan yoldan geçenler veya kuyruk bekleyenler birbirinin radarını kilitlemesin
        if self.y < -3.5 and en_yakin_robot and en_yakin_robot.y < -3.5:
            r_dist = 0.85

        if en_yakin_robot and en_yakin_dist < r_dist:
            self.avoiding = True
            self.avoid_reason = f"{en_yakin_robot.isim.upper()}"
            
            # Robotun bizim ön yarım küremizde (önümüzde) olup olmadığını hesapla (Dot Product)
            dx = en_yakin_robot.x - self.x
            dy = en_yakin_robot.y - self.y
            dot_front = dx * math.cos(self.aci) + dy * math.sin(self.aci)
            is_in_front = dot_front > 0.0

            # Yönlerin karşı karşıya (kafa kafaya) veya aynı yönde (kuyruk takibi) olup olmadığını hesapla
            cos_diff = math.cos(self.aci - en_yakin_robot.aci)
            karsi_karsiya = cos_diff < -0.45
            ayni_yon = cos_diff > 0.45
            
            if is_in_front:
                if karsi_karsiya:
                    # Kafa kafaya gelme: Öncelik kuralları uygulanır
                    self.radar_renk = (240, 140, 20, 50)  # Turuncu Uyarı Radarı
                    
                    ben_oncelikli = False
                    if self.yuk_tasiniyor and not en_yakin_robot.yuk_tasiniyor:
                        ben_oncelikli = True
                    elif not self.yuk_tasiniyor and en_yakin_robot.yuk_tasiniyor:
                        ben_oncelikli = False
                    else:
                        ben_oncelikli = self.isim < en_yakin_robot.isim
                    
                    if not ben_oncelikli:
                        # Öncelik karşı tarafta: Çok yavaş git ve aktif olarak yana kaç!
                        self.hiz_orani = 0.15
                        self.durum = "Yol Veriyor (Yandan Geçiş)"
                        if en_yakin_dist < 0.65:
                            self.hiz_orani = 0.0
                            return 0.0
                    else:
                        # Öncelik bende: Güvenli ve yavaşça yana kaçarak geç
                        if en_yakin_dist < 1.1:
                            self.hiz_orani = 0.25 + 0.20 * ((en_yakin_dist - CRITICAL_DIST) / (1.1 - CRITICAL_DIST))
                        else:
                            self.hiz_orani = 0.45
                        self.durum = "Öncelikli Geçiş (Yandan)"
                elif ayni_yon:
                    # Aynı yönde kuyruk takibi: Lider / Takipçi ayrımı
                    ben_lider = False
                    if self.gidis == en_yakin_robot.gidis:
                        if self.rota_idx > en_yakin_robot.rota_idx:
                            ben_lider = True
                        elif self.rota_idx < en_yakin_robot.rota_idx:
                            ben_lider = False
                        else:
                            # Aynı rota indeksindelerse hedefe en yakın olan liderdir (öndedir)
                            self_hedef = self.hedef_konum()
                            r_hedef = en_yakin_robot.hedef_konum()
                            if self_hedef and r_hedef:
                                dist_self = math.hypot(self_hedef[0] - self.x, self_hedef[1] - self.y)
                                dist_r = math.hypot(r_hedef[0] - en_yakin_robot.x, r_hedef[1] - en_yakin_robot.y)
                                ben_lider = dist_self < dist_r
                    
                    if ben_lider:
                        # Lideriz: Arkamızdaki takipçi için durmuyoruz, tam hız devam!
                        self.hiz_orani = 1.0
                        self.avoiding = False
                        return baz_hiz
                    else:
                        # Takipçiyiz: Öndeki robotu güvenli takip mesafesinden izliyoruz
                        self.radar_renk = (200, 200, 50, 45)  # Sarı Takip Radarı
                        self.durum = "Kuyruk Takibi"
                        
                        GIVEN_STOP_DIST = 0.95
                        if self.y < -3.5 and en_yakin_robot.y < -3.5:
                            GIVEN_STOP_DIST = 0.65
                            
                        if en_yakin_dist <= GIVEN_STOP_DIST:
                            self.hiz_orani = 0.0
                            return 0.0
                        else:
                            self.hiz_orani = min(1.0, (en_yakin_dist - GIVEN_STOP_DIST) / (r_dist - GIVEN_STOP_DIST))
                else:
                    # Açısal veya yanal yakınlaşmalarda yavaşça yavaşla
                    self.radar_renk = C_COLL_ZONE
                    local_critical = CRITICAL_DIST
                    if self.y < -3.5 and en_yakin_robot.y < -3.5:
                        local_critical = 0.62
                        
                    if en_yakin_dist < local_critical:
                        self.hiz_orani = 0.12
                    else:
                        self.hiz_orani = 0.12 + 0.88 * ((en_yakin_dist - local_critical) / (r_dist - local_critical))
            else:
                # Arkamızda kalan robottan etkilenmiyoruz, yolumuza tam hız devam edebiliriz
                self.hiz_orani = 1.0
                self.avoiding = False
                return baz_hiz

            # Kaçınma Manevrası: Robotu yana itecek teğetsel vektör
            karsi_len = math.hypot(dx, dy)
            if karsi_len > 0 and self.hiz_orani > 0.05:
                # Kaçış genliğini arttırdık (0.35 -> 0.85) böylece daha uzaktan ve geniş bir kavisle geçerler
                sapma_x = (dy / karsi_len) * 0.85
                sapma_y = (-dx / karsi_len) * 0.85
                
                # --- AKILLI GÜVENLİK YÖNLENDİRMESİ ---
                # Robotun rafların arkasına / içine sıkışacak şekilde yanlış yöne kaçmasını önleyelim.
                # Sağ dikey koridorda (x > 1.5): Kaçış yönü her zaman sağa (duvara doğru, x artışı) olmalı.
                if self.x > 1.5 and sapma_x < 0:
                    sapma_x = -sapma_x
                    sapma_y = -sapma_y
                # Sol dikey koridorda (x < -1.5): Kaçış yönü her zaman sola (duvara doğru, x azalışı) olmalı.
                elif self.x < -1.5 and sapma_x > 0:
                    sapma_x = -sapma_x
                    sapma_y = -sapma_y
                # Üst yatay koridorda (y > 3.5): Üst raflara girmemek için kaçış yönü aşağı doğru (y azalışı) olmalı.
                elif self.y > 3.5 and sapma_y > 0:
                    sapma_x = -sapma_x
                    sapma_y = -sapma_y
                    
                self.avoid_vector = (sapma_x, sapma_y)
                
        return baz_hiz * self.hiz_orani

    def ciz(self, surf, sim_sure):
        if not self.aktif or self.sim_sure < self.gecikme:
            return

        # 1. Alt Kısım: Radar/Güvenlik Alanı (Zemin seviyesinde çizilir)
        draw_iso_ellipse(surf, self.x, self.y, 0, RADAR_MESAFE, RADAR_MESAFE * 0.6, self.radar_renk)
        draw_iso_ellipse_border(surf, self.x, self.y, 0, RADAR_MESAFE, RADAR_MESAFE * 0.6, sh(self.radar_renk, 1.5), 1)
        
        # 2. Gölge
        draw_iso_ellipse(surf, self.x, self.y, 0, 0.45, 0.25, (0, 0, 0, 110))

        # 2.5 Robot Farları (Öne doğru sarı ışık huzmesi efekti)
        light_pts = [
            world_to_screen(self.x, self.y, 0.01),
            world_to_screen(self.x + math.cos(self.aci - 0.28) * 2.2, self.y + math.sin(self.aci - 0.28) * 2.2, 0.01),
            world_to_screen(self.x + math.cos(self.aci + 0.28) * 2.2, self.y + math.sin(self.aci + 0.28) * 2.2, 0.01)
        ]
        light_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(light_surf, (255, 235, 140, 24), light_pts)
        surf.blit(light_surf, (0, 0))

        # 3. AGV Robot Gövdesi (3D Kutu)
        ww, wd, wh = 0.40, 0.28, 0.20
        wx = self.x - ww / 2
        wy = self.y - wd / 2
        
        # Eğer bekliyorsa veya manevradaysa yanıp sönen ikaz ışığı efekti
        if self.bekliyor and int(sim_sure * 3) % 2 == 0:
            agv_renk = (255, 255, 255)
        elif self.avoiding and int(sim_sure * 5) % 2 == 0:
            agv_renk = (255, 100, 100) # Kırmızı ikaz
        else:
            agv_renk = self.renk
            
        draw_iso_box(surf, wx, wy, 0, ww, wd, wh, agv_renk)

        # 3.5 Dönen Lidar Tarayıcı (Döner kırmızı laser çizgisi)
        draw_iso_box(surf, self.x - 0.05, self.y - 0.05, wh, 0.10, 0.10, 0.06, (30, 32, 45))
        sweep_angle = sim_sure * 10.0
        lx = self.x + math.cos(sweep_angle) * 0.16
        ly = self.y + math.sin(sweep_angle) * 0.16
        lcx, lcy = world_to_screen(self.x, self.y, wh + 0.03)
        ltx, lty = world_to_screen(lx, ly, wh + 0.03)
        pygame.draw.line(surf, (255, 60, 60), (lcx, lcy), (ltx, lty), 1)

        # 4. Yön Göstergesi (Ön tarafını gösteren parlak LED ve Çizgi)
        led_x = self.x + math.cos(self.aci) * 0.26
        led_y = self.y + math.sin(self.aci) * 0.26
        cx, cy = world_to_screen(self.x, self.y, wh + 0.02)
        tx, ty = world_to_screen(led_x, led_y, wh + 0.02)
        pygame.draw.line(surf, (255, 255, 180), (cx, cy), (tx, ty), 2)
        pygame.draw.circle(surf, (255, 255, 100), (tx, ty), 3)

        # 5. Görev Yükü (Görev Paylaşımı Kapsamında Taşınan Paket/Kutu + Raf/Kamyon Yerleştirme Animasyonları)
        anim_x, anim_y, anim_z = self.x, self.y, wh
        show_box = self.yuk_tasiniyor
        
        if self.bekliyor:
            t_anim = (3.0 - self.bekleme_kalan) / 3.0
            hedef_wp = self.hedef_wp()
            
            if hedef_wp and "WP5" in hedef_wp and self.yuk_tasiniyor:
                # Rafa Yerleştirme Animasyonu
                if t_anim < 0.2:
                    anim_x, anim_y, anim_z = self.x, self.y, wh
                elif t_anim < 0.8:
                    t_slide = (t_anim - 0.2) / 0.6
                    t_slide = t_slide * t_slide * (3 - 2 * t_slide) # Ease-in-out
                    anim_x = self.x
                    anim_y = self.y + 0.8 * t_slide
                    anim_z = wh + (0.66 - wh) * t_slide
                else:
                    anim_x = self.x
                    anim_y = self.y + 0.8
                    anim_z = 0.66
                show_box = True
                
                # Hizalanma ve Yerleştirme Sırasında Yeşil Lazer Kılavuz Çizgisi
                if 0.15 < t_anim < 0.85:
                    p_robot = world_to_screen(self.x, self.y, wh + 0.02)
                    p_shelf = world_to_screen(self.x, self.y + 0.8, 0.66)
                    pygame.draw.line(surf, (100, 255, 100), p_robot, p_shelf, 2)
                    pygame.draw.circle(surf, (100, 255, 100), p_shelf, 4)
                    
                # Başarılı Yerleştirme Halka Efekti
                if t_anim >= 0.8:
                    flash_r = 0.45 * (1.0 - (t_anim - 0.8) / 0.2)
                    draw_iso_ellipse_border(surf, self.x, self.y + 0.8, 0.66, flash_r, flash_r * 0.6, (100, 255, 100), 2)
                    
            elif hedef_wp == "WP1" and not self.yuk_tasiniyor:
                # Kamyondan Yük Alınması Animasyonu
                if t_anim < 0.2:
                    show_box = False
                elif t_anim < 0.8:
                    t_slide = (t_anim - 0.2) / 0.6
                    t_slide = t_slide * t_slide * (3 - 2 * t_slide)
                    anim_x = self.x + 1.2 * (1.0 - t_slide) # Kamyondan x yönünde gelir
                    anim_y = self.y
                    anim_z = wh + (0.50 - wh) * (1.0 - t_slide)
                    show_box = True
                    if self.aktif_gorev:
                        self.yuk_renk = self.aktif_gorev.color
                else:
                    anim_x, anim_y, anim_z = self.x, self.y, wh
                    show_box = True
                    if self.aktif_gorev:
                        self.yuk_renk = self.aktif_gorev.color

        if show_box:
            draw_iso_box(surf, anim_x - 0.16, anim_y - 0.14, anim_z, 0.32, 0.28, 0.22, self.yuk_renk)
            p_top = world_to_screen(anim_x, anim_y, anim_z + 0.22)
            pygame.draw.circle(surf, (255, 255, 255), p_top, 2)

        # 6. Çarpışma Önleme İkaz Balonu ve Kaçış Vektörü Çizimi
        if self.avoiding:
            # Ünlem işareti balonu
            ux, uy = world_to_screen(self.x, self.y, wh + 0.65)
            pygame.draw.circle(surf, (230, 50, 50), (ux, uy - 3), 7)
            pygame.draw.circle(surf, C_WHITE, (ux, uy - 3), 7, 1)
            
            # İçindeki küçük "!" işareti
            font_ikaz = pygame.font.SysFont("arial", 9, bold=True)
            txt_ikaz = font_ikaz.render("!", True, C_WHITE)
            surf.blit(txt_ikaz, (ux - 2, uy - 9))
            # Kaçış Miktarını gösteren yönlü çizgi
            if abs(self.avoid_vector[0]) > 0 or abs(self.avoid_vector[1]) > 0:
                vx, vy = world_to_screen(self.x + self.avoid_vector[0] * 1.5, self.y + self.avoid_vector[1] * 1.5, 0.05)
                rx, ry = world_to_screen(self.x, self.y, 0.05)
                pygame.draw.line(surf, (255, 80, 80), (rx, ry), (vx, vy), 2)
                pygame.draw.circle(surf, (255, 80, 80), (vx, vy), 3)

# ============================================================
# 8. DÜNYA VE DEPO YAPISI SINIFI (Flat Zemin Çizimleri)
# ============================================================
class World:
    def __init__(self, font_kucuk):
        self.font_kucuk = font_kucuk

    def draw_floor_label(self, surf, text, wx, wy, color=(100, 115, 135)):
        sx, sy = world_to_screen(wx, wy)
        lbl = self.font_kucuk.render(text, True, color)
        surf.blit(lbl, (sx - lbl.get_width() // 2, sy))

    def draw_flat_floor(self, surf, show_rota, robotlar):
        # 1. Zemin (Epoksi Beton Renk Tonları)
        draw_iso_polygon(surf, [
            (DUNYA_X_MIN, DUNYA_Y_MIN),
            (DUNYA_X_MAX, DUNYA_Y_MIN),
            (DUNYA_X_MAX, DUNYA_Y_MAX),
            (DUNYA_X_MIN, DUNYA_Y_MAX)
        ], C_FLOOR)

        # 2. Izgara Çizgileri (Derinlik algısı için zemin çizgileri)
        for gx in range(int(DUNYA_X_MIN), int(DUNYA_X_MAX) + 1, 2):
            p1 = world_to_screen(gx, DUNYA_Y_MIN)
            p2 = world_to_screen(gx, DUNYA_Y_MAX)
            pygame.draw.line(surf, C_GRID, p1, p2, 1)
            
        for gy in range(int(DUNYA_Y_MIN), int(DUNYA_Y_MAX) + 1, 2):
            p1 = world_to_screen(DUNYA_X_MIN, gy)
            p2 = world_to_screen(DUNYA_X_MAX, gy)
            pygame.draw.line(surf, C_GRID, p1, p2, 1)

        # 3. Yollar / Şeritler (Koyu Yol Rengi)
        # Alt Yatay Şerit
        draw_iso_polygon(surf, [(DUNYA_X_MIN, -5.5), (DUNYA_X_MAX, -5.5), (DUNYA_X_MAX, -3.5), (DUNYA_X_MIN, -3.5)], C_ROAD)
        # Orta Yatay Şerit (Aesthetic Grid)
        draw_iso_polygon(surf, [(-8.0, -1.6), (8.0, -1.6), (8.0, -0.4), (-8.0, -0.4)], C_ROAD)
        # Robotların Özel Dikey Koridorları (5 Ayrı Yol - Engellerden Arındırılmış)
        for xi in [-3.75, 2.25, 3.75, 6.0, 8.75]:
            draw_iso_polygon(surf, [(xi - 0.4, DUNYA_Y_MIN), (xi + 0.4, DUNYA_Y_MIN), (xi + 0.4, DUNYA_Y_MAX), (xi - 0.4, DUNYA_Y_MAX)], C_ROAD)
        # Üst Bölge Yolu
        draw_iso_polygon(surf, [(-5.0, 3.8), (10.0, 3.8), (10.0, 6.2), (-5.0, 6.2)], C_ROAD)

        # 4. Güvenlik Şeritleri (Sarı-Siyah Çizgi - İki Şerit Arasındaki Bölücü Çizgi)
        for xo in range(int(DUNYA_X_MIN), int(DUNYA_X_MAX), 2):
            p1 = world_to_screen(xo, -5.1, 0.01)
            p2 = world_to_screen(xo + 1.0, -5.1, 0.01)
            pygame.draw.line(surf, C_SAFE_LINE, p1, p2, 2)

        # 5. Rota Gösterimleri (Tercihe Bağlı İnce Kesik Çizgiler)
        if show_rota:
            for r in robotlar:
                if not r.aktif: continue
                # Aktif göreve ait rotayı çiz
                pts = [world_to_screen(*WP[k], 0.02) for k in (r.gidis_rotasi if r.gidis else r.donus_rotasi)]
                for i in range(len(pts)-1):
                    pygame.draw.line(surf, sh(r.renk, 0.6), pts[i], pts[i+1], 1)

        # 6. Duvarlar (Derinlik İçin Arka Kısımlara 3D Yapı Çizilir)
        # Kuzey Duvarı
        draw_iso_box(surf, DUNYA_X_MIN, DUNYA_Y_MAX, 0, DUNYA_X_MAX - DUNYA_X_MIN, 0.4, 2.2, (50, 55, 70))
        # Doğu Duvarı
        draw_iso_box(surf, DUNYA_X_MAX, DUNYA_Y_MIN, 0, 0.4, DUNYA_Y_MAX - DUNYA_Y_MIN, 2.2, (45, 50, 65))

        # 7. Premium Zemin Etiketleri
        self.draw_floor_label(surf, "--- HIGHTECH WAREHOUSE PRIVATE HIGHWAY SYSTEM ---", 0.0, -6.5, (95, 105, 130))
        self.draw_floor_label(surf, ">>> GOING LANE (y = -5.4) >>>", 3.0, -5.6, (100, 200, 150))
        self.draw_floor_label(surf, "<<< RETURNING LANE (y = -4.8) <<<", 3.0, -4.2, (220, 140, 120))
        self.draw_floor_label(surf, "<<< TRUCK UNLOADING DOCK (WP1) <<<", 0.0, -5.9, (160, 130, 110))

# ============================================================
# 9. HUD PANELİ VE GRAFİKSEL BİLGİ ARA YÜZÜ (Görev & Çarpışma Ekranı)
# ============================================================
class HUD:
    def __init__(self, task_manager):
        self.x = REND_W + 5
        self.y = 5
        self.w = HUD_W - 10
        self.h = H - 10
        self.task_manager = task_manager

    def draw(self, surf, robotlar, sim_t, fps, hiz, fn, fs, vis):
        if not vis:
            return
            
        # HUD Panel Arka Planı ve Izgara Deseni (Premium Dashboard Görünümü)
        s_hud = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        s_hud.fill((12, 14, 24, 235))
        for i in range(0, self.w, 20):
            pygame.draw.line(s_hud, (40, 45, 65, 20), (i, 0), (i, self.h), 1)
        for j in range(0, self.h, 20):
            pygame.draw.line(s_hud, (40, 45, 65, 20), (0, j), (self.w, j), 1)
        surf.blit(s_hud, (self.x, self.y))
        pygame.draw.rect(surf, (60, 65, 95), (self.x, self.y, self.w, self.h), 1)

        # Başlık ve Üst Bölüm
        pygame.draw.rect(surf, (30, 35, 55), (self.x + 2, self.y + 2, self.w - 4, 30))
        title = fn.render("DEPO FİLO YÖNETİMİ", True, (240, 200, 30))
        surf.blit(title, (self.x + 10, self.y + 8))

        yy = self.y + 40
        def satir(text, color=(200, 200, 220), fnt=fs):
            nonlocal yy
            txt = fnt.render(text, True, color)
            surf.blit(txt, (self.x + 10, yy))
            yy += txt.get_height() + 3

        # Genel Sistem Metrikleri
        satir(f"Sim Süresi: {sim_t:.1f}s   FPS: {fps:.0f}   Hız: {hiz}x", C_WHITE)
        
        # Fütüristik Sistem Çalışma Durumu Neon Rozeti
        pygame.draw.rect(surf, (20, 40, 30), (self.x + 10, yy, self.w - 20, 22), border_radius=4)
        pygame.draw.rect(surf, (50, 200, 100), (self.x + 10, yy, self.w - 20, 22), 1, border_radius=4)
        if int(sim_t * 2.0) % 2 == 0:
            pygame.draw.circle(surf, (100, 255, 120), (self.x + 20, yy + 11), 4)
        else:
            pygame.draw.circle(surf, (30, 120, 60), (self.x + 20, yy + 11), 4)
        txt_sys = fs.render("FİLO AKTİF - MONİTÖR ÇEVRİMİÇİ", True, (120, 255, 150))
        surf.blit(txt_sys, (self.x + 32, yy + 5))
        yy += 28

        satir(f"Tamamlanan Görev Sayısı: {self.task_manager.completed_count}", (100, 255, 120), fn)
        
        # Çizgi Bölücü
        pygame.draw.line(surf, (50, 55, 80), (self.x + 8, yy), (self.x + self.w - 8, yy), 1)
        yy += 6

        # Görev Paylaşımı ve Robot Bilgileri Bölümü
        satir("ROBOT AKTİF İŞ YÜKÜ VE GÖREVLER", (140, 180, 250), fn)
        yy += 4

        for r in robotlar:
            # Robot İsmi ve Durum Kutusu
            pygame.draw.rect(surf, r.renk, (self.x + 10, yy + 2, 8, 12))
            txt_name = fn.render(f" {r.isim.upper()}", True, r.renk)
            surf.blit(txt_name, (self.x + 22, yy))
            
            # Çarpışma Uyarı Rozeti
            if r.avoiding:
                pygame.draw.rect(surf, (220, 50, 50), (self.x + self.w - 110, yy + 1, 95, 13))
                txt_avoid = fs.render("! ÇARPIŞMA ÖNLEME", True, C_WHITE)
                surf.blit(txt_avoid, (self.x + self.w - 106, yy + 2))
            else:
                pygame.draw.rect(surf, (50, 150, 80), (self.x + self.w - 60, yy + 1, 45, 13))
                txt_ok = fs.render("GÜVENLİ", True, C_WHITE)
                surf.blit(txt_ok, (self.x + self.w - 56, yy + 2))
                
            yy += 16
            
            if r.aktif:
                # Görev Detayları
                if r.aktif_gorev:
                    satir(f"  Görev ID: #{r.aktif_gorev.id_num} | Hedef: {r.aktif_gorev.target}", (200, 200, 180))
                    satir(f"  Durum   : {r.durum}", (160, 220, 160))
                else:
                    satir("  Görev Bekleniyor...", C_GRAY)
                
                # Konum ve Tur Bilgisi
                satir(f"  Tur: {r.tamamlanan_tur} | Konum: ({r.x:.1f}, {r.y:.1f})", C_GRAY)
            else:
                satir(f"  Pasif (Bekleme Süresi: {r.gecikme}s)", C_GRAY)
                
            # Alt çizgi
            pygame.draw.line(surf, (35, 40, 60), (self.x + 8, yy + 2), (self.x + self.w - 8, yy + 2), 1)
            yy += 8

        # Görev Havuzu İzleyici
        satir("AKTİF GÖREV AKIŞI (TASK ALLOCATION)", (140, 180, 250), fn)
        yy += 4
        
        # Son 3 görevi listeleme
        pool = [t for t in self.task_manager.active_tasks if t.status != "Tamamlandı"][-3:]
        if not pool:
            satir("  Bekleyen görev yok.", C_GRAY)
        else:
            for t in pool:
                status_color = (250, 180, 50) if t.status == "Taşınıyor" else (150, 150, 150)
                satir(f"  G#{t.id_num} | {t.source} -> {t.target} | [{t.status}]", status_color)
                
        yy = self.h - 140
        pygame.draw.line(surf, (55, 60, 85), (self.x + 8, yy), (self.x + self.w - 8, yy), 1)
        yy += 6
        
        # Kontroller ve Kısayol Açıklamaları
        satir("[P] Duraklat  [R] Sıfırla  [T] Rota", C_GRAY)
        satir("[SPACE / S] Hız (1x, 2x, 5x)", C_GRAY)
        satir("[Arrow Keys] Görünümü Kaydır", C_GRAY)
        satir("[Mouse Wheel / I / O] Yakınlaş/Uzaklaş", C_GRAY)
        satir("[ESC] Çıkış", C_GRAY)

# ============================================================
# 10. SİMÜLASYON YÖNETİCİ SINIFI (Ana Döngü ve Başlangıç Noktası)
# ============================================================
class Simulation:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Multi-Robot Warehouse Sim 2.5D (Görev & Çarpışma Önleme)")
        self.ekran = pygame.display.set_mode((W, H))
        self.saat = pygame.time.Clock()

        # Yazı Tipleri Yükleme
        try:
            self.font_kalin = pygame.font.SysFont("consolas", 13, bold=True)
            self.font_kucuk = pygame.font.SysFont("consolas", 11)
            self.font_buyuk = pygame.font.SysFont("consolas", 18, bold=True)
        except Exception:
            self.font_kalin = pygame.font.Font(None, 14)
            self.font_kucuk = pygame.font.Font(None, 12)
            self.font_buyuk = pygame.font.Font(None, 18)

        # Durum Yöneticileri
        self.task_manager = TaskManager()
        
        # Robotların Tanımlanması
        self.robotlar = []
        for tanim in ROBOT_TANIMLARI:
            self.robotlar.append(Robot(tanim, self.robotlar, self.task_manager))

        # Çevre ve HUD Tanımları
        self.world = World(self.font_kucuk)
        self.hud = HUD(self.task_manager)

        # Simülasyon Kontrol Değişkenleri
        self.duraklatildi = False
        self.hiz_idx = 0
        self.hiz_secenekleri = [1, 2, 5]
        self.show_hud = True
        self.show_rota = True
        self.sim_sure = 0.0

        # Sürükle-Bırak Kamera Kontrolleri
        self.dragging_camera = False
        self.drag_start_pos = (0, 0)
        self.drag_start_rc = (0, 0)

    def sifirla(self):
        """Tüm robotları ve görev yöneticisini sıfırlar."""
        self.sim_sure = 0.0
        self.task_manager = TaskManager()
        for r in self.robotlar:
            r.task_manager = self.task_manager
            r._sifirla()
        self.hud.task_manager = self.task_manager

    def run(self):
        global ISO, RCX, RCY
        devam = True
        while devam:
            # Saniye bazında geçen zamanı hesaplama
            ham_dt = self.saat.tick(FPS_HEDEF) / 1000.0
            fps = self.saat.get_fps()

            # Klavye / Fare Olaylarının Dinlenmesi
            for olay in pygame.event.get():
                if olay.type == pygame.QUIT:
                    devam = False
                elif olay.type == pygame.MOUSEBUTTONDOWN:
                    if olay.button == 1:    # Sol Tık (Sürükleme Başlangıcı)
                        # HUD menüsünün üzerine tıklanarak sürüklenmesini önlemek için
                        if olay.pos[0] < REND_W:
                            self.dragging_camera = True
                            self.drag_start_pos = olay.pos
                            self.drag_start_rc = (RCX, RCY)
                    elif olay.button == 4:    # Tekerlek Yukarı (Yakınlaştır)
                        ISO = min(80, ISO + 2)
                    elif olay.button == 5:  # Tekerlek Aşağı (Uzaklaştır)
                        ISO = max(10, ISO - 2)
                elif olay.type == pygame.MOUSEBUTTONUP:
                    if olay.button == 1:    # Sol Tık Bırakma
                        self.dragging_camera = False
                elif olay.type == pygame.MOUSEMOTION:
                    if self.dragging_camera:
                        dx = olay.pos[0] - self.drag_start_pos[0]
                        dy = olay.pos[1] - self.drag_start_pos[1]
                        RCX = self.drag_start_rc[0] + dx
                        RCY = self.drag_start_rc[1] + dy
                elif olay.type == pygame.KEYDOWN:
                    if olay.key == pygame.K_ESCAPE:
                        devam = False
                    elif olay.key == pygame.K_p:
                        self.duraklatildi = not self.duraklatildi
                    elif olay.key in (pygame.K_s, pygame.K_SPACE):
                        self.hiz_idx = (self.hiz_idx + 1) % len(self.hiz_secenekleri)
                    elif olay.key == pygame.K_r:
                        self.sifirla()
                    elif olay.key == pygame.K_h:
                        self.show_hud = not self.show_hud
                    elif olay.key == pygame.K_t:
                        self.show_rota = not self.show_rota

            # Sürekli klavye durum takibi (Kamera kaydırma ve hassas zoom için)
            keys = pygame.key.get_pressed()
            
            # Ok tuşları ile kamerayı kaydır
            pan_hiz = 6
            if keys[pygame.K_LEFT]:  RCX += pan_hiz
            if keys[pygame.K_RIGHT]: RCX -= pan_hiz
            if keys[pygame.K_UP]:    RCY += pan_hiz
            if keys[pygame.K_DOWN]:  RCY -= pan_hiz
            
            # I ve O tuşları ile hassas yakınlaşma/uzaklaşma
            if keys[pygame.K_i]: ISO = min(80, ISO + 0.4)
            if keys[pygame.K_o]: ISO = max(10, ISO - 0.4)

            # Simülasyon fizik güncellemeleri
            hiz = self.hiz_secenekleri[self.hiz_idx]
            if not self.duraklatildi:
                dt = min(ham_dt, 0.05) * hiz
                self.sim_sure += dt
                for r in self.robotlar:
                    r.guncelle(dt, self.sim_sure)

            # Ekranı temizleme
            self.ekran.fill(C_BG)

            # Sol Kısım: Simülasyon Çizim Ekranı Clip Edilir (HUD panelini ezmemesi için)
            clip_rect = pygame.Rect(0, 0, REND_W, H)
            self.ekran.set_clip(clip_rect)

            # 1. DÜZ ELEMANLAR (Zemin, Izgara, Şeritler ve Rotalar)
            self.world.draw_flat_floor(self.ekran, self.show_rota, self.robotlar)

            # 2. BİRLEŞİK 3D ELEMANLARI TOPLAMA (Raflar, Engeller, Bayraklar ve Robotlar)
            drawables = []

            # A) Depo Rafları Çizimleri
            random.seed(999) # Sabit renk tohumu
            for rx, ry in RAFLAR:
                ww, wd, wh = 1.25, 0.55, 1.60
                wx = rx - ww / 2
                wy = ry - wd / 2
                
                # Her rafın ahşap panel kutu renklerini tohumlu üretelim
                kat_kutular = []
                for kat in range(3):
                    kutular = []
                    for kutu_idx in range(3):
                        kutu_col = (random.randint(100, 220), random.randint(90, 160), random.randint(40, 120))
                        kutular.append(kutu_col)
                    kat_kutular.append(kutular)

                # Çizim callback'i
                def draw_rack(surf, wx=wx, wy=wy, ww=ww, wd=wd, wh=wh, kat_kutular=kat_kutular):
                    # Metal İskelet Ayakları ve Raflar
                    draw_iso_box(surf, wx, wy, 0, ww, wd, wh, (70, 80, 95))
                    # 3 Katlı Raf Bölmeleri
                    for kat in range(3):
                        kat_h = 0.10 + kat * 0.52
                        draw_iso_box(surf, wx + 0.04, wy + 0.02, kat_h, ww - 0.08, wd - 0.04, 0.04, (130, 95, 55))
                        # Kutu Ürünleri
                        for kutu_idx in range(3):
                            kutu_x = wx + 0.08 + kutu_idx * 0.36
                            draw_iso_box(surf, kutu_x, wy + 0.08, kat_h + 0.04, 0.28, wd - 0.16, 0.35, kat_kutular[kat][kutu_idx])

                drawables.append({
                    'depth': -(rx + ry),
                    'draw': draw_rack
                })

            # B) Statik Engeller Çizimleri
            for ad, ox, oy, ow, od, oh, col in ENGELLER:
                def draw_obstacle(surf, ad=ad, ox=ox, oy=oy, ow=ow, od=od, oh=oh, col=col):
                    draw_iso_ellipse(surf, ox, oy, 0, ow * 0.6, od * 0.6, (0, 0, 0, 100))
                    draw_iso_box(surf, ox - ow/2, oy - od/2, 0, ow, od, oh, col)
                    tx, ty = world_to_screen(ox, oy, oh + 0.2)
                    lbl = self.world.font_kucuk.render(ad, True, (200, 190, 170))
                    surf.blit(lbl, (tx - lbl.get_width() // 2, ty))

                drawables.append({
                    'depth': -(ox + oy),
                    'draw': draw_obstacle
                })

            # C) Waypoint Çizimleri (Bayraklar yerine dönen holografik parlayan kristaller)
            for key, pos in WP.items():
                def draw_wp(surf, key=key, pos=pos):
                    f_col = (230, 200, 30)
                    if "WP5" in key:
                        f_col = (50, 200, 250)
                    elif "WP1" in key:
                        f_col = (250, 80, 80)
                    
                    # 1. Zemin halkası (Pulsing ring)
                    pulse_val = math.sin(self.sim_sure * 5.0 + hash(key) % 10)
                    pulse_r = 0.35 + 0.08 * pulse_val
                    draw_iso_ellipse_border(surf, pos[0], pos[1], 0.01, pulse_r, pulse_r * 0.6, sh(f_col, 1.2), 1)
                    draw_iso_ellipse(surf, pos[0], pos[1], 0.01, pulse_r * 0.6, pulse_r * 0.36, (*sh(f_col, 0.4), 30))
                    
                    # 2. İnce dikey ışın sütunu
                    base_pos = world_to_screen(pos[0], pos[1], 0)
                    top_h = 1.0 + 0.1 * pulse_val
                    top_pos = world_to_screen(pos[0], pos[1], top_h)
                    pygame.draw.line(surf, (*sh(f_col, 0.6), 80), base_pos, top_pos, 1)

                    # 3. Dönen Holografik Kristal Çizimi
                    h_center = 0.8 + 0.08 * pulse_val
                    rot_aci = self.sim_sure * 2.0 + hash(key) % 10
                    pts_offset = [
                        (math.cos(rot_aci) * 0.14, math.sin(rot_aci) * 0.14),
                        (math.cos(rot_aci + math.pi/2) * 0.14, math.sin(rot_aci + math.pi/2) * 0.14),
                        (math.cos(rot_aci + math.pi) * 0.14, math.sin(rot_aci + math.pi) * 0.14),
                        (math.cos(rot_aci + 3*math.pi/2) * 0.14, math.sin(rot_aci + 3*math.pi/2) * 0.14),
                    ]
                    
                    pt_top = world_to_screen(pos[0], pos[1], h_center + 0.22)
                    pt_bot = world_to_screen(pos[0], pos[1], h_center - 0.22)
                    pt_mid = [world_to_screen(pos[0] + dx, pos[1] + dy, h_center) for dx, dy in pts_offset]
                    
                    col_top1 = sh(f_col, 1.2)
                    col_top2 = sh(f_col, 0.9)
                    col_bot1 = sh(f_col, 0.7)
                    col_bot2 = sh(f_col, 0.5)
                    
                    # Üst koni
                    pygame.draw.polygon(surf, col_top1, [pt_top, pt_mid[0], pt_mid[1]])
                    pygame.draw.polygon(surf, col_top2, [pt_top, pt_mid[1], pt_mid[2]])
                    pygame.draw.polygon(surf, col_top1, [pt_top, pt_mid[2], pt_mid[3]])
                    pygame.draw.polygon(surf, col_top2, [pt_top, pt_mid[3], pt_mid[0]])
                    
                    # Alt koni
                    pygame.draw.polygon(surf, col_bot1, [pt_bot, pt_mid[0], pt_mid[1]])
                    pygame.draw.polygon(surf, col_bot2, [pt_bot, pt_mid[1], pt_mid[2]])
                    pygame.draw.polygon(surf, col_bot1, [pt_bot, pt_mid[2], pt_mid[3]])
                    pygame.draw.polygon(surf, col_bot2, [pt_bot, pt_mid[3], pt_mid[0]])
                    
                    # Parlak kenarlar
                    for i in range(4):
                        pygame.draw.line(surf, C_WHITE, pt_mid[i], pt_mid[(i+1)%4], 1)
                        pygame.draw.line(surf, C_WHITE, pt_top, pt_mid[i], 1)
                        pygame.draw.line(surf, C_WHITE, pt_bot, pt_mid[i], 1)
                        
                    # Yazı Etiketi
                    lbl = self.world.font_kucuk.render(key, True, C_WHITE)
                    lbl_w, lbl_h = lbl.get_size()
                    lbl_pos = (pt_top[0] - lbl_w // 2, pt_top[1] - 22)
                    pygame.draw.rect(surf, (15, 17, 26, 180), (lbl_pos[0] - 4, lbl_pos[1] - 2, lbl_w + 8, lbl_h + 4), border_radius=3)
                    pygame.draw.rect(surf, sh(f_col, 0.8), (lbl_pos[0] - 4, lbl_pos[1] - 2, lbl_w + 8, lbl_h + 4), 1, border_radius=3)
                    surf.blit(lbl, lbl_pos)

                drawables.append({
                    'depth': -(pos[0] + pos[1]),
                    'draw': draw_wp
                })

            # D) Aktif Robotlar Çizimleri
            for r in self.robotlar:
                if not r.aktif or self.sim_sure < r.gecikme:
                    continue
                def draw_robot(surf, r=r):
                    r.ciz(surf, self.sim_sure)

                drawables.append({
                    'depth': -(r.x + r.y),
                    'draw': draw_robot
                })

            # 3. DERİNLİK SIRALAMASINA GÖRE ÇİZ (Painter's Algorithm)
            drawables.sort(key=lambda d: d['depth'])
            for item in drawables:
                item['draw'](self.ekran)

            self.ekran.set_clip(None)

            # Çizim alanı ile HUD paneli arasındaki dikey çizgi
            pygame.draw.line(self.ekran, (55, 60, 85), (REND_W, 0), (REND_W, H), 1)

            # Sağ Kısım: HUD Bilgilendirme Ekranının Çizilmesi
            self.hud.draw(self.ekran, self.robotlar, self.sim_sure, fps, hiz, 
                          self.font_kalin, self.font_kucuk, self.show_hud)

            # Duraklatıldı İkaz Yazısı Çizimi
            if self.duraklatildi:
                txt_pause = self.font_buyuk.render("⏸  SIMÜLASYON DURAKLATILDI", True, (250, 200, 30))
                self.ekran.blit(txt_pause, (20, 20))

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

# ============================================================
# 11. BAŞLATICI (MAIN ENTRY)
# ============================================================
if __name__ == "__main__":
    try:
        sim = Simulation()
        sim.run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)
