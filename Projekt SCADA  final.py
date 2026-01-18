import sys 

import math 

import random 

from datetime import datetime 

 

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,  

                             QPushButton, QLabel, QHBoxLayout, QTabWidget,  

                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 

                             QGroupBox, QDoubleSpinBox, QGridLayout, QComboBox) 

from PyQt5.QtCore import QTimer, Qt 

from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF 

from PyQt5.QtCore import QPointF 

 

# ========================================== 

# 1. KONFIGURACJA MOTYWÓW (Dla pełnego dopasowania) 

# ========================================== 

 

THEMES = { 

    "Jasny (Biuro)": { 

        "bg": "#f0f0f0", "text": "#000000", "outline": "#000000", 

        "pipe_off": "#cccccc", "pipe_on": "#0064ff", 

        "water": (0, 150, 255, 200), "tank_bg": (255, 255, 255, 255) 

    }, 

    "Ciemny (Nocny)": { 

        "bg": "#2b2b2b", "text": "#ffffff", "outline": "#ffffff", 

        "pipe_off": "#555555", "pipe_on": "#4488ff", 

        "water": (0, 100, 200, 180), "tank_bg": (60, 60, 60, 255) 

    }, 

    "Szary (Przemysłowy)": { 

        "bg": "#808080", "text": "#000000", "outline": "#333333", 

        "pipe_off": "#666666", "pipe_on": "#003366", 

        "water": (0, 80, 150, 200), "tank_bg": (180, 180, 180, 255) 

    }, 

    "Niebieski (Blueprint)": { 

        "bg": "#001f3f", "text": "#7FDBFF", "outline": "#7FDBFF", 

        "pipe_off": "#003366", "pipe_on": "#FFFFFF", 

        "water": (127, 219, 255, 100), "tank_bg": (0, 31, 63, 50) 

    }, 

    "Jesień (Brąz/Rdza)": { 

        "bg": "#3e2723", "text": "#ffecb3", "outline": "#8d6e63", 

        "pipe_off": "#5d4037", "pipe_on": "#ffca28", 

        "water": (255, 111, 0, 180), "tank_bg": (62, 39, 35, 200) # Woda pomarańczowa 

    }, 

    "Cyberpunk (Neon)": { 

        "bg": "#0a0a12", "text": "#00ff00", "outline": "#ff00ff", 

        "pipe_off": "#1a1a1a", "pipe_on": "#00ffff", 

        "water": (0, 255, 0, 150), "tank_bg": (20, 20, 30, 255) # Toksyczna zieleń 

    }, 

    "Matrix (Zielony neon/Czarny)": { 

        "bg": "#000000", "text": "#00ff00", "outline": "#008f11", 

        "pipe_off": "#003300", "pipe_on": "#ccffcc", 

        "water": (0, 255, 0, 80), "tank_bg": (0, 20, 0, 255) 

    }, 

    "Wampir (Krwisty)": { 

        "bg": "#1a0000", "text": "#ff9999", "outline": "#ff0000", 

        "pipe_off": "#400000", "pipe_on": "#ff0000", 

        "water": (200, 0, 0, 180), "tank_bg": (30, 0, 0, 255) # Czerwona woda 

    }, 

} 

 

# ========================================== 

# 2. MODEL (FIZYKA) 

# ========================================== 

 

class ElementWizualizacji: 

    def __init__(self): 

        self.alarm_phase = 0.0 

        self.alarm_speed = 0.2 

        self.stan_alarmowy = False  

 

    def aktualizuj_animacje(self): 

        if self.stan_alarmowy: 

            self.alarm_phase += self.alarm_speed 

 

    def pobierz_kolor_alarmu(self): 

        if not self.stan_alarmowy: 

            return None 

        intensity = (math.sin(self.alarm_phase) + 1) / 2  

        alpha = int(50 + (150 * intensity)) 

        return QColor(255, 0, 0, alpha) 

 

class Zbiornik(ElementWizualizacji): 

    def __init__(self, x, y, w, h, max_poj, nazwa): 

        super().__init__() 

        self.rect = (x, y, w, h) 

        self.max_poj = float(max_poj) 

        self.poziom = 0.0 

        self.nazwa = nazwa 

 

    def dodaj_ciecz(self, ilosc): 

        self.poziom += ilosc 

        return self.poziom > self.max_poj 

 

    def pobierz_ciecz(self, ilosc): 

        real_take = min(self.poziom, ilosc) 

        self.poziom -= real_take 

        return real_take 

 

    @property 

    def procent_zapelnienia(self): 

        if self.max_poj == 0: return 0 

        return self.poziom / self.max_poj 

 

class Pompa(ElementWizualizacji): 

    def __init__(self, x, y, nazwa): 

        super().__init__() 

        self.x = x 

        self.y = y 

        self.nazwa = nazwa 

        self.aktywna = False 

        self.wydajnosc = 5.0 

        self.licznik_suchobiegu = 0  

 

class Zawor(ElementWizualizacji): 

    def __init__(self, x, y, nazwa): 

        super().__init__() 

        self.x = x 

        self.y = y 

        self.nazwa = nazwa 

        self.otwarty = False 

 

class Rura(ElementWizualizacji): 

    def __init__(self, punkty): 

        super().__init__() 

        self.punkty = punkty 

        self.czy_plynie = False 

 

# ========================================== 

# 3. WIDOK (RYSOWANIE) 

# ========================================== 

 

class EkranProcesu(QWidget): 

    def __init__(self, zbiorniki, pompy, rury, zawory): 

        super().__init__() 

        self.zbiorniki = zbiorniki 

        self.pompy = pompy 

        self.rury = rury 

        self.zawory = zawory 

        self.setMinimumSize(800, 600) 

         

        # Domyślny motyw 

        self.current_theme = THEMES["Jasny (Biuro)"] 

 

    def ustaw_motyw(self, nazwa_motywu): 

        if nazwa_motywu in THEMES: 

            self.current_theme = THEMES[nazwa_motywu] 

            self.update() 

 

    def paintEvent(self, event): 

        qp = QPainter(self) 

        qp.setRenderHint(QPainter.Antialiasing) 

 

        # 1. TŁO 

        bg_col = QColor(self.current_theme["bg"]) 

        qp.fillRect(event.rect(), bg_col) 

 

        # Pobieranie kolorów z motywu 

        col_text = QColor(self.current_theme["text"]) 

        col_outline = QColor(self.current_theme["outline"]) 

        col_pipe_off = QColor(self.current_theme["pipe_off"]) 

        col_pipe_on = QColor(self.current_theme["pipe_on"]) 

        col_water = QColor(*self.current_theme["water"]) 

        col_tank_bg = QColor(*self.current_theme["tank_bg"]) 

 

        # 2. RYSOWANIE RUR 

        for rura in self.rury: 

            if rura.czy_plynie: 

                col = col_pipe_on 

                width = 10 

            else: 

                col = col_pipe_off 

                width = 8 

 

            qp.setPen(QPen(col, width, Qt.SolidLine, Qt.RoundCap)) 

            for i in range(len(rura.punkty) - 1): 

                p1 = rura.punkty[i] 

                p2 = rura.punkty[i+1] 

                qp.drawLine(p1[0], p1[1], p2[0], p2[1]) 

 

        # 3. RYSOWANIE ZBIORNIKÓW 

        for z in self.zbiorniki: 

            x, y, w, h = z.rect 

             

            # Wypełnienie tła zbiornika 

            qp.setPen(Qt.NoPen) 

            qp.setBrush(col_tank_bg) 

            qp.drawRect(x, y, w, h) 

 

            # Obrys 

            qp.setPen(QPen(col_outline, 3)) 

            qp.setBrush(Qt.NoBrush) 

            qp.drawRect(x, y, w, h) 

 

            # Ciecz (Kolor zależny od motywu!) 

            if z.poziom > 0: 

                procent_wizualny = min(z.poziom / z.max_poj, 1.0) 

                wys_cieczy = int(h * procent_wizualny) 

                 

                qp.setBrush(QBrush(col_water)) 

                qp.setPen(Qt.NoPen) 

                qp.drawRect(x + 2, y + h - wys_cieczy, w - 4, wys_cieczy) 

 

            # Teksty 

            qp.setPen(col_text) 

            font = qp.font(); font.setBold(True); font.setPointSize(10); qp.setFont(font) 

            qp.drawText(x, y - 25, z.nazwa) 

            font.setBold(False); font.setPointSize(9); qp.setFont(font) 

            qp.drawText(x, y - 5, f"{int(z.poziom)}/{int(z.max_poj)} L") 

             

            # Alarm wizualny (Przepełnienie) 

            if z.stan_alarmowy: 

                alarm_col = z.pobierz_kolor_alarmu() 

                if alarm_col: 

                    qp.setBrush(QBrush(alarm_col)) 

                    qp.setPen(Qt.NoPen) 

                    qp.drawRect(x-5, y-5, w+10, h+10) 

                    qp.setPen(Qt.red); font.setBold(True); qp.setFont(font) 

                    qp.drawText(x + 10, y + int(h/2), "PRZEPEŁNIENIE!") 

 

        # 4. RYSOWANIE ZAWORÓW 

        for v in self.zawory: 

            size = 15 

            c = QPointF(v.x, v.y) 

            p1 = QPointF(c.x() - size, c.y() - size) 

            p2 = QPointF(c.x() - size, c.y() + size) 

            p3 = c 

            p4 = QPointF(c.x() + size, c.y() - size) 

            p5 = QPointF(c.x() + size, c.y() + size) 

             

            col = QColor(0, 255, 0) if v.otwarty else QColor(255, 0, 0) 

            qp.setBrush(QBrush(col)) 

            qp.setPen(QPen(col_outline, 1)) 

             

            qp.drawPolygon(QPolygonF([p1, p2, p3])) 

            qp.drawPolygon(QPolygonF([p3, p4, p5])) 

             

            qp.setPen(col_text) 

            qp.drawText(int(v.x) - 15, int(v.y) - 20, v.nazwa) 

 

 

        # 5. RYSOWANIE POMP 

        for p in self.pompy: 

            # Baza pompy 

            base_color = QColor(0, 200, 0) if p.aktywna else QColor(100, 100, 100) 

            qp.setBrush(QBrush(base_color)) 

            qp.setPen(QPen(col_outline, 2)) 

            qp.drawEllipse(p.x - 20, p.y - 20, 40, 40) 

             

            if p.aktywna: 

                qp.setPen(QPen(col_text, 2)) # Wirnik w kolorze tekstu 

                offset = int(datetime.now().microsecond / 100000) 

                qp.drawLine(p.x - 15, p.y, p.x + 15, p.y) 

                qp.drawLine(p.x, p.y - 15, p.x, p.y + 15) 

 

            qp.setPen(col_text) 

            qp.drawText(p.x - 20, p.y + 35, p.nazwa) 

 

            # Alarm suchobiegu 

            if p.stan_alarmowy: 

                alarm_col = p.pobierz_kolor_alarmu() 

                if alarm_col: 

                    qp.setBrush(QBrush(alarm_col)) 

                    qp.setPen(Qt.NoPen) 

                    qp.drawEllipse(p.x - 25, p.y - 25, 50, 50) 

                    qp.setPen(Qt.red) 

                    qp.drawText(p.x - 30, p.y - 30, "SUCHOBIEG!") 

                     

                    # Odliczanie 

                    pozostalo = 5.0 - (p.licznik_suchobiegu * 0.05) 

                    if pozostalo > 0: 

                        qp.setPen(Qt.yellow) 

                        qp.drawText(p.x - 10, p.y + 5, f"{pozostalo:.1f}s") 

 

# ========================================== 

# 4. KONTROLER (LOGIKA I GUI) 

# ========================================== 

 

class ScadaApp(QMainWindow): 

    def __init__(self): 

        super().__init__() 

        self.setWindowTitle("SCADA Pro - System Nadzoru v4.0 Final") 

        self.resize(1200, 850) 

 

        self.init_objects() 

         

        self.tabs = QTabWidget() 

        self.setCentralWidget(self.tabs) 

 

        self.tab_wiz = QWidget() 

        self.setup_wizualizacja() 

        self.tabs.addTab(self.tab_wiz, "Panel Operatorski") 

 

        self.tab_logi = QWidget() 

        self.setup_logi() 

        self.tabs.addTab(self.tab_logi, "Dziennik Zdarzeń") 

 

        self.timer = QTimer() 

        self.timer.timeout.connect(self.main_loop) 

        self.timer.start(50)  

 

        self.log_event("INFO", "System uruchomiony.") 

 

    def setup_wizualizacja(self): 

        layout = QHBoxLayout(self.tab_wiz) 

        self.ekran = EkranProcesu(self.zbiorniki, self.pompy, self.rury, self.zawory) 

        layout.addWidget(self.ekran, stretch=3) 

 

        panel = QWidget() 

        panel.setFixedWidth(320) 

        panel_layout = QVBoxLayout(panel) 

 

        # Motywy 

        grp_wyglad = QGroupBox("Motyw Graficzny") 

        lay_wyglad = QVBoxLayout() 

        self.combo_tlo = QComboBox() 

        self.combo_tlo.addItems(list(THEMES.keys())) 

        self.combo_tlo.currentTextChanged.connect(self.ekran.ustaw_motyw) 

        lay_wyglad.addWidget(self.combo_tlo) 

        grp_wyglad.setLayout(lay_wyglad) 

        panel_layout.addWidget(grp_wyglad) 

 

        # Pompy z WYDAJNOŚCIĄ 

        grp_pompy = QGroupBox("Sterowanie Pompami") 

        lay_pompy = QGridLayout() 

         

        # P1 

        self.btn_p1 = QPushButton("P-1 Start") 

        self.btn_p1.setCheckable(True) 

        self.btn_p1.clicked.connect(lambda: self.toggle_pump(self.p1, self.btn_p1)) 

         

        self.spin_p1 = QDoubleSpinBox() 

        self.spin_p1.setRange(0.1, 50.0); self.spin_p1.setValue(5.0); self.spin_p1.setSuffix(" L/cykl") 

        self.spin_p1.valueChanged.connect(lambda v: setattr(self.p1, 'wydajnosc', v)) 

         

        lay_pompy.addWidget(QLabel("Pompa P-1:"), 0, 0) 

        lay_pompy.addWidget(self.btn_p1, 0, 1) 

        lay_pompy.addWidget(QLabel("Wydajność:"), 1, 0) 

        lay_pompy.addWidget(self.spin_p1, 1, 1) 

         

        # P2 

        self.btn_p2 = QPushButton("P-2 Start") 

        self.btn_p2.setCheckable(True) 

        self.btn_p2.clicked.connect(lambda: self.toggle_pump(self.p2, self.btn_p2)) 

 

        self.spin_p2 = QDoubleSpinBox() 

        self.spin_p2.setRange(0.1, 50.0); self.spin_p2.setValue(5.0); self.spin_p2.setSuffix(" L/cykl") 

        self.spin_p2.valueChanged.connect(lambda v: setattr(self.p2, 'wydajnosc', v)) 

 

        lay_pompy.addWidget(QLabel("Pompa P-2:"), 2, 0) 

        lay_pompy.addWidget(self.btn_p2, 2, 1) 

        lay_pompy.addWidget(QLabel("Wydajność:"), 3, 0) 

        lay_pompy.addWidget(self.spin_p2, 3, 1) 

 

        grp_pompy.setLayout(lay_pompy) 

        panel_layout.addWidget(grp_pompy) 

 

        # Zawory 

        grp_zawory = QGroupBox("Hydraulika i Spusty") 

        lay_zawory = QVBoxLayout() 

         

        self.btn_zawor = QPushButton("Zawór V-1 (Z3->Z4): ZAMKNIĘTY") 

        self.btn_zawor.setCheckable(True) 

        self.btn_zawor.setStyleSheet("background-color: #ffcccc;") 

        self.btn_zawor.toggled.connect(self.toggle_zawor) 

        lay_zawory.addWidget(self.btn_zawor) 

 

        self.btn_spust = QPushButton("SPUST Z4 (Trzymaj)") 

        self.btn_spust.setStyleSheet("background-color: orange;") 

        # POPRAWIONE PODPIĘCIE PRZYCISKU (pressed/released) 

        self.btn_spust.pressed.connect(lambda: setattr(self, 'spust_aktywny', True)) 

        self.btn_spust.released.connect(lambda: setattr(self, 'spust_aktywny', False)) 

        self.spust_aktywny = False 

        lay_zawory.addWidget(self.btn_spust) 

         

        grp_zawory.setLayout(lay_zawory) 

        panel_layout.addWidget(grp_zawory) 

 

        # Dolewanie 

        grp_woda = QGroupBox("Dolewanie Ręczne") 

        lay_woda = QGridLayout() 

        for i, z in enumerate(self.zbiorniki): 

            btn = QPushButton(f"{z.nazwa} +100L") 

            btn.clicked.connect(lambda ch, x=z: x.dodaj_ciecz(100)) 

            lay_woda.addWidget(btn, i // 2, i % 2) 

        grp_woda.setLayout(lay_woda) 

        panel_layout.addWidget(grp_woda) 

 

        # Reset 

        btn_reset = QPushButton("ZATWIERDŹ / RESET BŁĘDÓW") 

        btn_reset.setMinimumHeight(40) 

        btn_reset.setStyleSheet("font-weight: bold; font-size: 12px; background-color: #ddd;") 

        btn_reset.clicked.connect(self.reset_alarms) 

        panel_layout.addWidget(btn_reset) 

 

        panel_layout.addStretch() 

        layout.addWidget(panel) 

 

    def setup_logi(self): 

        layout = QVBoxLayout(self.tab_logi) 

        self.tabela_logow = QTableWidget() 

        self.tabela_logow.setColumnCount(3) 

        self.tabela_logow.setHorizontalHeaderLabels(["Czas", "Typ", "Komunikat"]) 

        self.tabela_logow.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 

        layout.addWidget(self.tabela_logow) 

 

    def init_objects(self): 

        # Współrzędne dostosowane tak, by Z3 i Z4 się nie zlewały 

        self.z1 = Zbiornik(50, 100, 100, 200, 1000, "Z1") 

        self.z1.poziom = 200 

         

        self.z2 = Zbiornik(250, 100, 100, 200, 1000, "Z2") 

         

        # Z3 przesunięte wyżej i w prawo 

        self.z3 = Zbiornik(450, 100, 100, 200, 1000, "Z3") 

         

        # Z4 jest niżej, rura wchodzi wyraźnie od góry 

        self.z4 = Zbiornik(350, 450, 400, 100, 2500, "Z4") 

 

        self.p1 = Pompa(200, 250, "P-1") 

        self.p2 = Pompa(400, 250, "P-2") # P-2 wyżej 

         

        self.v1 = Zawor(600, 350, "V-1") 

 

        # R1: Z1 -> Z2 

        r1 = Rura([(100, 300), (100, 350), (200, 350), (200, 250), (250, 250)]) 

         

        # R2: Z2 -> Z3 

        r2 = Rura([(300, 300), (300, 350), (400, 350), (400, 250), (450, 250)]) 

         

        # R3: Z3 -> Z4 (NOWA TRASA - wyraźna separacja) 

        # Wychodzi dołem Z3, idzie w dół, przez zawór, potem w lewo i wchodzi do Z4 od góry 

        r3 = Rura([ 

            (550, 250), # Dół Z3 

            (550, 350), # W dół 

            (600, 350), # Przez zawór (prawo) - małe obejście dla zaworu 

            (650, 350), # Za zaworem 

            (650, 400), # W dół 

            (550, 400), # W lewo nad Z4 

            (550, 450)  # W dół do Z4 

        ]) 

 

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4] 

        self.pompy = [self.p1, self.p2] 

        self.rury = [r1, r2, r3] 

        self.zawory = [self.v1] 

 

    def log_event(self, typ, msg): 

        row = self.tabela_logow.rowCount() 

        self.tabela_logow.insertRow(row) 

         

        czas = datetime.now().strftime("%H:%M:%S") 

        self.tabela_logow.setItem(row, 0, QTableWidgetItem(czas)) 

         

        # Tworzymy item typu i ustawiamy mu kolor TŁA 

        item_typ = QTableWidgetItem(typ) 

        if typ == "ALARM": 

            item_typ.setBackground(QColor(255, 180, 180)) # Jasny czerwony 

        elif typ == "AWARIA": 

            item_typ.setBackground(QColor(255, 0, 0))     # Mocny czerwony 

            item_typ.setForeground(QBrush(Qt.white))      # Biały tekst 
            
        elif typ == "USTERKA": 
        
            item_typ.setBackground(QColor(255, 80, 80))     # Mocny czerwony 
        
            item_typ.setForeground(QBrush(Qt.white))      # Biały tekst             

        elif typ == "SYSTEM": 

            item_typ.setBackground(QColor(255, 255, 150)) # Żółty 

             

        self.tabela_logow.setItem(row, 1, item_typ) 

        self.tabela_logow.setItem(row, 2, QTableWidgetItem(msg)) 

        self.tabela_logow.scrollToBottom() 

 

    def toggle_pump(self, pompa, btn): 

        pompa.aktywna = btn.isChecked() 

        if pompa.aktywna: 

            self.log_event("INFO", f"Uruchomiono pompę {pompa.nazwa}") 

            pompa.licznik_suchobiegu = 0  

        else: 

            self.log_event("INFO", f"Zatrzymano pompę {pompa.nazwa}") 

 

    def toggle_zawor(self, checked): 

        self.v1.otwarty = checked 

        if checked: 

            self.btn_zawor.setText("Zawór V-1: OTWARTY") 

            self.btn_zawor.setStyleSheet("background-color: #ccffcc;")  

            self.log_event("INFO", "Otwarto zawór V-1 (Odpływ Z3)") 

        else: 

            self.btn_zawor.setText("Zawór V-1: ZAMKNIĘTY") 

            self.btn_zawor.setStyleSheet("background-color: #ffcccc;")  

            self.log_event("INFO", "Zamknięto zawór V-1") 

 

    def reset_alarms(self): 

        for el in self.zbiorniki + self.pompy: 

            el.stan_alarmowy = False 

            if isinstance(el, Pompa): 

                el.licznik_suchobiegu = 0  

        self.log_event("INFO", "Zatwierdzono i skasowano błędy.") 

 

    def obsluga_pompy(self, pompa, btn_gui, z_zrodlo, z_cel, rura_idx): 

        if pompa.aktywna: 

            if z_zrodlo.poziom > 0: 

                # Fizyka: używamy pompa.wydajnosc ze spinboxa 

                flow = z_zrodlo.pobierz_ciecz(pompa.wydajnosc) 

                z_cel.dodaj_ciecz(flow) 

                self.rury[rura_idx].czy_plynie = True 

                 

                pompa.stan_alarmowy = False 

                pompa.licznik_suchobiegu = 0 

            else: 

                self.rury[rura_idx].czy_plynie = False 

                if not pompa.stan_alarmowy: 

                    pompa.stan_alarmowy = True 

                    self.log_event("AWARIA", f"Suchobieg pompy {pompa.nazwa}!") 

 

                pompa.licznik_suchobiegu += 1 

                if pompa.licznik_suchobiegu >= 100: # 5 sekund (100 * 50ms) 

                    pompa.aktywna = False 

                    btn_gui.setChecked(False)  

                    self.log_event("USTERKA", f"AUTO-STOP {pompa.nazwa} (Ochrona termiczna)") 

        else: 

            self.rury[rura_idx].czy_plynie = False 

 

    def main_loop(self): 

        # P1 i P2 

        self.obsluga_pompy(self.p1, self.btn_p1, self.z1, self.z2, 0) 

        self.obsluga_pompy(self.p2, self.btn_p2, self.z2, self.z3, 1) 

 

        # Grawitacja Z3 -> Z4 (przez V1) 

        if self.v1.otwarty and self.z3.poziom > 0: 

            flow = self.z3.pobierz_ciecz(3.0) 

            self.z4.dodaj_ciecz(flow) 

            self.rury[2].czy_plynie = True 

        else: 

            self.rury[2].czy_plynie = False 

 

        # Spust Z4 

        if self.spust_aktywny and self.z4.poziom > 0: 

            self.z4.pobierz_ciecz(15.0) 

 

        # Alarmy przepełnienia 

        for z in self.zbiorniki: 

            if z.poziom >= z.max_poj: 

                if not z.stan_alarmowy: 

                    z.stan_alarmowy = True 

                    self.log_event("ALARM", f"Przepełnienie {z.nazwa}!") 

 

        # Animacje 

        for el in self.zbiorniki + self.pompy: 

            el.aktualizuj_animacje() 

 

        self.ekran.update() 

 

if __name__ == "__main__": 

    app = QApplication(sys.argv) 

    app.setStyle("Fusion") 

    window = ScadaApp() 

    window.show() 

    sys.exit(app.exec_()) 