#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GESTIONE ORDINI RISTORANTE - VERSIONE COMPLETA STABILE
Tutte le funzionalità: tavoli, asporto, categorie, prodotti, riepilogo, pagamento

Esegui: python main_mobile.py
"""

import sys
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
import sqlite3

print("🍽️  Avvio...")
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTableWidget, QTableWidgetItem, QScrollArea,
        QMessageBox, QSpinBox, QLineEdit, QGridLayout, QDialog,
        QDialogButtonBox, QFrame, QTextEdit, QTabWidget, QListWidget,
        QListWidgetItem, QComboBox, QDoubleSpinBox, QInputDialog, QFileDialog,
        QMenu
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont, QColor, QCursor
    print("✓ PyQt5 caricato")
except ImportError as e:
    print(f"✗ Errore PyQt5: {e}")
    print("✗ Installa PyQt5: pip install PyQt5")
    sys.exit(1)

# ============================================================================
# MODELLI
# ============================================================================

class StatoOrdine(Enum):
    IN_SOSPESO = "In sospeso"
    IN_PREPARAZIONE = "In preparazione"
    SERVITO = "Servito"
    PAGATO = "Pagato"

class Prodotto:
    def __init__(self, id_prodotto: int, nome: str, categoria: str, prezzo: float):
        self.id_prodotto = id_prodotto
        self.nome = nome
        self.categoria = categoria
        self.prezzo = prezzo

class RigaOrdine:
    def __init__(self, prodotto: Prodotto, quantita: int = 1):
        self.prodotto = prodotto
        self.quantita = quantita
        self.nota_cucina = ""  # Nota specifica per questa riga
        self.ingredienti = ""  # Ingredienti specifici per questa riga
        self.in_attesa = False  # Se il prodotto è in attesa
        self.motivo_rifiuto = ""  # Motivo se vuoto (Annullato/Sostituzione)
    
    def get_subtotale(self) -> float:
        return self.prodotto.prezzo * self.quantita

class Ordine:
    _contatore_id = 0
    
    def __init__(self, id_tavolo: int, numero_persone: int = 1):
        Ordine._contatore_id += 1
        self.id_ordine = Ordine._contatore_id
        self.id_tavolo = id_tavolo
        self.numero_persone = numero_persone
        self.righe_ordinare: List[RigaOrdine] = []  # Prodotti da ordinare
        self.righe_ordinato: List[RigaOrdine] = []  # Prodotti già ordinati
        self.stato = StatoOrdine.IN_SOSPESO
        self.data_creazione = datetime.now()
    
    def aggiungi_prodotto(self, prodotto: Prodotto, quantita: int = 1):
        # Crea sempre una nuova riga in ordinare
        self.righe_ordinare.append(RigaOrdine(prodotto, quantita))
    
    def rimuovi_prodotto(self, indice_riga: int) -> bool:
        if 0 <= indice_riga < len(self.righe_ordinare):
            self.righe_ordinare.pop(indice_riga)
            return True
        return False
    
    def modifica_quantita(self, indice_riga: int, nuova_quantita: int) -> bool:
        if 0 <= indice_riga < len(self.righe_ordinare):
            if nuova_quantita > 0:
                self.righe_ordinare[indice_riga].quantita = nuova_quantita
            else:
                self.righe_ordinare.pop(indice_riga)
            return True
        return False
    
    def get_totale(self) -> float:
        totale = 0
        for r in self.righe_ordinare:
            totale += r.get_subtotale()
        for r in self.righe_ordinato:
            totale += r.get_subtotale()
        return totale
    
    def get_numero_articoli(self) -> int:
        return sum(riga.quantita for riga in self.righe_ordinare) + sum(riga.quantita for riga in self.righe_ordinato)
    
    def cambia_stato(self, nuovo_stato: StatoOrdine):
        self.stato = nuovo_stato
    
    def is_vuoto(self) -> bool:
        return len(self.righe_ordinare) == 0 and len(self.righe_ordinato) == 0

class Tavolo:
    def __init__(self, numero_tavolo: int):
        self.numero_tavolo = numero_tavolo
        self.ordine_attivo: Optional[Ordine] = None
        self.occupato = False
        self.in_attesa = False  # Tavolo in attesa
    
    def crea_nuovo_ordine(self, numero_persone: int = 1) -> Ordine:
        self.ordine_attivo = Ordine(self.numero_tavolo, numero_persone)
        self.occupato = True
        return self.ordine_attivo
    
    def chiudi_ordine(self) -> Optional[Ordine]:
        ordine = self.ordine_attivo
        self.ordine_attivo = None
        self.occupato = False
        return ordine

# ============================================================================
# DATABASE
# ============================================================================

class DatabaseOrdini:
    def __init__(self, nome_db: str = "ristorante_ordini.db"):
        self.nome_db = nome_db
        self.connessione = sqlite3.connect(nome_db)
        self.connessione.row_factory = sqlite3.Row
        self._crea_tabelle()
        self._carica_menu()
    
    def _crea_tabelle(self):
        cursor = self.connessione.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS categorie (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS prodotti (
            id_prodotto INTEGER PRIMARY KEY, nome TEXT, categoria TEXT, prezzo REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ordini (
            id_ordine INTEGER PRIMARY KEY AUTOINCREMENT, id_tavolo INTEGER, numero_persone INTEGER,
            stato TEXT, totale REAL, data_creazione TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS righe_ordini (
            id_riga INTEGER PRIMARY KEY AUTOINCREMENT, id_ordine INTEGER, id_prodotto INTEGER,
            quantita INTEGER, prezzo_unitario REAL)''')
        self.connessione.commit()
    
    def _carica_menu(self):
        cursor = self.connessione.cursor()
        cursor.execute('SELECT COUNT(*) FROM prodotti')
        if cursor.fetchone()[0] == 0:
            # Inserisci categorie
            categorie = ["Caffetteria", "Bevande", "Dolci", "Panini", "Pizze", "Primi piatti", "Cocktails", "Birre"]
            for cat in categorie:
                try:
                    cursor.execute('INSERT INTO categorie (nome) VALUES (?)', (cat,))
                except:
                    pass  # Categoria già esiste
            
            menu = [
                # Caffetteria
                (1, "Caffè espresso", "Caffetteria", 1.00),
                (2, "Cappuccino", "Caffetteria", 1.50),
                (3, "Latte", "Caffetteria", 1.80),
                (4, "Macchiato", "Caffetteria", 1.20),
                (5, "Lungo", "Caffetteria", 1.00),
                # Bevande
                (11, "Acqua naturale", "Bevande", 1.50),
                (12, "Acqua frizzante", "Bevande", 1.50),
                (13, "Coca Cola", "Bevande", 2.00),
                (14, "Sprite", "Bevande", 2.00),
                (15, "Aranciata", "Bevande", 2.00),
                (16, "Succo d'arancia", "Bevande", 2.50),
                # Dolci
                (21, "Tiramisu", "Dolci", 5.00),
                (22, "Panna cotta", "Dolci", 4.50),
                (23, "Gelato", "Dolci", 3.50),
                (24, "Cheesecake", "Dolci", 5.50),
                (25, "Pannacotta al cioccolato", "Dolci", 4.50),
                # Panini
                (31, "Panino prosciutto e mozzarella", "Panini", 6.00),
                (32, "Panino mortadella", "Panini", 5.50),
                (33, "Panino porchetta", "Panini", 7.00),
                (34, "Panino pollo", "Panini", 6.50),
                (35, "Panino tonno", "Panini", 6.00),
                # Pizze
                (41, "Margherita", "Pizze", 8.00),
                (42, "Quattro formaggi", "Pizze", 9.50),
                (43, "Diavola", "Pizze", 9.00),
                (44, "Carbonara", "Pizze", 10.00),
                (45, "Ortolana", "Pizze", 8.50),
                (46, "Hawaiana", "Pizze", 9.50),
                # Primi piatti
                (51, "Spaghetti Carbonara", "Primi piatti", 9.00),
                (52, "Risotto ai funghi", "Primi piatti", 10.00),
                (53, "Penne Arrabbiata", "Primi piatti", 8.50),
                (54, "Lasagna", "Primi piatti", 10.50),
                (55, "Fettuccine Alfredo", "Primi piatti", 10.00),
                (56, "Ravioli ricotta e spinaci", "Primi piatti", 9.50),
                # Cocktails
                (61, "Mojito", "Cocktails", 7.00),
                (62, "Margarita", "Cocktails", 7.50),
                (63, "Piña Colada", "Cocktails", 8.00),
                (64, "Daiquiri", "Cocktails", 7.50),
                (65, "Cosmopolitan", "Cocktails", 8.00),
                (66, "Long Island", "Cocktails", 9.00),
                # Birre
                (71, "Birra bionda", "Birre", 3.50),
                (72, "Birra rossa", "Birre", 4.00),
                (73, "Birra scura", "Birre", 4.50),
                (74, "Birra artigianale IPA", "Birre", 5.00),
                (75, "Birra analcolica", "Birre", 2.50),
            ]
            cursor.executemany('INSERT INTO prodotti VALUES (?, ?, ?, ?)', menu)
            self.connessione.commit()
    
    def get_prodotti_per_categoria(self, categoria: str) -> List[Prodotto]:
        cursor = self.connessione.cursor()
        cursor.execute('SELECT * FROM prodotti WHERE categoria = ? ORDER BY nome', (categoria,))
        return [Prodotto(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]
    
    def get_categorie(self) -> List[str]:
        cursor = self.connessione.cursor()
        cursor.execute('SELECT nome FROM categorie ORDER BY nome')
        return [row[0] for row in cursor.fetchall()]
    
    def cerca_prodotti(self, termine: str) -> List[Prodotto]:
        cursor = self.connessione.cursor()
        cursor.execute('SELECT * FROM prodotti WHERE nome LIKE ? ORDER BY nome', (f"%{termine}%",))
        return [Prodotto(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]
    
    def salva_ordine(self, ordine: Ordine) -> bool:
        try:
            cursor = self.connessione.cursor()
            cursor.execute(
                'INSERT INTO ordini (id_tavolo, numero_persone, stato, totale, data_creazione) VALUES (?, ?, ?, ?, ?)',
                (ordine.id_tavolo, ordine.numero_persone, ordine.stato.value, ordine.get_totale(), ordine.data_creazione.isoformat())
            )
            id_ordine = cursor.lastrowid
            for riga in ordine.righe:
                cursor.execute(
                    'INSERT INTO righe_ordini (id_ordine, id_prodotto, quantita, prezzo_unitario) VALUES (?, ?, ?, ?)',
                    (id_ordine, riga.prodotto.id_prodotto, riga.quantita, riga.prodotto.prezzo)
                )
            self.connessione.commit()
            return True
        except Exception as e:
            print(f"Errore: {e}")
            return False
    
    def get_ordini_tavolo(self, numero_tavolo: int) -> list:
        """Ritorna gli ordini salvati per un tavolo (per ora lista vuota)"""
        # TODO: Implementare il caricamento degli ordini dal DB
        return []
    
    def add_product(self, nome: str, categoria: str, prezzo: float):
        """Aggiunge un nuovo prodotto"""
        cursor = self.connessione.cursor()
        cursor.execute('INSERT INTO prodotti (nome, categoria, prezzo) VALUES (?, ?, ?)', 
                      (nome, categoria, prezzo))
        self.connessione.commit()
    
    def delete_product(self, id_prodotto: int):
        """Elimina un prodotto"""
        cursor = self.connessione.cursor()
        cursor.execute('DELETE FROM prodotti WHERE id_prodotto = ?', (id_prodotto,))
        self.connessione.commit()
    
    def add_or_update_product(self, id_prod: int, nome: str, categoria: str, prezzo: float):
        """Aggiunge o aggiorna un prodotto (per import CSV)"""
        cursor = self.connessione.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO prodotti (id_prodotto, nome, categoria, prezzo) VALUES (?, ?, ?, ?)',
            (id_prod, nome, categoria, prezzo)
        )
        self.connessione.commit()
    
    def get_all_products(self):
        """Ritorna tutti i prodotti"""
        cursor = self.connessione.cursor()
        cursor.execute('SELECT id_prodotto, nome, categoria, prezzo FROM prodotti ORDER BY categoria, nome')
        rows = cursor.fetchall()
        return [Prodotto(row[0], row[1], row[2], row[3]) for row in rows]
    
    def add_category(self, nome_categoria: str):
        """Aggiunge una nuova categoria"""
        try:
            cursor = self.connessione.cursor()
            cursor.execute('INSERT INTO categorie (nome) VALUES (?)', (nome_categoria,))
            self.connessione.commit()
        except:
            pass  # Categoria già esiste
    
    def delete_category(self, categoria: str):
        """Elimina una categoria e tutti i suoi prodotti"""
        cursor = self.connessione.cursor()
        cursor.execute('DELETE FROM prodotti WHERE categoria = ?', (categoria,))
        self.connessione.commit()
    
    def chiudi(self):
        """Chiude la connessione al database"""
        self.connessione.close()

# ============================================================================
# GESTIONE
# ============================================================================

class GestioneOrdini:
    def __init__(self, numero_tavoli: int = 30):
        self.tavoli: Dict[int, Tavolo] = {i: Tavolo(i) for i in range(0, numero_tavoli + 1)}
        self.db = DatabaseOrdini()
    
    def get_tavolo(self, numero_tavolo: int) -> Optional[Tavolo]:
        return self.tavoli.get(numero_tavolo)
    
    def get_tutti_tavoli(self) -> List[Tavolo]:
        return sorted([t for t in self.tavoli.values() if t.numero_tavolo > 0], key=lambda t: t.numero_tavolo)
    
    def crea_ordine(self, numero_tavolo: int, numero_persone: int = 1) -> Optional[Ordine]:
        tavolo = self.get_tavolo(numero_tavolo)
        if tavolo and not tavolo.occupato:
            return tavolo.crea_nuovo_ordine(numero_persone)
        return None
    
    def libera_tavolo(self, numero_tavolo: int) -> Optional[Ordine]:
        tavolo = self.get_tavolo(numero_tavolo)
        if tavolo:
            ordine = tavolo.chiudi_ordine()
            if ordine and not ordine.is_vuoto():
                self.db.salva_ordine(ordine)
            return ordine
        return None
    
    def get_ordine_attivo(self, numero_tavolo: int) -> Optional[Ordine]:
        tavolo = self.get_tavolo(numero_tavolo)
        return tavolo.ordine_attivo if tavolo else None
    
    def aggiungi_al_ordine(self, numero_tavolo: int, prodotto: Prodotto, quantita: int = 1) -> bool:
        ordine = self.get_ordine_attivo(numero_tavolo)
        if ordine:
            ordine.aggiungi_prodotto(prodotto, quantita)
            return True
        return False
    
    def get_categoria_prodotti(self, categoria: str) -> List[Prodotto]:
        return self.db.get_prodotti_per_categoria(categoria)
    
    def get_tutti_prodotti(self) -> List[Prodotto]:
        """Ritorna tutti i prodotti"""
        return self.db.get_all_products()
    
    def get_categorie(self) -> List[str]:
        return self.db.get_categorie()
    
    def cerca_prodotti(self, termine: str) -> List[Prodotto]:
        return self.db.cerca_prodotti(termine)
    
    def cambia_stato_ordine(self, numero_tavolo: int, nuovo_stato: StatoOrdine) -> bool:
        ordine = self.get_ordine_attivo(numero_tavolo)
        if ordine:
            ordine.cambia_stato(nuovo_stato)
            self.db.salva_ordine(ordine)
            return True
        return False

# ============================================================================
# CARD PRODOTTO
# ============================================================================

class CardProdotto(QFrame):
    clicked = pyqtSignal(object)
    
    def __init__(self, prodotto: Prodotto, quantita: int = 0):
        super().__init__()
        self.prodotto = prodotto
        self.quantita = quantita
        
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(0)
        
        # BIANCO sempre
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0px;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)
        
        # Nome in alto a sinistra
        nome = QLabel(prodotto.nome)
        nome.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: bold;")
        nome.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        nome.setWordWrap(True)
        layout.addWidget(nome)
        
        layout.addStretch()
        
        # Sezione basso: quantità a sinistra, prezzo a destra
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        
        # Quantità a sinistra (se aggiunto)
        if quantita > 0:
            qtd = QLabel(f"x{quantita}")
            qtd.setStyleSheet("color: #3498db; font-size: 12px; font-weight: bold;")
            qtd.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
            bottom_layout.addWidget(qtd)
        
        bottom_layout.addStretch()
        
        # Prezzo a destra
        prezzo = QLabel(f"€{prodotto.prezzo:.2f}")
        prezzo.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold;")
        prezzo.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        bottom_layout.addWidget(prezzo)
        
        layout.addLayout(bottom_layout)
        
        self.setMinimumSize(110, 110)
        self.setMaximumSize(130, 130)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.prodotto)

# ============================================================================
# DIALOGS
# ============================================================================

class DialogPersone(QDialog):
    def __init__(self, numero_tavolo: int, parent=None):
        super().__init__(parent)
        self.numero_tavolo = numero_tavolo
        self.numero_persone = 1
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(f"Tavolo {self.numero_tavolo}")
        self.setGeometry(0, 0, 600, 300)
        self.setModal(True)
        self.setStyleSheet("background-color: #f5f5f5;")
        
        # Centra la dialog sullo schermo
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 600) // 2
        y = (screen.height() - 300) // 2
        self.move(x, y)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titolo
        label = QLabel(f"Tavolo {self.numero_tavolo}")
        label.setStyleSheet("font-size: 28px; font-weight: bold; color: #34495e;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Domanda
        domanda = QLabel("Quante persone?")
        domanda.setStyleSheet("font-size: 20px; color: #2c3e50;")
        domanda.setAlignment(Qt.AlignCenter)
        layout.addWidget(domanda)
        
        # Tastiera con bottoni 1-10
        tastiera_layout = QGridLayout()
        tastiera_layout.setSpacing(8)
        
        for i in range(1, 11):
            btn = QPushButton(str(i))
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #2980b9; }
                QPushButton:pressed { background-color: #1f618d; }
            """)
            btn.clicked.connect(lambda checked, num=i: self.seleziona_e_chiudi(num))
            row = (i - 1) // 5
            col = (i - 1) % 5
            tastiera_layout.addWidget(btn, row, col)
        
        layout.addLayout(tastiera_layout)
        self.setLayout(layout)
    
    def seleziona_e_chiudi(self, numero: int):
        """Seleziona il numero e chiudi la dialog"""
        self.numero_persone = numero
        self.accept()
    
    def get_numero_persone(self):
        return self.numero_persone

# ============================================================================
# INTERFACCIA PRINCIPALE
# ============================================================================

class InterfacciaMobile(QMainWindow):
    def __init__(self):
        super().__init__()
        self.gestione = GestioneOrdini(numero_tavoli=30)
        self.tavolo_attuale = 0
        self.categoria_attuale = ""
        
        self.setWindowTitle("Gestione Ordini")
        self.setGeometry(0, 0, 1080, 1920)
        self.configura_stili()
        self.crea_schermata_principale()
    
    def configura_stili(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QPushButton { background-color: #3498db; color: white; border: none; border-radius: 8px; padding: 12px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
            QLineEdit { font-size: 14px; padding: 10px; border: 2px solid #bdc3c7; border-radius: 8px; }
        """)
    
    def crea_schermata_principale(self):
        """Schermata con tavoli e bottone asporto"""
        widget = QWidget()
        self.setCentralWidget(widget)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # HEADER con ASPORTO, TAVOLI e ADMIN
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(20)
        
        btn_asporto = QPushButton("🛒 ASPORTO")
        btn_asporto.setMinimumHeight(50)
        btn_asporto.setMinimumWidth(140)
        btn_asporto.setStyleSheet("background-color: #e74c3c; font-size: 14px;")
        btn_asporto.clicked.connect(self.ordina_asporto)
        header_layout.addWidget(btn_asporto)
        
        title = QLabel("🍽️ TAVOLI")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title, 1)
        
        btn_admin = QPushButton("⚙️ Admin")
        btn_admin.setMinimumHeight(50)
        btn_admin.setMinimumWidth(140)
        btn_admin.setStyleSheet("background-color: #9b59b6; font-size: 14px;")
        btn_admin.clicked.connect(self.mostra_pannello_admin)
        header_layout.addWidget(btn_admin)
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("background-color: #34495e;")
        header_widget.setFixedHeight(80)
        layout.addWidget(header_widget)
        
        # SCROLL TAVOLI
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        
        widget_tavoli = QWidget()
        widget_tavoli.setStyleSheet("background-color: white;")
        grid_tavoli = QGridLayout(widget_tavoli)
        grid_tavoli.setSpacing(12)
        grid_tavoli.setContentsMargins(15, 15, 15, 15)
        
        self.pulsanti_tavoli = {}
        for i, tavolo in enumerate(self.gestione.get_tutti_tavoli()):
            # Crea widget tavolo con layout
            tavolo_widget = QWidget()
            tavolo_layout = QVBoxLayout(tavolo_widget)
            tavolo_layout.setContentsMargins(0, 0, 0, 0)
            tavolo_layout.setSpacing(0)
            
            # Bottone numero tavolo (top)
            btn = QPushButton(f"Tavolo {tavolo.numero_tavolo}")
            btn.setMinimumHeight(100)
            btn.setFont(QFont("Arial", 14, QFont.Bold))
            
            # Determina colore based on stato
            if tavolo.in_attesa:
                colore = "#e74c3c"  # Rosso se in attesa
                btn.setStyleSheet("background-color: #e74c3c; color: white; border: none; border-radius: 8px 8px 0px 0px; padding: 12px;")
            elif tavolo.occupato:
                colore = "#f39c12"  # Arancione se occupato
                btn.setStyleSheet("background-color: #f39c12; color: white; border: none; border-radius: 8px 8px 0px 0px; padding: 12px;")
            else:
                colore = "#3498db"  # Blu se libero
                btn.setStyleSheet("background-color: #3498db; color: white; border: none; border-radius: 8px 8px 0px 0px; padding: 12px;")
            
            btn.clicked.connect(lambda checked, num=tavolo.numero_tavolo: self.clicca_tavolo(num))
            tavolo_layout.addWidget(btn)
            
            # Info in basso (persone sinistra, prezzo destra)
            info_widget = QWidget()
            info_layout = QHBoxLayout(info_widget)
            info_layout.setContentsMargins(8, 5, 8, 5)
            info_layout.setSpacing(0)
            
            if tavolo.in_attesa:
                info_widget.setStyleSheet("background-color: #e74c3c; border-radius: 0px 0px 8px 8px;")
                
                if tavolo.ordine_attivo:
                    persone = QLabel(str(tavolo.ordine_attivo.numero_persone))
                    persone.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                    info_layout.addWidget(persone)
                    
                    info_layout.addStretch()
                    
                    prezzo = QLabel(f"€{tavolo.ordine_attivo.get_totale():.2f}")
                    prezzo.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                    info_layout.addWidget(prezzo)
            elif tavolo.occupato and tavolo.ordine_attivo:
                info_widget.setStyleSheet("background-color: #f39c12; border-radius: 0px 0px 8px 8px;")
                
                persone = QLabel(str(tavolo.ordine_attivo.numero_persone))
                persone.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                info_layout.addWidget(persone)
                
                info_layout.addStretch()
                
                prezzo = QLabel(f"€{tavolo.ordine_attivo.get_totale():.2f}")
                prezzo.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                info_layout.addWidget(prezzo)
            else:
                info_widget.setStyleSheet("background-color: #3498db; border-radius: 0px 0px 8px 8px;")
                info_layout.addStretch()
            
            info_widget.setLayout(info_layout)
            tavolo_layout.addWidget(info_widget)
            
            tavolo_widget.setLayout(tavolo_layout)
            tavolo_widget.setMinimumHeight(120)
            tavolo_widget.setMinimumWidth(120)
            
            self.pulsanti_tavoli[tavolo.numero_tavolo] = btn
            row = i // 3
            col = i % 3
            grid_tavoli.addWidget(tavolo_widget, row, col)
        
        scroll.setWidget(widget_tavoli)
        layout.addWidget(scroll)
    
    def clicca_tavolo(self, numero_tavolo: int):
        tavolo = self.gestione.get_tavolo(numero_tavolo)
        
        if tavolo.occupato:
            # Se ha già ordinato, vai direttamente alla schermata ordine con TAB Ordinato
            self.mostra_schermata_ordine(numero_tavolo, tab_ordinato=True)
        else:
            # Crea overlay per domanda persone
            self.mostra_overlay_persone(numero_tavolo)
    
    def ordina_asporto(self):
        """ASPORTO - Direttamente a ordinare senza popup"""
        self.gestione.crea_ordine(0, 1)
        self.mostra_schermata_ordine(0)
    
    def mostra_schermata_riepilogo_readonly(self, numero_tavolo: int):
        """Mostra ordine già preso (READ-ONLY) con bottone Ordina"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        if not ordine or ordine.is_vuoto():
            return
        
        widget = QWidget()
        self.setCentralWidget(widget)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # HEADER con ORDINATO e bottone ORDINA
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(15)
        
        btn_back = QPushButton("←")
        btn_back.setStyleSheet("background-color: #95a5a6; min-width: 35px; min-height: 35px; border-radius: 6px; font-size: 14px;")
        btn_back.clicked.connect(self.torna_a_tavoli)
        header_layout.addWidget(btn_back)
        
        header = QLabel("✓ ORDINATO")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header, 1)
        
        btn_ordina = QPushButton("+ Ordina")
        btn_ordina.setStyleSheet("background-color: #27ae60; min-width: 100px; min-height: 35px; border-radius: 6px; font-size: 14px;")
        btn_ordina.clicked.connect(lambda: self.mostra_schermata_ordine(numero_tavolo))
        header_layout.addWidget(btn_ordina)
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("background-color: #34495e;")
        header_widget.setFixedHeight(60)
        layout.addWidget(header_widget)
        
        # DETTAGLI ORDINE
        details_layout = QHBoxLayout()
        details_layout.setContentsMargins(20, 15, 20, 15)
        details_layout.setSpacing(20)
        
        tavolo_info = QLabel(f"Tavolo: {numero_tavolo}\nPersone: {ordine.numero_persone}")
        tavolo_info.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #ecf0f1; border-radius: 8px;")
        details_layout.addWidget(tavolo_info)
        
        details_layout.addStretch()
        
        layout.addLayout(details_layout)
        
        # LISTA PRODOTTI (READ-ONLY, SENZA +/-)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        table_layout = QVBoxLayout(container)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(1)
        
        for riga in ordine.righe:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(10, 3, 10, 3)
            row_layout.setSpacing(15)
            
            # Nome prodotto
            nome_label = QLabel(riga.prodotto.nome)
            nome_label.setStyleSheet("""
                QLabel {
                    background-color: #34495e;
                    color: white;
                    border: 2px solid #2c3e50;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
            nome_label.setMinimumHeight(35)
            row_layout.addWidget(nome_label, 1)
            
            # Quantità
            qtd_label = QLabel(f"x{riga.quantita}")
            qtd_label.setStyleSheet("font-size: 16px; font-weight: bold; min-width: 50px; text-align: center;")
            row_layout.addWidget(qtd_label)
            
            # Prezzo unitario
            prezzo_label = QLabel(f"€{riga.prodotto.prezzo:.2f}")
            prezzo_label.setStyleSheet("font-size: 14px; font-weight: bold; min-width: 80px; text-align: center;")
            row_layout.addWidget(prezzo_label)
            
            # Subtotale
            subtot_label = QLabel(f"€{riga.get_subtotale():.2f}")
            subtot_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; min-width: 90px; text-align: center;")
            row_layout.addWidget(subtot_label)
            
            row_widget.setLayout(row_layout)
            row_widget.setStyleSheet("background-color: white; border: 1px solid #ecf0f1; border-radius: 8px;")
            
            table_layout.addWidget(row_widget)
        
        container.setLayout(table_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        
        # TOTALE
        totale_label = QLabel(f"TOTALE: €{ordine.get_totale():.2f}")
        totale_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; padding: 20px; background-color: #27ae60;")
        totale_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(totale_label)
        
        # PULSANTI INFERIORI (PAGA E CHIUDI)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(15, 15, 15, 15)
        btn_layout.setSpacing(15)
        
        btn_paga = QPushButton("💳 Paga")
        btn_paga.setMinimumHeight(60)
        btn_paga.setStyleSheet("background-color: #f39c12; font-size: 16px;")
        btn_paga.clicked.connect(lambda: self.paga_ordine(numero_tavolo))
        btn_layout.addWidget(btn_paga)
        
        btn_chiudi = QPushButton("🔒 Chiudi Tavolo")
        btn_chiudi.setMinimumHeight(60)
        btn_chiudi.setStyleSheet("background-color: #e74c3c; font-size: 16px;")
        btn_chiudi.clicked.connect(lambda: self.chiudi_tavolo(numero_tavolo))
        btn_layout.addWidget(btn_chiudi)
        
        layout.addLayout(btn_layout)
    
    def mostra_overlay_persone(self, numero_tavolo: int):
        """Mostra overlay per selezionare numero persone (no finestra dialog)"""
        # Crea widget overlay (sfondo semi-trasparente)
        self.overlay = QWidget(self)
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        
        # Crea il pannello centrale CENTRATO
        screen_width = self.width()
        screen_height = self.height()
        panel_width = 700
        panel_height = 400
        x = (screen_width - panel_width) // 2
        y = (screen_height - panel_height) // 2
        
        pannello = QWidget(self.overlay)
        pannello.setGeometry(x, y, panel_width, panel_height)
        pannello.setStyleSheet("background-color: #f5f5f5; border-radius: 15px;")
        
        layout = QVBoxLayout(pannello)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Titolo
        titolo = QLabel(f"Tavolo {numero_tavolo}")
        titolo.setStyleSheet("font-size: 32px; font-weight: bold; color: #34495e;")
        titolo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titolo)
        
        # Domanda
        domanda = QLabel("Quante persone?")
        domanda.setStyleSheet("font-size: 22px; color: #2c3e50;")
        domanda.setAlignment(Qt.AlignCenter)
        layout.addWidget(domanda)
        
        # Tastiera 1-10
        tastiera_layout = QGridLayout()
        tastiera_layout.setSpacing(10)
        
        for i in range(1, 11):
            btn = QPushButton(str(i))
            btn.setMinimumHeight(70)
            btn.setMinimumWidth(70)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                    border: none;
                    border-radius: 10px;
                }
                QPushButton:hover { background-color: #2980b9; }
                QPushButton:pressed { background-color: #1f618d; }
            """)
            btn.clicked.connect(lambda checked, num=i, t=numero_tavolo: self.conferma_persone(num, t))
            row = (i - 1) // 5
            col = (i - 1) % 5
            tastiera_layout.addWidget(btn, row, col)
        
        layout.addLayout(tastiera_layout)
        layout.addStretch()
        
        pannello.setLayout(layout)
        
        # Click fuori chiude
        self.overlay.mousePressEvent = lambda event: self.chiudi_overlay()
        
        # Impedisci che il click sul pannello chiuda l'overlay
        pannello.mousePressEvent = lambda event: None
        
        self.overlay.show()
    
    def conferma_persone(self, numero_persone: int, numero_tavolo: int):
        """Conferma persone e vai a ordinare"""
        self.chiudi_overlay()
        self.gestione.crea_ordine(numero_tavolo, numero_persone)
        self.aggiorna_colori_tavoli()
        self.mostra_schermata_ordine(numero_tavolo)
    
    def chiudi_overlay(self):
        """Chiudi l'overlay"""
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.deleteLater()
            self.overlay = None
    
    def chiudi_tavolo(self, numero_tavolo: int):
        """Chiudi il tavolo e libera"""
        self.gestione.libera_tavolo(numero_tavolo)
        self.aggiorna_colori_tavoli()
        self.torna_a_tavoli()
    
    def mostra_pannello_admin(self):
        """Mostra pannello amministrazione prodotti"""
        widget = QWidget()
        self.setCentralWidget(widget)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # HEADER
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(15)
        
        btn_back = QPushButton("←")
        btn_back.setStyleSheet("background-color: #95a5a6; min-width: 35px; min-height: 35px; border-radius: 6px; font-size: 14px;")
        btn_back.clicked.connect(self.torna_a_tavoli)
        header_layout.addWidget(btn_back)
        
        header = QLabel("⚙️ AMMINISTRAZIONE")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header, 1)
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("background-color: #34495e;")
        header_widget.setFixedHeight(60)
        layout.addWidget(header_widget)
        
        # CONTENUTO PRINCIPALE (Tabs)
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #bdc3c7; }
            QTabBar::tab { background-color: #ecf0f1; padding: 8px 20px; }
            QTabBar::tab:selected { background-color: #3498db; color: white; }
        """)
        
        # TAB 1: Gestione Prodotti
        tab_prodotti = self.crea_tab_prodotti()
        tabs.addTab(tab_prodotti, "📦 Prodotti")
        
        # TAB 2: Gestione Categorie
        tab_categorie = self.crea_tab_categorie()
        tabs.addTab(tab_categorie, "📂 Categorie")
        
        # TAB 3: Import/Export CSV
        tab_csv = self.crea_tab_csv()
        tabs.addTab(tab_csv, "📄 CSV")
        
        layout.addWidget(tabs)
    
    def crea_tab_prodotti(self):
        """Tab per gestire prodotti"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabella prodotti
        self.tabella_prodotti = QTableWidget()
        self.tabella_prodotti.setColumnCount(5)
        self.tabella_prodotti.setHorizontalHeaderLabels(["ID", "Nome", "Categoria", "Prezzo", "Azioni"])
        self.tabella_prodotti.setColumnWidth(0, 50)
        self.tabella_prodotti.setColumnWidth(1, 150)
        self.tabella_prodotti.setColumnWidth(2, 120)
        self.tabella_prodotti.setColumnWidth(3, 100)
        self.tabella_prodotti.setColumnWidth(4, 100)
        
        # Popola la tabella
        self.aggiorna_tabella_prodotti()
        
        layout.addWidget(self.tabella_prodotti)
        
        # Pulsanti aggiungi/salva
        btn_layout = QHBoxLayout()
        
        btn_nuovo = QPushButton("➕ Nuovo Prodotto")
        btn_nuovo.setMinimumHeight(40)
        btn_nuovo.setStyleSheet("background-color: #27ae60; font-size: 14px;")
        btn_nuovo.clicked.connect(self.dialogo_nuovo_prodotto)
        btn_layout.addWidget(btn_nuovo)
        
        btn_salva = QPushButton("💾 Salva")
        btn_salva.setMinimumHeight(40)
        btn_salva.setStyleSheet("background-color: #3498db; font-size: 14px;")
        btn_salva.clicked.connect(self.salva_prodotti)
        btn_layout.addWidget(btn_salva)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def crea_tab_categorie(self):
        """Tab per gestire categorie"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Gestione Categorie")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        # Lista categorie
        self.lista_categorie = QListWidget()
        categorie = self.gestione.get_categorie()
        for cat in categorie:
            self.lista_categorie.addItem(cat)
        
        layout.addWidget(self.lista_categorie)
        
        # Pulsanti
        btn_layout = QHBoxLayout()
        
        btn_aggiungi = QPushButton("➕ Nuova Categoria")
        btn_aggiungi.setMinimumHeight(40)
        btn_aggiungi.setStyleSheet("background-color: #27ae60; font-size: 14px;")
        btn_aggiungi.clicked.connect(self.dialogo_nuova_categoria)
        btn_layout.addWidget(btn_aggiungi)
        
        btn_elimina = QPushButton("🗑️ Elimina")
        btn_elimina.setMinimumHeight(40)
        btn_elimina.setStyleSheet("background-color: #e74c3c; font-size: 14px;")
        btn_elimina.clicked.connect(self.elimina_categoria)
        btn_layout.addWidget(btn_elimina)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def crea_tab_csv(self):
        """Tab per import/export CSV"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        label = QLabel("Import/Export CSV")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        info = QLabel(
            "Esporta il menu in CSV per modificarlo facilmente in Excel.\n"
            "Importa da CSV per aggiornare i prodotti.\n\n"
            "Formato CSV:\nid,nome,categoria,prezzo"
        )
        info.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(info)
        
        layout.addSpacing(20)
        
        # Pulsanti
        btn_layout = QVBoxLayout()
        
        btn_export = QPushButton("📥 Esporta Menu (CSV)")
        btn_export.setMinimumHeight(50)
        btn_export.setStyleSheet("background-color: #3498db; font-size: 14px;")
        btn_export.clicked.connect(self.esporta_csv)
        btn_layout.addWidget(btn_export)
        
        btn_import = QPushButton("📤 Importa Menu (CSV)")
        btn_import.setMinimumHeight(50)
        btn_import.setStyleSheet("background-color: #27ae60; font-size: 14px;")
        btn_import.clicked.connect(self.importa_csv)
        btn_layout.addWidget(btn_import)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return widget
    
    def aggiorna_tabella_prodotti(self):
        """Popola la tabella con i prodotti"""
        self.tabella_prodotti.setRowCount(0)
        
        db = DatabaseOrdini()
        prodotti = db.get_all_products()
        db.chiudi()
        
        for i, prod in enumerate(prodotti):
            self.tabella_prodotti.insertRow(i)
            
            self.tabella_prodotti.setItem(i, 0, QTableWidgetItem(str(prod.id_prodotto)))
            self.tabella_prodotti.setItem(i, 1, QTableWidgetItem(prod.nome))
            self.tabella_prodotti.setItem(i, 2, QTableWidgetItem(prod.categoria))
            self.tabella_prodotti.setItem(i, 3, QTableWidgetItem(f"€{prod.prezzo:.2f}"))
            
            # Bottone elimina
            btn_elimina = QPushButton("🗑️")
            btn_elimina.setMaximumWidth(40)
            btn_elimina.clicked.connect(lambda checked, id=prod.id_prodotto: self.elimina_prodotto(id))
            self.tabella_prodotti.setCellWidget(i, 4, btn_elimina)
    
    def dialogo_nuovo_prodotto(self):
        """Dialog per aggiungere nuovo prodotto"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuovo Prodotto")
        dialog.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout()
        
        # Nome
        layout.addWidget(QLabel("Nome:"))
        nome_input = QLineEdit()
        layout.addWidget(nome_input)
        
        # Categoria
        layout.addWidget(QLabel("Categoria:"))
        categoria_combo = QComboBox()
        categoria_combo.addItems(self.gestione.get_categorie())
        layout.addWidget(categoria_combo)
        
        # Prezzo
        layout.addWidget(QLabel("Prezzo:"))
        prezzo_input = QDoubleSpinBox()
        prezzo_input.setMaximum(999.99)
        prezzo_input.setDecimals(2)
        prezzo_input.setValue(0.00)
        layout.addWidget(prezzo_input)
        
        # Bottoni
        btn_layout = QHBoxLayout()
        
        btn_annulla = QPushButton("Annulla")
        btn_annulla.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_annulla)
        
        btn_ok = QPushButton("✓ Aggiungi")
        btn_ok.setStyleSheet("background-color: #27ae60; color: white;")
        btn_ok.clicked.connect(lambda: self.aggiungi_prodotto(nome_input.text(), categoria_combo.currentText(), prezzo_input.value(), dialog))
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def aggiungi_prodotto(self, nome: str, categoria: str, prezzo: float, dialog):
        """Aggiungi prodotto al database"""
        if not nome or prezzo <= 0:
            QMessageBox.warning(self, "Errore", "Compila tutti i campi correttamente!")
            return
        
        db = DatabaseOrdini()
        db.add_product(nome, categoria, prezzo)
        db.chiudi()
        
        self.aggiorna_tabella_prodotti()
        QMessageBox.information(self, "Successo", f"Prodotto '{nome}' aggiunto!")
        dialog.accept()
    
    def elimina_prodotto(self, id_prodotto: int):
        """Elimina prodotto"""
        reply = QMessageBox.question(self, "Conferma", "Vuoi davvero eliminare questo prodotto?")
        if reply == QMessageBox.Yes:
            db = DatabaseOrdini()
            db.delete_product(id_prodotto)
            db.chiudi()
            self.aggiorna_tabella_prodotti()
    
    def dialogo_nuova_categoria(self):
        """Dialog per nuova categoria"""
        nome, ok = QInputDialog.getText(self, "Nuova Categoria", "Nome categoria:")
        if ok and nome:
            db = DatabaseOrdini()
            db.add_category(nome)
            db.chiudi()
            self.lista_categorie.addItem(nome)
    
    def elimina_categoria(self):
        """Elimina categoria selezionata"""
        item = self.lista_categorie.currentItem()
        if not item:
            QMessageBox.warning(self, "Errore", "Seleziona una categoria!")
            return
        
        categoria = item.text()
        reply = QMessageBox.question(self, "Conferma", f"Elimina categoria '{categoria}'?")
        if reply == QMessageBox.Yes:
            db = DatabaseOrdini()
            db.delete_category(categoria)
            db.chiudi()
            self.lista_categorie.takeItem(self.lista_categorie.row(item))
    
    def salva_prodotti(self):
        """Salva modifiche ai prodotti"""
        QMessageBox.information(self, "Successo", "Prodotti salvati!")
    
    def esporta_csv(self):
        """Esporta menu in CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Esporta Menu", "menu.csv", "CSV (*.csv)")
        if not file_path:
            return
        
        db = DatabaseOrdini()
        prodotti = db.get_all_products()
        db.chiudi()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("id,nome,categoria,prezzo\n")
                for prod in prodotti:
                    f.write(f"{prod.id_prodotto},{prod.nome},{prod.categoria},{prod.prezzo:.2f}\n")
            QMessageBox.information(self, "Successo", f"Menu esportato in:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'esportazione:\n{str(e)}")
    
    def importa_csv(self):
        """Importa menu da CSV"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Importa Menu", "", "CSV (*.csv)")
        if not file_path:
            return
        
        try:
            db = DatabaseOrdini()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines:
                    QMessageBox.warning(self, "Errore", "File CSV vuoto!")
                    return
                
                for line in lines[1:]:  # Salta header
                    parts = line.strip().split(',')
                    if len(parts) == 4:
                        try:
                            id_prod, nome, categoria, prezzo = parts
                            prezzo = float(prezzo)
                            db.add_or_update_product(int(id_prod), nome, categoria, prezzo)
                        except:
                            continue
            
            db.chiudi()
            self.aggiorna_tabella_prodotti()
            QMessageBox.information(self, "Successo", "Menu importato correttamente!")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'importazione:\n{str(e)}")
    
    def mostra_schermata_ordine(self, numero_tavolo: int, tab_ordinato: bool = False):
        """Schermata ordine SPLIT: 1/3 sinistra con TAB, 2/3 destra menu"""
        widget = QWidget()
        self.setCentralWidget(widget)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        # ============================================================
        # HEADER TOP: FRECCIA INDIETRO
        # ============================================================
        header_top = QHBoxLayout()
        header_top.setContentsMargins(15, 10, 15, 10)
        header_top.setSpacing(15)
        
        btn_back = QPushButton("←")
        btn_back.setMinimumHeight(40)
        btn_back.setMaximumWidth(50)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_back.clicked.connect(self.torna_a_tavoli)
        header_top.addWidget(btn_back)
        header_top.addStretch()
        
        header_top_widget = QWidget()
        header_top_widget.setLayout(header_top)
        header_top_widget.setStyleSheet("background-color: #34495e;")
        header_top_widget.setFixedHeight(60)
        layout.addWidget(header_top_widget)
        
        # ============================================================
        # SINISTRA: 1/3 - RIEPILOGO CON TAB
        # ============================================================
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        sinistra_widget = QWidget()
        sinistra_widget.setStyleSheet("background-color: #2c3e50;")
        sinistra_layout = QVBoxLayout(sinistra_widget)
        sinistra_layout.setContentsMargins(10, 10, 10, 10)
        sinistra_layout.setSpacing(10)
        
        # Header
        header_label = QLabel("📋 Ordine")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        sinistra_layout.addWidget(header_label)
        
        # Info tavolo
        info_label = QLabel(f"Tavolo: {numero_tavolo}\nPersone: {ordine.numero_persone}")
        info_label.setStyleSheet("font-size: 12px; color: white; padding: 8px; background-color: #34495e; border-radius: 6px;")
        info_label.setAlignment(Qt.AlignCenter)
        sinistra_layout.addWidget(info_label)
        
        # TAB BUTTON: Ordinato / Ordinare (con sottolineatura)
        tab_button_layout = QHBoxLayout()
        tab_button_layout.setContentsMargins(0, 0, 0, 0)
        tab_button_layout.setSpacing(2)
        
        # ORDINATO
        btn_ordinato = QPushButton("✓ Ordinato")
        stile_ordinato_inattivo = """
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-bottom: 3px solid #34495e;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px 0px 0px 4px;
            }
            QPushButton:hover { background-color: #2c3e50; }
        """
        stile_ordinato_attivo = """
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                border-bottom: 4px solid #f39c12;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px 0px 0px 4px;
            }
            QPushButton:hover { background-color: #2c3e50; }
        """
        btn_ordinato.setStyleSheet(stile_ordinato_attivo if tab_ordinato else stile_ordinato_inattivo)
        btn_ordinato.setMinimumHeight(35)
        btn_ordinato.clicked.connect(lambda: self.cambia_tab_ordinato(numero_tavolo, btn_ordinato, btn_ordinare))
        tab_button_layout.addWidget(btn_ordinato, 1)
        
        # ORDINARE
        btn_ordinare = QPushButton("+ Ordinare")
        stile_ordinare_inattivo = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-bottom: 3px solid #3498db;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 0px 4px 4px 0px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """
        stile_ordinare_attivo = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-bottom: 4px solid #f39c12;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
                border-radius: 0px 4px 4px 0px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """
        btn_ordinare.setStyleSheet(stile_ordinare_attivo if not tab_ordinato else stile_ordinare_inattivo)
        btn_ordinare.setMinimumHeight(35)
        btn_ordinare.clicked.connect(lambda: self.cambia_tab_ordinare(numero_tavolo, btn_ordinato, btn_ordinare))
        tab_button_layout.addWidget(btn_ordinare, 1)
        
        # Salva i bottoni per dopo
        self.btn_ordinato_tab = btn_ordinato
        self.btn_ordinare_tab = btn_ordinare
        self.stile_ordinato_attivo = stile_ordinato_attivo
        self.stile_ordinato_inattivo = stile_ordinato_inattivo
        self.stile_ordinare_attivo = stile_ordinare_attivo
        self.stile_ordinare_inattivo = stile_ordinare_inattivo
        
        sinistra_layout.addLayout(tab_button_layout)
        
        # SCROLL AREA per contenuto (Ordinato o Ordinare)
        self.scroll_ordine = QScrollArea()
        self.scroll_ordine.setWidgetResizable(True)
        self.scroll_ordine.setStyleSheet("""
            QScrollArea { border: none; background-color: #2c3e50; }
            QScrollBar:vertical { width: 6px; background-color: #34495e; }
            QScrollBar::handle:vertical { background-color: #95a5a6; border-radius: 3px; }
        """)
        
        self.container_ordine = QWidget()
        self.container_ordine.setStyleSheet("background-color: #2c3e50;")
        self.layout_ordine = QVBoxLayout(self.container_ordine)
        self.layout_ordine.setContentsMargins(0, 0, 0, 0)
        self.layout_ordine.setSpacing(1)
        
        self.scroll_ordine.setWidget(self.container_ordine)
        sinistra_layout.addWidget(self.scroll_ordine, 1)
        
        # Totale
        totale = QLabel(f"€{ordine.get_totale():.2f}")
        totale.setStyleSheet("font-size: 22px; font-weight: bold; color: #27ae60; padding: 12px; text-align: center;")
        totale.setAlignment(Qt.AlignCenter)
        sinistra_layout.addWidget(totale)
        
        # Salva il label totale per aggiornarlo
        self.label_totale = totale
        
        # BOTTONI DINAMICI (cambiano se Ordinato o Ordinare)
        self.btn_layout_ordini = QHBoxLayout()
        self.btn_layout_ordini.setSpacing(6)
        
        # Se ordinato, mostra PAGARE; se ordinare, mostra solo CONFERMA
        self.aggiorna_bottoni_ordini(numero_tavolo, tab_ordinato)
        
        sinistra_layout.addLayout(self.btn_layout_ordini)
        
        # ============================================================
        # DESTRA: 2/3 - MENU
        # ============================================================
        destra_widget = QWidget()
        destra_widget.setStyleSheet("background-color: white;")
        destra_layout = QVBoxLayout(destra_widget)
        self.destra_layout = destra_layout  # Salva per inserire ricerca dopo
        destra_layout.setContentsMargins(0, 0, 0, 0)
        destra_layout.setSpacing(0)
        
        # Header DESTRA con ricerca a destra
        header_destra_layout = QHBoxLayout()
        header_destra_layout.setContentsMargins(15, 12, 15, 12)
        header_destra_layout.setSpacing(15)
        
        header_label2 = QLabel(f"Tavolo {numero_tavolo} ({ordine.numero_persone})")
        header_label2.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        header_destra_layout.addWidget(header_label2)
        
        header_destra_layout.addStretch()
        
        # Bottone lente di ricerca (angolo destro)
        btn_ricerca = QPushButton("🔍")
        btn_ricerca.setMaximumWidth(45)
        btn_ricerca.setMinimumHeight(38)
        btn_ricerca.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_ricerca.clicked.connect(lambda: self.apri_popup_ricerca(numero_tavolo))
        header_destra_layout.addWidget(btn_ricerca)
        
        # Bottone 3 puntini (menu)
        btn_menu = QPushButton("⋮")
        btn_menu.setMaximumWidth(45)
        btn_menu.setMinimumHeight(38)
        btn_menu.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_menu.clicked.connect(lambda: self.mostra_menu_ordine(numero_tavolo))
        header_destra_layout.addWidget(btn_menu)
        
        header_destra_widget = QWidget()
        header_destra_widget.setLayout(header_destra_layout)
        header_destra_widget.setStyleSheet("background-color: #34495e;")
        header_destra_widget.setFixedHeight(60)
        destra_layout.addWidget(header_destra_widget)
        
        # Menu
        menu_layout = QHBoxLayout()
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)
        
        # Categorie
        categorie_scroll = QScrollArea()
        categorie_scroll.setWidgetResizable(True)
        categorie_scroll.setMaximumWidth(90)
        categorie_scroll.setStyleSheet("QScrollArea { border: none; background-color: #ecf0f1; }")
        
        categorie_widget = QWidget()
        categorie_layout = QVBoxLayout(categorie_widget)
        categorie_layout.setContentsMargins(5, 5, 5, 5)
        categorie_layout.setSpacing(3)
        
        self.pulsanti_categorie = {}
        categorie = self.gestione.get_categorie()
        
        for categoria in categorie:
            btn = QPushButton(categoria)
            btn.setMinimumHeight(38)
            btn.setMaximumHeight(38)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 9px;
                    font-weight: bold;
                    text-align: center;
                    white-space: normal;
                }
                QPushButton:hover { background-color: #e67e22; }
            """)
            btn.clicked.connect(lambda checked, cat=categoria, n=numero_tavolo: self.cambia_categoria(cat, n))
            categorie_layout.addWidget(btn)
            self.pulsanti_categorie[categoria] = btn
        
        categorie_layout.addStretch()
        categorie_widget.setLayout(categorie_layout)
        categorie_scroll.setWidget(categorie_widget)
        menu_layout.addWidget(categorie_scroll)
        
        # Prodotti
        self.scroll_prodotti = QScrollArea()
        self.scroll_prodotti.setWidgetResizable(True)
        self.scroll_prodotti.setStyleSheet("""
            QScrollArea { border: none; background-color: white; }
            QScrollBar:vertical { width: 8px; background-color: #ecf0f1; }
            QScrollBar::handle:vertical { background-color: #95a5a6; border-radius: 4px; }
        """)
        
        self.widget_prodotti = QWidget()
        self.widget_prodotti.setStyleSheet("background-color: white;")
        self.layout_prodotti = QVBoxLayout(self.widget_prodotti)
        self.layout_prodotti.setSpacing(0)
        self.layout_prodotti.setContentsMargins(8, 8, 8, 8)
        
        self.scroll_prodotti.setWidget(self.widget_prodotti)
        menu_layout.addWidget(self.scroll_prodotti, 1)
        
        menu_widget = QWidget()
        menu_widget.setLayout(menu_layout)
        destra_layout.addWidget(menu_widget, 1)
        
        # SEZIONE A DESTRA: NOTA CUCINA E INGREDIENTI
        self.sezione_destra_widget = QWidget()
        self.sezione_destra_widget.setStyleSheet("background-color: #ecf0f1; border-left: 2px solid #bdc3c7;")
        self.sezione_destra_widget.setMaximumWidth(250)
        self.sezione_destra_layout = QVBoxLayout(self.sezione_destra_widget)
        self.sezione_destra_layout.setContentsMargins(15, 15, 15, 15)
        self.sezione_destra_layout.setSpacing(10)
        
        # Inizialmente vuota
        label_vuoto = QLabel("Seleziona un prodotto")
        label_vuoto.setStyleSheet("color: #95a5a6; font-size: 12px; padding: 20px; text-align: center;")
        label_vuoto.setAlignment(Qt.AlignCenter)
        self.sezione_destra_layout.addWidget(label_vuoto)
        self.sezione_destra_layout.addStretch()
        
        destra_layout.addWidget(self.sezione_destra_widget)
        
        # Aggiungi sinistra e destra a main_layout
        main_layout.addWidget(sinistra_widget, 1)
        main_layout.addWidget(destra_widget, 2)
        
        layout.addLayout(main_layout)
        
        # Inizializza
        self.tavolo_attuale = numero_tavolo
        self.categoria_attuale = "Bevande"
        self.note_prodotti = {}  # Inizializza note per i prodotti
        QApplication.processEvents()
        
        # Mostra il TAB corretto
        if tab_ordinato:
            self.cambia_tab_ordinato(numero_tavolo, self.btn_ordinato_tab, self.btn_ordinare_tab)
        else:
            self.cambia_tab_ordinare(numero_tavolo, self.btn_ordinato_tab, self.btn_ordinare_tab)
        
        self.mostra_prodotti_card("Bevande", numero_tavolo)
    
    def aggiorna_bottoni_ordini(self, numero_tavolo: int, tab_ordinato: bool):
        """Aggiorna i bottoni: Ordinare → Conferma, Ordinato → Pagare"""
        # Pulisci layout
        while self.btn_layout_ordini.count():
            child = self.btn_layout_ordini.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if tab_ordinato:
            # TAB ORDINATO: Mostra bottone VUOTO e PAGARE
            btn_vuoto = QPushButton("🗑️ Vuoto")
            btn_vuoto.setMinimumHeight(45)
            btn_vuoto.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #7f8c8d; }
            """)
            btn_vuoto.clicked.connect(lambda: self.mostra_motivo_rifiuto(numero_tavolo))
            self.btn_layout_ordini.addWidget(btn_vuoto)
            
            btn_pagare = QPushButton("💳 Pagare")
            btn_pagare.setMinimumHeight(45)
            btn_pagare.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            btn_pagare.clicked.connect(lambda: self.paga_ordine(numero_tavolo))
            self.btn_layout_ordini.addWidget(btn_pagare)
        else:
            # TAB ORDINARE: Mostra bottone CONFERMA
            btn_conf = QPushButton("✓ Conferma")
            btn_conf.setMinimumHeight(45)
            btn_conf.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #229954; }
            """)
            btn_conf.clicked.connect(lambda: self.conferma_ordine_final(numero_tavolo))
            self.btn_layout_ordini.addWidget(btn_conf)
    
    def paga_ordine(self, numero_tavolo: int):
        """Schermata pagamento FULLSCREEN"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        # Schermata FULLSCREEN
        widget = QWidget()
        self.setCentralWidget(widget)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # HEADER
        header = QLabel("💳 PAGAMENTO")
        header.setStyleSheet("font-size: 32px; font-weight: bold; color: white; padding: 25px; background-color: #34495e;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # CONTENUTO CENTRALE
        centrale = QWidget()
        centrale_layout = QVBoxLayout(centrale)
        centrale_layout.setContentsMargins(40, 40, 40, 40)
        centrale_layout.setSpacing(30)
        
        # INFO TAVOLO
        info = QLabel(f"Tavolo: {numero_tavolo} | Persone: {ordine.numero_persone}")
        info.setStyleSheet("font-size: 18px; color: white; padding: 15px; background-color: #2c3e50; border-radius: 4px;")
        info.setAlignment(Qt.AlignCenter)
        centrale_layout.addWidget(info)
        
        # TOTALE GRANDE
        totale_label = QLabel(f"TOTALE: €{ordine.get_totale():.2f}")
        totale_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #27ae60; padding: 30px;")
        totale_label.setAlignment(Qt.AlignCenter)
        centrale_layout.addWidget(totale_label)
        
        # OPZIONI PAGAMENTO (orizzontale)
        pag_layout = QHBoxLayout()
        pag_layout.setSpacing(20)
        
        btn_contanti = QPushButton("💵 CONTANTI")
        btn_contanti.setMinimumHeight(120)
        btn_contanti.setMinimumWidth(250)
        btn_contanti.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        btn_contanti.clicked.connect(lambda: self.completa_pagamento_fullscreen(numero_tavolo, "Contanti"))
        pag_layout.addWidget(btn_contanti)
        
        btn_carta = QPushButton("💳 CARTA")
        btn_carta.setMinimumHeight(120)
        btn_carta.setMinimumWidth(250)
        btn_carta.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_carta.clicked.connect(lambda: self.completa_pagamento_fullscreen(numero_tavolo, "Carta"))
        pag_layout.addWidget(btn_carta)
        
        btn_stampa = QPushButton("🖨️ STAMPA")
        btn_stampa.setMinimumHeight(120)
        btn_stampa.setMinimumWidth(250)
        btn_stampa.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        btn_stampa.clicked.connect(lambda: self.stampa_scontrino(numero_tavolo))
        pag_layout.addWidget(btn_stampa)
        
        centrale_layout.addLayout(pag_layout)
        centrale_layout.addStretch()
        
        # BOTTONE INDIETRO
        btn_back = QPushButton("← INDIETRO")
        btn_back.setMinimumHeight(60)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        btn_back.clicked.connect(lambda: self.mostra_schermata_ordine(numero_tavolo, tab_ordinato=True))
        centrale_layout.addWidget(btn_back)
        
        centrale.setLayout(centrale_layout)
        layout.addWidget(centrale)
    
    def completa_pagamento_fullscreen(self, numero_tavolo: int, metodo: str):
        """Completa il pagamento FULLSCREEN e chiude il tavolo"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        QMessageBox.information(self, "Pagamento Completato", 
                              f"Pagamento ricevuto in {metodo}!\n\nTotale: €{ordine.get_totale():.2f}")
        
        self.gestione.libera_tavolo(numero_tavolo)
        self.torna_a_tavoli()
    
    def aggiungi_numero_calc(self, display, numero):
        """Aggiungi numero alla calcolatrice"""
        testo = display.text().replace("€", "").strip()
        if numero == '.':
            if '.' not in testo:
                testo += numero
        else:
            if testo == '0' or testo == '':
                testo = numero
            else:
                testo += numero
        display.setText(f"€{testo}")
    
    def stampa_scontrino(self, numero_tavolo: int):
        """Stampa lo scontrino con i prodotti"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        # Crea il testo dello scontrino
        scontrino = "=" * 40 + "\n"
        scontrino += "SCONTRINO TAVOLO\n"
        scontrino += "=" * 40 + "\n\n"
        scontrino += f"Tavolo: {numero_tavolo}\n"
        scontrino += f"Persone: {ordine.numero_persone}\n"
        scontrino += f"Data: {ordine.data_creazione.strftime('%d/%m/%Y %H:%M')}\n\n"
        
        scontrino += "-" * 40 + "\n"
        scontrino += f"{'Prodotto':<25} {'Qtà':<5} {'Prezzo':>8}\n"
        scontrino += "-" * 40 + "\n"
        
        for riga in ordine.righe:
            scontrino += f"{riga.prodotto.nome[:24]:<25} {riga.quantita:<5} €{riga.get_subtotale():>7.2f}\n"
            
            # Aggiungi nota se c'è
            if hasattr(self, 'note_prodotti'):
                for idx, nota_dict in self.note_prodotti.items():
                    if 'nota' in nota_dict and nota_dict['nota'].strip():
                        scontrino += f"  📝 {nota_dict['nota']}\n"
                    if 'ingredienti' in nota_dict and nota_dict['ingredienti'].strip():
                        scontrino += f"  🥘 {nota_dict['ingredienti']}\n"
        
        scontrino += "-" * 40 + "\n"
        scontrino += f"{'TOTALE':<30} €{ordine.get_totale():>8.2f}\n"
        scontrino += "=" * 40 + "\n"
        scontrino += "Grazie della visita!\n"
        scontrino += "=" * 40 + "\n"
        
        # Mostra in un dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Scontrino")
        dialog.setGeometry(400, 300, 500, 600)
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setText(scontrino)
        text.setReadOnly(True)
        text.setStyleSheet("""
            QTextEdit {
                font-family: Courier;
                font-size: 10px;
                padding: 10px;
                border: 1px solid #bdc3c7;
            }
        """)
        layout.addWidget(text)
        
        # Bottone stampa
        btn_print = QPushButton("🖨️ Stampa Scontrino")
        btn_print.setMinimumHeight(40)
        btn_print.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_print.clicked.connect(lambda: self.stampa_reale(scontrino))
        layout.addWidget(btn_print)
        
        # Bottone chiudi
        btn_close = QPushButton("Chiudi")
        btn_close.setMinimumHeight(40)
        btn_close.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def stampa_reale(self, testo):
        """Simula la stampa dello scontrino"""
        QMessageBox.information(self, "Stampa", "Scontrino inviato alla stampante!\n\n(In un sistema reale, questo invierebbe il comando alla stampante termica)")
    
    def mostra_prodotti_card(self, categoria: str, numero_tavolo: int, search: bool = False, termine_ricerca: str = ""):
        """Mostra prodotti di una categoria (search per ricerca)"""
        # Pulisci il layout
        while self.layout_prodotti.count():
            child = self.layout_prodotti.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        if search and termine_ricerca:
            # Ricerca in tutte le categorie
            tutti_prodotti = self.gestione.get_tutti_prodotti()
            termine = termine_ricerca.lower()
            prodotti = [p for p in tutti_prodotti if termine in p.nome.lower()]
        else:
            # Mostra solo della categoria
            prodotti = self.gestione.get_categoria_prodotti(categoria)
        
        # Mostra i prodotti
        self._mostra_grid_prodotti(prodotti, numero_tavolo, ordine)
        self.layout_prodotti.addStretch()
    
    def _mostra_grid_prodotti(self, prodotti: list, numero_tavolo: int, ordine):
        """Helper: mostra prodotti in tabella come in foto"""
        # Crea una tabella
        tabella = QTableWidget()
        tabella.setColumnCount(2)
        tabella.setHorizontalHeaderLabels(["Prodotto", "Prezzo"])
        tabella.horizontalHeader().setStretchLastSection(False)
        tabella.setColumnWidth(0, 220)
        tabella.setColumnWidth(1, 80)
        tabella.setRowCount(len(prodotti))
        tabella.setSelectionBehavior(QTableWidget.SelectRows)
        tabella.setSelectionMode(QTableWidget.NoSelection)
        tabella.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        for i, prodotto in enumerate(prodotti):
            quantita = 0
            # CercaQuantità sia in ordinare che in ordinato
            for riga in ordine.righe_ordinare:
                if riga.prodotto.id_prodotto == prodotto.id_prodotto:
                    quantita += riga.quantita
            for riga in ordine.righe_ordinato:
                if riga.prodotto.id_prodotto == prodotto.id_prodotto:
                    quantita += riga.quantita
            
            # Nome
            nome_text = prodotto.nome
            if quantita > 0:
                nome_text = f"{prodotto.nome} x{quantita}"
            
            nome_item = QTableWidgetItem(nome_text)
            nome_item.setForeground(QColor("#3498db" if quantita > 0 else "#2c3e50"))
            nome_item.setFont(QFont("Arial", 11, QFont.Bold))
            tabella.setItem(i, 0, nome_item)
            
            # Prezzo
            prezzo_item = QTableWidgetItem(f"€{prodotto.prezzo:.2f}")
            prezzo_item.setForeground(QColor("#2c3e50"))
            prezzo_item.setFont(QFont("Arial", 11, QFont.Bold))
            prezzo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tabella.setItem(i, 1, prezzo_item)
            
            tabella.setRowHeight(i, 40)
        
        # Rendi cliccabile - trova il prodotto per nome
        def click_riga(item):
            nome_cercato = item.text().split(' x')[0]  # Rimuovi x1, x2 etc
            prodotto_trovato = None
            for p in prodotti:
                if p.nome == nome_cercato:
                    prodotto_trovato = p
                    break
            if prodotto_trovato:
                self.card_cliccata(numero_tavolo, prodotto_trovato)
        
        tabella.itemClicked.connect(click_riga)
        
        self.layout_prodotti.addWidget(tabella)
    
    def card_cliccata(self, numero_tavolo: int, prodotto: Prodotto):
        """Click prodotto = aggiunge direttamente senza cambiare categoria"""
        self.gestione.aggiungi_al_ordine(numero_tavolo, prodotto, 1)
        # Aggiorna il riepilogo e il prezzo
        self.mostra_tab_ordinare(numero_tavolo)
        # Aggiorna il prezzo totale
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        self.label_totale.setText(f"€{ordine.get_totale():.2f}")
        # Mostra la sezione a destra (Nota/Ingredienti) - deselezionato per ora
        self.mostra_sezione_destra(None)
    
    def aggiorna_riepilogo_ordine(self, numero_tavolo: int):
        """Aggiorna solo il riepilogo senza ricreare la schermata"""
        self.mostra_tab_ordinare(numero_tavolo)
    
    def rimuovi_dal_riepilogo(self, numero_tavolo: int, indice: int):
        """Rimuovi prodotto dal riepilogo (da ordinare)"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine and indice < len(ordine.righe_ordinare):
            ordine.righe_ordinare.pop(indice)
            self.mostra_tab_ordinare(numero_tavolo)
            # Aggiorna il prezzo totale
            self.label_totale.setText(f"€{ordine.get_totale():.2f}")
            self.mostra_sezione_destra(None)
    
    def mostra_sezione_destra(self, prodotto: Prodotto):
        """Mostra nota cucina e ingredienti per il prodotto selezionato come TAB/bottoni popup"""
        # Pulisci layout
        while self.sezione_destra_layout.count():
            child = self.sezione_destra_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if prodotto is None:
            # Nessun prodotto selezionato
            label_vuoto = QLabel("Seleziona un prodotto")
            label_vuoto.setStyleSheet("color: #95a5a6; font-size: 12px; padding: 20px; text-align: center;")
            label_vuoto.setAlignment(Qt.AlignCenter)
            self.sezione_destra_layout.addWidget(label_vuoto)
            self.sezione_destra_layout.addStretch()
            return
        
        # Salva il prodotto selezionato
        self.prodotto_destra = prodotto
        
        # TAB BUTTON: Nota Cucina
        btn_nota = QPushButton("📝 Nota Cucina")
        btn_nota.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-height: 45px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_nota.clicked.connect(self.apri_popup_nota)
        self.sezione_destra_layout.addWidget(btn_nota)
        
        # TAB BUTTON: Ingredienti (solo per Pizze, Primi piatti, Panini)
        categorie_con_ingredienti = ["Pizze", "Primi piatti", "Panini"]
        
        if prodotto.categoria in categorie_con_ingredienti:
            btn_ingredienti = QPushButton("🥘 Ingredienti")
            btn_ingredienti.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    padding: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 6px;
                    min-height: 45px;
                }
                QPushButton:hover { background-color: #e67e22; }
            """)
            btn_ingredienti.clicked.connect(self.apri_popup_ingredienti)
            self.sezione_destra_layout.addWidget(btn_ingredienti)
        
        self.sezione_destra_layout.addStretch()
    
    def mostra_menu_ordine(self, numero_tavolo: int):
        """Mostra menu con opzioni per il prodotto selezionato"""
        if self.prodotto_selezionato_idx is None:
            QMessageBox.warning(self, "Errore", "Seleziona un prodotto!")
            return
        
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        # Cerca il prodotto in ordinare (prioritario)
        riga = None
        is_ordinare = False
        
        if self.prodotto_selezionato_idx < len(ordine.righe_ordinare):
            riga = ordine.righe_ordinare[self.prodotto_selezionato_idx]
            is_ordinare = True
        elif self.prodotto_selezionato_idx < len(ordine.righe_ordinato):
            riga = ordine.righe_ordinato[self.prodotto_selezionato_idx]
            is_ordinare = False
        
        if not riga:
            QMessageBox.warning(self, "Errore", "Prodotto non trovato!")
            return
        
        # Crea menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # Azione attesa/sblocca
        if riga.in_attesa:
            action_attesa = menu.addAction("🔓 Sblocca")
            action_attesa.triggered.connect(lambda: self.sblocca_prodotto(numero_tavolo, self.prodotto_selezionato_idx, is_ordinare))
        else:
            action_attesa = menu.addAction("⏸️ Metti in Attesa")
            action_attesa.triggered.connect(lambda: self.metti_attesa(numero_tavolo, self.prodotto_selezionato_idx, is_ordinare))
        
        # Mostra il menu
        pos = QCursor.pos()
        menu.exec_(pos)
    
    def metti_attesa(self, numero_tavolo: int, idx: int, is_ordinare: bool = True):
        """Metti un prodotto in attesa"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        if is_ordinare:
            if idx < len(ordine.righe_ordinare):
                ordine.righe_ordinare[idx].in_attesa = True
        else:
            if idx < len(ordine.righe_ordinato):
                ordine.righe_ordinato[idx].in_attesa = True
        
        # Colora il tavolo in rosso
        tavolo = self.gestione.get_tavolo(numero_tavolo)
        if tavolo:
            tavolo.in_attesa = True
        
        self.mostra_tab_ordinare(numero_tavolo)
        self.mostra_tab_ordinato(numero_tavolo)
        self.aggiorna_colori_tavoli()
    
    def sblocca_prodotto(self, numero_tavolo: int, idx: int, is_ordinare: bool = True):
        """Sblocca un prodotto in attesa"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        if is_ordinare:
            if idx < len(ordine.righe_ordinare):
                ordine.righe_ordinare[idx].in_attesa = False
        else:
            if idx < len(ordine.righe_ordinato):
                ordine.righe_ordinato[idx].in_attesa = False
        
        # Controlla se ci sono altri prodotti in attesa
        ha_attesa = any(riga.in_attesa for riga in ordine.righe_ordinare)
        ha_attesa = ha_attesa or any(riga.in_attesa for riga in ordine.righe_ordinato)
        
        if not ha_attesa:
            tavolo = self.gestione.get_tavolo(numero_tavolo)
            if tavolo:
                tavolo.in_attesa = False
        
        self.mostra_tab_ordinare(numero_tavolo)
        self.mostra_tab_ordinato(numero_tavolo)
        self.aggiorna_colori_tavoli()
    
    def seleziona_prodotto_ordinato(self, numero_tavolo: int, idx: int):
        """Seleziona prodotto in ordinato"""
        if not hasattr(self, 'prodotto_selezionato_ordinato_idx'):
            self.prodotto_selezionato_ordinato_idx = None
        
        # Toggle selezione
        if self.prodotto_selezionato_ordinato_idx == idx:
            self.prodotto_selezionato_ordinato_idx = None
        else:
            self.prodotto_selezionato_ordinato_idx = idx
        
        self.mostra_tab_ordinato(numero_tavolo)
    
    def mostra_motivo_rifiuto(self, numero_tavolo: int):
        """Mostra popup per scegliere motivo rifiuto (Annullato/Sostituzione)"""
        if not hasattr(self, 'prodotto_selezionato_ordinato_idx') or self.prodotto_selezionato_ordinato_idx is None:
            QMessageBox.warning(self, "Errore", "Seleziona un prodotto!")
            return
        
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if self.prodotto_selezionato_ordinato_idx >= len(ordine.righe_ordinato):
            QMessageBox.warning(self, "Errore", "Prodotto non trovato!")
            return
        
        riga = ordine.righe_ordinato[self.prodotto_selezionato_ordinato_idx]
        
        # Crea popup
        dialog = QDialog(self, Qt.FramelessWindowHint)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #34495e;
                border-radius: 10px;
            }
        """)
        dialog.setFixedSize(350, 200)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Titolo
        titolo = QLabel(f"Motivo - {riga.prodotto.nome}")
        titolo.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold;")
        layout.addWidget(titolo)
        
        # Bottoni
        btn_annullato = QPushButton("❌ Annullato")
        btn_annullato.setMinimumHeight(40)
        btn_annullato.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        btn_annullato.clicked.connect(lambda: self.salva_motivo_rifiuto(dialog, riga, "Annullato", numero_tavolo))
        layout.addWidget(btn_annullato)
        
        btn_sostituzione = QPushButton("🔄 Sostituzione Prodotto")
        btn_sostituzione.setMinimumHeight(40)
        btn_sostituzione.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #d68910; }
        """)
        btn_sostituzione.clicked.connect(lambda: self.salva_motivo_rifiuto(dialog, riga, "Sostituzione Prodotto", numero_tavolo))
        layout.addWidget(btn_sostituzione)
        
        # Centra il dialog
        x = (self.width() - dialog.width()) // 2
        y = (self.height() - dialog.height()) // 2
        dialog.setGeometry(x, y, dialog.width(), dialog.height())
        
        dialog.exec_()
    
    def salva_motivo_rifiuto(self, dialog: QDialog, riga: 'RigaOrdine', motivo: str, numero_tavolo: int):
        """Salva motivo rifiuto come nota"""
        riga.motivo_rifiuto = motivo
        dialog.accept()
        self.mostra_tab_ordinato(numero_tavolo)
    
    
        """Mostra/nascondi barra ricerca inline nel header"""
        # Se esiste già, toggle
        if hasattr(self, 'ricerca_barra') and self.ricerca_barra:
            if self.ricerca_barra.isVisible():
                self.ricerca_barra.hide()
                self.ricerca_input.clear()
                self.mostra_prodotti_card(self.categoria_attuale, numero_tavolo, search=False)
            else:
                self.ricerca_barra.show()
                self.ricerca_input.setFocus()
            return
        
        # Crea barra ricerca inline nel header destra
        self.ricerca_barra = QLineEdit()
        self.ricerca_barra.setPlaceholderText("Cerca prodotto...")
        self.ricerca_barra.setStyleSheet("""
            QLineEdit {
                font-size: 12px;
                padding: 8px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background-color: white;
                min-height: 35px;
            }
            QLineEdit:focus { border: 2px solid #2980b9; }
        """)
        
        self.ricerca_input = self.ricerca_barra
        
        # Inserisci la barra nel layout header destra (prima dei bottoni categoria)
        # Trovo il layout dei categorie e inserisco prima
        if hasattr(self, 'destra_layout'):
            # Nascondi inizialmente
            self.ricerca_barra.hide()
            self.destra_layout.insertWidget(1, self.ricerca_barra)
        
        # Connetti la ricerca
        def filtra_prodotti(testo):
            if testo.strip():
                self.mostra_prodotti_card(self.categoria_attuale, numero_tavolo, search=True, termine_ricerca=testo)
            else:
                self.mostra_prodotti_card(self.categoria_attuale, numero_tavolo, search=False)
        
        self.ricerca_input.textChanged.connect(lambda: filtra_prodotti(self.ricerca_input.text()))
        
        # Mostra la barra
        self.ricerca_barra.show()
        self.ricerca_input.setFocus()
    
    def apri_popup_nota(self):
        """Apri popup per nota cucina"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nota Cucina")
        dialog.setGeometry(500, 400, 500, 300)
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout()
        
        title = QLabel(f"📝 Nota Cucina")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        text_nota = QTextEdit()
        text_nota.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 10px;
                background-color: white;
            }
        """)
        text_nota.setPlaceholderText("Es: Senza sale, ben cotto, con salsa a parte...")
        layout.addWidget(text_nota)
        
        btn_layout = QHBoxLayout()
        
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setMinimumHeight(40)
        btn_chiudi.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_chiudi.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_chiudi)
        
        btn_ok = QPushButton("✓ Salva")
        btn_ok.setMinimumHeight(40)
        btn_ok.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_ok.clicked.connect(lambda: self.salva_nota(dialog, text_nota.toPlainText()))
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def apri_popup_ingredienti(self):
        """Apri popup per ingredienti"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ingredienti")
        dialog.setGeometry(500, 400, 500, 300)
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout()
        
        title = QLabel(f"🥘 Ingredienti")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        text_ingredienti = QTextEdit()
        text_ingredienti.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                border: 2px solid #f39c12;
                border-radius: 6px;
                padding: 10px;
                background-color: white;
            }
        """)
        text_ingredienti.setPlaceholderText("Es: Aggiungi mozzarella, pomodoro, basilico...")
        layout.addWidget(text_ingredienti)
        
        btn_layout = QHBoxLayout()
        
        btn_chiudi = QPushButton("Chiudi")
        btn_chiudi.setMinimumHeight(40)
        btn_chiudi.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_chiudi.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_chiudi)
        
        btn_ok = QPushButton("✓ Salva")
        btn_ok.setMinimumHeight(40)
        btn_ok.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        btn_ok.clicked.connect(lambda: self.salva_ingredienti(dialog, text_ingredienti.toPlainText()))
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def salva_nota(self, dialog: QDialog, nota: str):
        """Salva nota cucina nella riga selezionata"""
        if nota.strip():
            ordine = self.gestione.get_ordine_attivo(self.tavolo_attuale)
            if self.prodotto_selezionato_idx is not None and self.prodotto_selezionato_idx < len(ordine.righe_ordinare):
                ordine.righe_ordinare[self.prodotto_selezionato_idx].nota_cucina = nota
                self.mostra_tab_ordinare(self.tavolo_attuale)
            dialog.accept()
        else:
            QMessageBox.warning(self, "Errore", "Scrivi una nota!")
    
    def salva_ingredienti(self, dialog: QDialog, ingredienti: str):
        """Salva ingredienti nella riga selezionata"""
        if ingredienti.strip():
            ordine = self.gestione.get_ordine_attivo(self.tavolo_attuale)
            if self.prodotto_selezionato_idx is not None and self.prodotto_selezionato_idx < len(ordine.righe_ordinare):
                ordine.righe_ordinare[self.prodotto_selezionato_idx].ingredienti = ingredienti
                self.mostra_tab_ordinare(self.tavolo_attuale)
            dialog.accept()
        else:
            QMessageBox.warning(self, "Errore", "Scrivi gli ingredienti!")
    
    def mostra_tab_ordinato(self, numero_tavolo: int):
        """Mostra ordini confermati (ordinato) con note sotto il prodotto"""
        # Pulisci layout
        while self.layout_ordine.count():
            child = self.layout_ordine.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Prendi l'ordine attivo
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if not ordine:
            return
        
        self.righe_ordinato_widget = {}  # Salva riferimenti
        
        # Mostra i prodotti ordinati
        if ordine.righe_ordinato:
            for i, riga in enumerate(ordine.righe_ordinato):
                # Container per prodotto + nota
                container = QWidget()
                container_layout = QVBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(2)
                
                # RIGA PRODOTTO (CLICCABILE)
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(8, 6, 8, 6)
                row_layout.setSpacing(10)
                
                # Nome
                nome_testo = riga.prodotto.nome
                
                # Aggiungi icona attesa se il prodotto è in attesa
                if riga.in_attesa:
                    nome_testo = f"⏸️ {nome_testo}"
                
                nome = QLabel(nome_testo)
                
                # Colora di blu se selezionato
                if hasattr(self, 'prodotto_selezionato_ordinato_idx') and self.prodotto_selezionato_ordinato_idx == i:
                    nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background-color: #3498db; padding: 4px; border-radius: 3px;")
                    row_widget.setStyleSheet("background-color: #2980b9;")
                else:
                    nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
                    row_widget.setStyleSheet("background-color: #34495e;")
                
                # Rendi cliccabile
                nome.mousePressEvent = lambda event, idx=i: self.seleziona_prodotto_ordinato(numero_tavolo, idx)
                row_layout.addWidget(nome, 1)
                
                # Quantità
                qtd = QLabel(f"x{riga.quantita}")
                qtd.setStyleSheet("color: white; font-size: 12px; font-weight: bold; min-width: 28px; text-align: center;")
                row_layout.addWidget(qtd)
                
                # Prezzo
                prezzo = QLabel(f"€{riga.get_subtotale():.2f}")
                prezzo.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; min-width: 60px; text-align: right;")
                row_layout.addWidget(prezzo)
                
                row_widget.setLayout(row_layout)
                container_layout.addWidget(row_widget)
                
                # INDICATORE ATTESA (se in attesa)
                if riga.in_attesa:
                    attesa_label = QLabel("⏸️ In Attesa")
                    attesa_label.setStyleSheet("color: #e74c3c; font-size: 10px; font-weight: bold; padding: 4px 8px; background-color: #2c3e50;")
                    container_layout.addWidget(attesa_label)
                
                # MOTIVO RIFIUTO (se vuoto)
                if riga.motivo_rifiuto.strip():
                    motivo_label = QLabel(f"❌ {riga.motivo_rifiuto}")
                    motivo_label.setStyleSheet("color: #e74c3c; font-size: 10px; font-weight: bold; padding: 4px 8px; background-color: #2c3e50;")
                    container_layout.addWidget(motivo_label)
                
                # NOTE E INGREDIENTI DELLA RIGA
                if riga.nota_cucina.strip():
                    nota_label = QLabel(f"📝 {riga.nota_cucina}")
                    nota_label.setStyleSheet("color: #3498db; font-size: 10px; italic; padding: 4px 8px; background-color: #2c3e50;")
                    nota_label.setWordWrap(True)
                    container_layout.addWidget(nota_label)
                
                if riga.ingredienti.strip():
                    ing_label = QLabel(f"🥘 {riga.ingredienti}")
                    ing_label.setStyleSheet("color: #f39c12; font-size: 10px; italic; padding: 4px 8px; background-color: #2c3e50;")
                    ing_label.setWordWrap(True)
                    container_layout.addWidget(ing_label)
                
                container.setLayout(container_layout)
                self.layout_ordine.addWidget(container)
        else:
            # Nessun ordine ordinato
            label_vuoto = QLabel("Nessun ordine")
            label_vuoto.setStyleSheet("color: #95a5a6; font-size: 11px; padding: 20px;")
            label_vuoto.setAlignment(Qt.AlignCenter)
            self.layout_ordine.addWidget(label_vuoto)
        
        self.layout_ordine.addStretch()
    
    def cambia_tab_ordinato(self, numero_tavolo: int, btn_ordinato, btn_ordinare):
        """Cambia a TAB Ordinato con sottolineatura"""
        btn_ordinato.setStyleSheet(self.stile_ordinato_attivo)
        btn_ordinare.setStyleSheet(self.stile_ordinare_inattivo)
        self.mostra_tab_ordinato(numero_tavolo)
        self.aggiorna_bottoni_ordini(numero_tavolo, True)
    
    def cambia_tab_ordinare(self, numero_tavolo: int, btn_ordinato, btn_ordinare):
        """Cambia a TAB Ordinare con sottolineatura"""
        btn_ordinato.setStyleSheet(self.stile_ordinato_inattivo)
        btn_ordinare.setStyleSheet(self.stile_ordinare_attivo)
        self.mostra_tab_ordinare(numero_tavolo)
        self.aggiorna_bottoni_ordini(numero_tavolo, False)
    
    def mostra_tab_ordinare(self, numero_tavolo: int):
        """Mostra ordini attuali (ordinare) con +/- e selezione"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        # Pulisci layout
        while self.layout_ordine.count():
            child = self.layout_ordine.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.righe_ordinare_widget = {}
        self.prodotto_selezionato_idx = None
        
        for i, riga in enumerate(ordine.righe_ordinare):
            # Container per prodotto + note
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            # RIGA PRODOTTO
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(10)
            
            # Nome (cliccabile per selezionare)
            nome_testo = riga.prodotto.nome
            
            # Aggiungi icona attesa se il prodotto è in attesa
            if riga.in_attesa:
                nome_testo = f"⏸️ {nome_testo}"
            
            nome = QLabel(nome_testo)
            
            # Se questo prodotto è selezionato, cambia colore a blu
            if self.prodotto_selezionato_idx == i:
                nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background-color: #3498db; padding: 4px; border-radius: 3px;")
                row_widget.setStyleSheet("background-color: #2980b9;")
            else:
                nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
                row_widget.setStyleSheet("background-color: #34495e;")
            
            nome.mousePressEvent = lambda event, idx=i, prod=riga.prodotto: self.seleziona_prodotto(numero_tavolo, idx, prod)
            row_layout.addWidget(nome, 1)
            
            # Quantità
            qtd = QLabel(f"x{riga.quantita}")
            qtd.setStyleSheet("color: white; font-size: 12px; font-weight: bold; min-width: 28px; text-align: center;")
            row_layout.addWidget(qtd)
            
            # Bottone -
            btn_minus = QPushButton("-")
            btn_minus.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 25px;
                    min-height: 25px;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            btn_minus.clicked.connect(lambda checked, idx=i: self.diminuisci_quantita(numero_tavolo, idx))
            row_layout.addWidget(btn_minus)
            
            # Bottone +
            btn_plus = QPushButton("+")
            btn_plus.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 25px;
                    min-height: 25px;
                }
                QPushButton:hover { background-color: #229954; }
            """)
            btn_plus.clicked.connect(lambda checked, idx=i, prod=riga.prodotto: self.aumenta_quantita(numero_tavolo, idx, prod))
            row_layout.addWidget(btn_plus)
            
            # Prezzo
            prezzo = QLabel(f"€{riga.get_subtotale():.2f}")
            prezzo.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; min-width: 60px; text-align: right;")
            row_layout.addWidget(prezzo)
            
            row_widget.setLayout(row_layout)
            row_widget.setStyleSheet("background-color: #34495e;")
            container_layout.addWidget(row_widget)
            
            # NOTE SOTTO IL PRODOTTO
            if riga.nota_cucina.strip():
                nota_label = QLabel(f"📝 {riga.nota_cucina}")
                nota_label.setStyleSheet("color: #3498db; font-size: 10px; italic; padding: 4px 8px; background-color: #2c3e50;")
                nota_label.setWordWrap(True)
                container_layout.addWidget(nota_label)
            
            if riga.ingredienti.strip():
                ing_label = QLabel(f"🥘 {riga.ingredienti}")
                ing_label.setStyleSheet("color: #f39c12; font-size: 10px; italic; padding: 4px 8px; background-color: #2c3e50;")
                ing_label.setWordWrap(True)
                container_layout.addWidget(ing_label)
            
            container.setLayout(container_layout)
            self.layout_ordine.addWidget(container)
            self.righe_ordinare_widget[i] = container
        
        self.layout_ordine.addStretch()
    
    def seleziona_prodotto(self, numero_tavolo: int, idx: int, prodotto: Prodotto):
        """Seleziona/deseleziona prodotto"""
        if self.prodotto_selezionato_idx == idx:
            # Deseleziona
            self.prodotto_selezionato_idx = None
            self.mostra_sezione_destra(None)
            # Aggiorna colore
            self.righe_ordinare_widget[idx].setStyleSheet("background-color: #34495e;")
        else:
            # Seleziona
            if self.prodotto_selezionato_idx is not None:
                # Deseleziona il precedente
                self.righe_ordinare_widget[self.prodotto_selezionato_idx].setStyleSheet("background-color: #34495e;")
            
            self.prodotto_selezionato_idx = idx
            self.righe_ordinare_widget[idx].setStyleSheet("background-color: #2980b9;")
            self.mostra_sezione_destra(prodotto)
    
    def aumenta_quantita(self, numero_tavolo: int, idx: int, prodotto: Prodotto):
        """Aumenta quantità prodotto in ordinare"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine and idx < len(ordine.righe_ordinare):
            ordine.righe_ordinare[idx].quantita += 1
            self.mostra_tab_ordinare(numero_tavolo)
            self.label_totale.setText(f"€{ordine.get_totale():.2f}")
    
    def diminuisci_quantita(self, numero_tavolo: int, idx: int):
        """Diminuisce quantità"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine and idx < len(ordine.righe_ordinare):
            if ordine.righe_ordinare[idx].quantita > 1:
                ordine.righe_ordinare[idx].quantita -= 1
            else:
                ordine.righe_ordinare.pop(idx)
            self.mostra_tab_ordinare(numero_tavolo)
            self.label_totale.setText(f"€{ordine.get_totale():.2f}")
    
    def conferma_ordine_final(self, numero_tavolo: int):
        """Conferma ordine: sposta prodotti da ordinare a ordinato"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        if not ordine.righe_ordinare:
            QMessageBox.warning(self, "Errore", "Non ci sono prodotti da ordinare!")
            return
        
        # Sposta i prodotti da ordinare a ordinato
        ordine.righe_ordinato.extend(ordine.righe_ordinare)
        
        # Svuota la lista ordinare
        ordine.righe_ordinare.clear()
        
        # Cambia stato
        ordine.stato = StatoOrdine.IN_PREPARAZIONE
        
        # Torna ai tavoli
        self.torna_a_tavoli()
    
    def mostra_dialogo_nota_cucina(self, numero_tavolo: int):
        """Dialog per nota cucina"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nota Cucina")
        dialog.setGeometry(300, 300, 500, 250)
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout()
        
        title = QLabel("📝 Nota Cucina")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        text_edit = QTextEdit()
        text_edit.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                padding: 10px;
                border: 2px solid #3498db;
                border-radius: 6px;
                background-color: white;
            }
        """)
        text_edit.setPlaceholderText("Es: Senza sale, ben cotto, con salsa a parte...")
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setMinimumHeight(40)
        btn_annulla.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_annulla.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_annulla)
        
        btn_ok = QPushButton("✓ Salva")
        btn_ok.setMinimumHeight(40)
        btn_ok.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_ok.clicked.connect(lambda: self.salva_nota_cucina(dialog, numero_tavolo, text_edit.toPlainText()))
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def salva_nota_cucina(self, dialog: QDialog, numero_tavolo: int, nota: str):
        """Salva nota cucina"""
        if nota.strip():
            QMessageBox.information(self, "Nota Aggiunta", f"Nota cucina salvata:\n\n{nota}")
            dialog.accept()
        else:
            QMessageBox.warning(self, "Errore", "Scrivi una nota!")
    
    def cambia_categoria(self, categoria: str, numero_tavolo: int):
        """Cambia categoria E salva quale categoria è attuale"""
        self.categoria_attuale = categoria
        self.mostra_prodotti_card(categoria, numero_tavolo)
    
    def mostra_schermata_riepilogo(self, numero_tavolo: int):
        """Riepilogo ordine come schermata intera"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        
        if ordine.is_vuoto():
            QMessageBox.warning(self, "Errore", "L'ordine è vuoto!")
            return
        
        widget = QWidget()
        self.setCentralWidget(widget)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # HEADER
        header = QLabel("📋 RIEPILOGO ORDINE")
        header.setStyleSheet("font-size: 26px; font-weight: bold; padding: 20px; background-color: #34495e; color: white;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # DETTAGLI
        details_layout = QHBoxLayout()
        details_layout.setContentsMargins(20, 15, 20, 15)
        details_layout.setSpacing(20)
        
        tavolo_info = QLabel(f"Tavolo: {numero_tavolo}\nPersone: {ordine.numero_persone}")
        tavolo_info.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px; background-color: #ecf0f1; border-radius: 8px;")
        details_layout.addWidget(tavolo_info)
        
        details_layout.addStretch()
        
        layout.addLayout(details_layout)
        
        # TABELLA PRODOTTI
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        table_layout = QVBoxLayout(container)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(1)  # 1px di spazio
        
        self.righe_widget = {}
        self.prodotto_selezionato = None  # Traccia selezione
        
        for i, riga in enumerate(ordine.righe):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(10, 3, 10, 3)  # Ridotto da 10, 6
            row_layout.setSpacing(15)
            
            nome_btn = QPushButton(riga.prodotto.nome)
            nome_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    border: 2px solid #2c3e50;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover { background-color: #2c3e50; }
            """)
            nome_btn.setMinimumHeight(35)
            nome_btn.clicked.connect(lambda checked, idx=i, w=row_widget: self.seleziona_riga_ordine(idx, w))
            row_layout.addWidget(nome_btn, 1)
            
            qtd_label = QLabel(f"x{riga.quantita}")
            qtd_label.setStyleSheet("font-size: 16px; font-weight: bold; min-width: 50px; text-align: center;")
            row_layout.addWidget(qtd_label)
            
            prezzo_label = QLabel(f"€{riga.prodotto.prezzo:.2f}")
            prezzo_label.setStyleSheet("font-size: 14px; font-weight: bold; min-width: 80px; text-align: center;")
            row_layout.addWidget(prezzo_label)
            
            subtot_label = QLabel(f"€{riga.get_subtotale():.2f}")
            subtot_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; min-width: 90px; text-align: center;")
            row_layout.addWidget(subtot_label)
            
            btn_plus = QPushButton("+")
            btn_plus.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: bold;
                    min-width: 45px;
                    min-height: 45px;
                }
                QPushButton:hover { background-color: #229954; }
            """)
            btn_plus.clicked.connect(lambda checked, idx=i: self.aumenta_quantita_riepilogo(numero_tavolo, idx))
            row_layout.addWidget(btn_plus)
            
            btn_minus = QPushButton("-")
            btn_minus.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 18px;
                    font-weight: bold;
                    min-width: 45px;
                    min-height: 45px;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            btn_minus.clicked.connect(lambda checked, idx=i: self.diminuisci_quantita_riepilogo(numero_tavolo, idx))
            row_layout.addWidget(btn_minus)
            
            row_widget.setLayout(row_layout)
            row_widget.setStyleSheet("background-color: white; border: 1px solid #ecf0f1; border-radius: 8px;")
            
            self.righe_widget[i] = row_widget
            table_layout.addWidget(row_widget)
        
        container.setLayout(table_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        
        # TOTALE
        totale_label = QLabel(f"TOTALE: €{ordine.get_totale():.2f}")
        totale_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; padding: 20px; background-color: #27ae60;")
        totale_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(totale_label)
        
        # PULSANTI
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(15, 15, 15, 15)
        btn_layout.setSpacing(15)
        
        btn_indietro = QPushButton("← Indietro")
        btn_indietro.setMinimumHeight(60)
        btn_indietro.setStyleSheet("background-color: #95a5a6; font-size: 16px;")
        btn_indietro.clicked.connect(lambda: self.mostra_schermata_ordine(numero_tavolo))
        btn_layout.addWidget(btn_indietro)
        
        btn_nota = QPushButton("📝 Nota Cucina")
        btn_nota.setMinimumHeight(60)
        btn_nota.setStyleSheet("background-color: #f39c12; font-size: 16px;")
        btn_nota.clicked.connect(lambda: self.mostra_dialogo_nota_cucina(numero_tavolo))
        btn_nota.hide()  # NASCONDI ALL'INIZIO
        btn_layout.addWidget(btn_nota)
        
        btn_layout.addStretch()
        
        btn_conferma = QPushButton("✓ CONFERMA ORDINE")
        btn_conferma.setMinimumHeight(60)
        btn_conferma.setMinimumWidth(200)
        btn_conferma.setStyleSheet("background-color: #27ae60; font-size: 16px;")
        btn_conferma.clicked.connect(lambda: self.conferma_ordine_finale(numero_tavolo))
        btn_layout.addWidget(btn_conferma)
        
        layout.addLayout(btn_layout)
        
        self.tavolo_riepilogo = numero_tavolo
        self.btn_nota_cucina = btn_nota  # Salva il bottone
        self.btn_layout_riepilogo = btn_layout  # Salva il layout
    
    def seleziona_riga_ordine(self, indice: int, widget: QWidget):
        """Seleziona/deseleziona riga ordine al click"""
        # Se è già selezionato, deseleziona
        if self.prodotto_selezionato == indice:
            widget.setStyleSheet("background-color: white; border: 1px solid #ecf0f1; border-radius: 8px;")
            self.prodotto_selezionato = None
            self.btn_nota_cucina.hide()
        else:
            # Deseleziona tutte le altre
            for w in self.righe_widget.values():
                w.setStyleSheet("background-color: white; border: 1px solid #ecf0f1; border-radius: 8px;")
            
            # Seleziona questa
            widget.setStyleSheet("background-color: #d5f4e6; border: 3px solid #27ae60; border-radius: 8px;")
            self.prodotto_selezionato = indice
            
            # Mostra nota cucina
            self.btn_nota_cucina.show()
    
    def deseleziona_tutti(self):
        """Deseleziona tutti i prodotti e nascondi nota cucina"""
        for w in self.righe_widget.values():
            w.setStyleSheet("background-color: white; border: 1px solid #ecf0f1; border-radius: 8px;")
        self.prodotto_selezionato = None
        self.btn_nota_cucina.hide()
    
    def aumenta_quantita_riepilogo(self, numero_tavolo: int, indice: int):
        """Aumenta quantità dal riepilogo"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine and indice < len(ordine.righe):
            ordine.righe[indice].quantita += 1
            self.mostra_schermata_riepilogo(numero_tavolo)
    
    def diminuisci_quantita_riepilogo(self, numero_tavolo: int, indice: int):
        """Diminuisce quantità dal riepilogo"""
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine and indice < len(ordine.righe):
            if ordine.righe[indice].quantita > 1:
                ordine.righe[indice].quantita -= 1
            else:
                ordine.righe.pop(indice)
            self.mostra_schermata_riepilogo(numero_tavolo)
    
    def mostra_dialogo_nota_cucina(self, numero_tavolo: int):
        """Dialog per nota cucina"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nota Cucina")
        dialog.setGeometry(300, 300, 600, 300)
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout()
        
        title = QLabel("📝 Aggiungi nota per la cucina")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 15px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        text_edit = QTextEdit()
        text_edit.setStyleSheet("""
            QTextEdit {
                font-size: 14px;
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
            }
        """)
        text_edit.setPlaceholderText("Es: Senza sale, ben cotto, con salsa a parte...")
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setMinimumHeight(50)
        btn_annulla.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_annulla.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_annulla)
        
        btn_ok = QPushButton("✓ Aggiungi")
        btn_ok.setMinimumHeight(50)
        btn_ok.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_ok.clicked.connect(lambda: self.salva_nota_cucina(dialog, numero_tavolo, text_edit.toPlainText()))
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def salva_nota_cucina(self, dialog: QDialog, numero_tavolo: int, nota: str):
        """Salva nota cucina"""
        if nota.strip():
            QMessageBox.information(self, "Nota Aggiunta", f"Nota cucina:\n\n{nota}")
            dialog.accept()
        else:
            QMessageBox.warning(self, "Errore", "Scrivi una nota!")
    
    def conferma_ordine_finale(self, numero_tavolo: int):
        """Conferma ordine e torna ai tavoli"""
        self.gestione.cambia_stato_ordine(numero_tavolo, StatoOrdine.IN_PREPARAZIONE)
        
        # Se è ASPORTO
        if numero_tavolo == 0:
            ordine = self.gestione.get_ordine_attivo(0)
            if ordine:
                QMessageBox.information(self, "ASPORTO", f"Totale da pagare: €{ordine.get_totale():.2f}\n\nOrdine confermato!")
                self.gestione.libera_tavolo(0)
        
        self.torna_a_tavoli()
    
    def torna_a_tavoli(self):
        """Torna alla schermata tavoli"""
        # Se l'ordine attuale è vuoto, libera il tavolo
        if self.tavolo_attuale > 0:
            ordine = self.gestione.get_ordine_attivo(self.tavolo_attuale)
            if ordine and ordine.is_vuoto():
                self.gestione.libera_tavolo(self.tavolo_attuale)
        
        self.crea_schermata_principale()
        self.aggiorna_colori_tavoli()
    
    def aggiorna_colori_tavoli(self):
        """Aggiorna colori e info tavoli"""
        # Ricrea la schermata principale
        self.crea_schermata_principale()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("✓ Applicazione pronta\n")
    
    app = QApplication(sys.argv)
    finestra = InterfacciaMobile()
    finestra.show()
    
    sys.exit(app.exec_())