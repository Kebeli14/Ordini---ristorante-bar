#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GESTIONE ORDINI RISTORANTE - VERSIONE COMPLETA
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
        QMenu, QSizePolicy
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
        self.nota_cucina = ""
        self.ingredienti = ""
        self.in_attesa = False
        self.motivo_rifiuto = ""   # "" | "Annullato" | "Sostituzione Prodotto"

    def get_subtotale(self) -> float:
        # Se annullato il prezzo NON viene conteggiato
        if self.motivo_rifiuto == "Annullato":
            return 0.0
        return self.prodotto.prezzo * self.quantita

class Ordine:
    _contatore_id = 0

    def __init__(self, id_tavolo: int, numero_persone: int = 1):
        Ordine._contatore_id += 1
        self.id_ordine = Ordine._contatore_id
        self.id_tavolo = id_tavolo
        self.numero_persone = numero_persone
        self.righe_ordinare: List[RigaOrdine] = []
        self.righe_ordinato: List[RigaOrdine] = []
        self.stato = StatoOrdine.IN_SOSPESO
        self.data_creazione = datetime.now()

    def aggiungi_prodotto(self, prodotto: Prodotto, quantita: int = 1):
        self.righe_ordinare.append(RigaOrdine(prodotto, quantita))

    def get_totale(self) -> float:
        return sum(r.get_subtotale() for r in self.righe_ordinare) + \
               sum(r.get_subtotale() for r in self.righe_ordinato)

    def get_numero_articoli(self) -> int:
        return sum(r.quantita for r in self.righe_ordinare) + \
               sum(r.quantita for r in self.righe_ordinato)

    def cambia_stato(self, nuovo_stato: StatoOrdine):
        self.stato = nuovo_stato

    def is_vuoto(self) -> bool:
        return len(self.righe_ordinare) == 0 and len(self.righe_ordinato) == 0

class Tavolo:
    def __init__(self, numero_tavolo: int):
        self.numero_tavolo = numero_tavolo
        self.ordine_attivo: Optional[Ordine] = None
        self.occupato = False
        self.in_attesa = False

    def crea_nuovo_ordine(self, numero_persone: int = 1) -> Ordine:
        self.ordine_attivo = Ordine(self.numero_tavolo, numero_persone)
        self.occupato = True
        return self.ordine_attivo

    def chiudi_ordine(self) -> Optional[Ordine]:
        ordine = self.ordine_attivo
        self.ordine_attivo = None
        self.occupato = False
        self.in_attesa = False
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
            id_ordine INTEGER PRIMARY KEY AUTOINCREMENT, id_tavolo INTEGER,
            numero_persone INTEGER, stato TEXT, totale REAL, data_creazione TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS righe_ordini (
            id_riga INTEGER PRIMARY KEY AUTOINCREMENT, id_ordine INTEGER,
            id_prodotto INTEGER, quantita INTEGER, prezzo_unitario REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cronologia_pagamenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_tavolo INTEGER, numero_persone INTEGER,
            metodo_pagamento TEXT, totale REAL,
            data_ora TIMESTAMP, dettaglio_prodotti TEXT)''')
        self.connessione.commit()

    def _carica_menu(self):
        cursor = self.connessione.cursor()
        cursor.execute('SELECT COUNT(*) FROM prodotti')
        if cursor.fetchone()[0] == 0:
            categorie = ["Caffetteria","Bevande","Dolci","Panini","Pizze","Primi piatti","Cocktails","Birre"]
            for cat in categorie:
                try:
                    cursor.execute('INSERT INTO categorie (nome) VALUES (?)', (cat,))
                except: pass
            menu = [
                (1,"Caffè espresso","Caffetteria",1.00),(2,"Cappuccino","Caffetteria",1.50),
                (3,"Latte","Caffetteria",1.80),(4,"Macchiato","Caffetteria",1.20),(5,"Lungo","Caffetteria",1.00),
                (11,"Acqua naturale","Bevande",1.50),(12,"Acqua frizzante","Bevande",1.50),
                (13,"Coca Cola","Bevande",2.00),(14,"Sprite","Bevande",2.00),
                (15,"Aranciata","Bevande",2.00),(16,"Succo d'arancia","Bevande",2.50),
                (21,"Tiramisu","Dolci",5.00),(22,"Panna cotta","Dolci",4.50),
                (23,"Gelato","Dolci",3.50),(24,"Cheesecake","Dolci",5.50),(25,"Pannacotta al cioccolato","Dolci",4.50),
                (31,"Panino prosciutto e mozzarella","Panini",6.00),(32,"Panino mortadella","Panini",5.50),
                (33,"Panino porchetta","Panini",7.00),(34,"Panino pollo","Panini",6.50),(35,"Panino tonno","Panini",6.00),
                (41,"Margherita","Pizze",8.00),(42,"Quattro formaggi","Pizze",9.50),
                (43,"Diavola","Pizze",9.00),(44,"Carbonara","Pizze",10.00),
                (45,"Ortolana","Pizze",8.50),(46,"Hawaiana","Pizze",9.50),
                (51,"Spaghetti Carbonara","Primi piatti",9.00),(52,"Risotto ai funghi","Primi piatti",10.00),
                (53,"Penne Arrabbiata","Primi piatti",8.50),(54,"Lasagna","Primi piatti",10.50),
                (55,"Fettuccine Alfredo","Primi piatti",10.00),(56,"Ravioli ricotta e spinaci","Primi piatti",9.50),
                (61,"Mojito","Cocktails",7.00),(62,"Margarita","Cocktails",7.50),
                (63,"Piña Colada","Cocktails",8.00),(64,"Daiquiri","Cocktails",7.50),
                (65,"Cosmopolitan","Cocktails",8.00),(66,"Long Island","Cocktails",9.00),
                (71,"Birra bionda","Birre",3.50),(72,"Birra rossa","Birre",4.00),
                (73,"Birra scura","Birre",4.50),(74,"Birra artigianale IPA","Birre",5.00),(75,"Birra analcolica","Birre",2.50),
            ]
            cursor.executemany('INSERT INTO prodotti VALUES (?, ?, ?, ?)', menu)
            self.connessione.commit()

    def salva_pagamento_cronologia(self, numero_tavolo, numero_persone, metodo, totale, righe):
        dettaglio = " | ".join(
            f"{r.prodotto.nome} x{r.quantita} (€{r.get_subtotale():.2f})"
            + (f" [{r.motivo_rifiuto}]" if r.motivo_rifiuto else "")
            for r in righe
        )
        cursor = self.connessione.cursor()
        cursor.execute(
            '''INSERT INTO cronologia_pagamenti
               (numero_tavolo,numero_persone,metodo_pagamento,totale,data_ora,dettaglio_prodotti)
               VALUES (?,?,?,?,?,?)''',
            (numero_tavolo, numero_persone, metodo, totale, datetime.now().isoformat(), dettaglio))
        self.connessione.commit()

    def get_cronologia(self, limit=200):
        cursor = self.connessione.cursor()
        cursor.execute(
            '''SELECT id,numero_tavolo,numero_persone,metodo_pagamento,
                      totale,data_ora,dettaglio_prodotti
               FROM cronologia_pagamenti ORDER BY data_ora DESC LIMIT ?''', (limit,))
        return cursor.fetchall()

    def get_statistiche_giornaliere(self):
        cursor = self.connessione.cursor()
        oggi = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            '''SELECT COUNT(*) as num_ordini,
                 COALESCE(SUM(totale),0) as totale_giorno,
                 COALESCE(SUM(numero_persone),0) as tot_persone,
                 COALESCE(SUM(CASE WHEN metodo_pagamento='Contanti' THEN totale ELSE 0 END),0) as tot_contanti,
                 COALESCE(SUM(CASE WHEN metodo_pagamento='Carta' THEN totale ELSE 0 END),0) as tot_carta
               FROM cronologia_pagamenti WHERE data_ora LIKE ?''', (f"{oggi}%",))
        row = cursor.fetchone()
        return {'num_ordini':row[0],'totale_giorno':row[1],'tot_persone':row[2],'tot_contanti':row[3],'tot_carta':row[4]}

    def get_prodotti_per_categoria(self, categoria):
        cursor = self.connessione.cursor()
        cursor.execute('SELECT * FROM prodotti WHERE categoria=? ORDER BY nome', (categoria,))
        return [Prodotto(r[0],r[1],r[2],r[3]) for r in cursor.fetchall()]

    def get_categorie(self):
        cursor = self.connessione.cursor()
        cursor.execute('SELECT nome FROM categorie ORDER BY nome')
        return [r[0] for r in cursor.fetchall()]

    def cerca_prodotti(self, termine):
        cursor = self.connessione.cursor()
        cursor.execute('SELECT * FROM prodotti WHERE nome LIKE ? ORDER BY nome', (f"%{termine}%",))
        return [Prodotto(r[0],r[1],r[2],r[3]) for r in cursor.fetchall()]

    def salva_ordine(self, ordine):
        try:
            cursor = self.connessione.cursor()
            cursor.execute(
                'INSERT INTO ordini (id_tavolo,numero_persone,stato,totale,data_creazione) VALUES (?,?,?,?,?)',
                (ordine.id_tavolo,ordine.numero_persone,ordine.stato.value,ordine.get_totale(),ordine.data_creazione.isoformat()))
            self.connessione.commit()
            return True
        except Exception as e:
            print(f"Errore: {e}")
            return False

    def get_all_products(self):
        cursor = self.connessione.cursor()
        cursor.execute('SELECT id_prodotto,nome,categoria,prezzo FROM prodotti ORDER BY categoria,nome')
        return [Prodotto(r[0],r[1],r[2],r[3]) for r in cursor.fetchall()]

    def add_product(self, nome, categoria, prezzo):
        cursor = self.connessione.cursor()
        cursor.execute('INSERT INTO prodotti (nome,categoria,prezzo) VALUES (?,?,?)', (nome,categoria,prezzo))
        self.connessione.commit()

    def delete_product(self, id_prodotto):
        cursor = self.connessione.cursor()
        cursor.execute('DELETE FROM prodotti WHERE id_prodotto=?', (id_prodotto,))
        self.connessione.commit()

    def add_or_update_product(self, id_prod, nome, categoria, prezzo):
        cursor = self.connessione.cursor()
        cursor.execute('INSERT OR REPLACE INTO prodotti (id_prodotto,nome,categoria,prezzo) VALUES (?,?,?,?)',
                       (id_prod,nome,categoria,prezzo))
        self.connessione.commit()

    def add_category(self, nome_categoria):
        try:
            cursor = self.connessione.cursor()
            cursor.execute('INSERT INTO categorie (nome) VALUES (?)', (nome_categoria,))
            self.connessione.commit()
        except: pass

    def delete_category(self, categoria):
        cursor = self.connessione.cursor()
        cursor.execute('DELETE FROM prodotti WHERE categoria=?', (categoria,))
        self.connessione.commit()

    def chiudi(self):
        self.connessione.close()

# ============================================================================
# GESTIONE ORDINI
# ============================================================================

class GestioneOrdini:
    def __init__(self, numero_tavoli=30):
        self.tavoli: Dict[int, Tavolo] = {i: Tavolo(i) for i in range(0, numero_tavoli+1)}
        self.db = DatabaseOrdini()

    def get_tavolo(self, numero_tavolo):
        return self.tavoli.get(numero_tavolo)

    def get_tutti_tavoli(self):
        return sorted([t for t in self.tavoli.values() if t.numero_tavolo > 0], key=lambda t: t.numero_tavolo)

    def crea_ordine(self, numero_tavolo, numero_persone=1):
        tavolo = self.get_tavolo(numero_tavolo)
        if tavolo and not tavolo.occupato:
            return tavolo.crea_nuovo_ordine(numero_persone)
        return None

    def libera_tavolo(self, numero_tavolo):
        tavolo = self.get_tavolo(numero_tavolo)
        if tavolo:
            ordine = tavolo.chiudi_ordine()
            if ordine and not ordine.is_vuoto():
                self.db.salva_ordine(ordine)
            return ordine
        return None

    def get_ordine_attivo(self, numero_tavolo):
        tavolo = self.get_tavolo(numero_tavolo)
        return tavolo.ordine_attivo if tavolo else None

    def aggiungi_al_ordine(self, numero_tavolo, prodotto, quantita=1):
        ordine = self.get_ordine_attivo(numero_tavolo)
        if ordine:
            ordine.aggiungi_prodotto(prodotto, quantita)
            return True
        return False

    def get_categoria_prodotti(self, categoria):
        return self.db.get_prodotti_per_categoria(categoria)

    def get_tutti_prodotti(self):
        return self.db.get_all_products()

    def get_categorie(self):
        return self.db.get_categorie()

    def cerca_prodotti(self, termine):
        return self.db.cerca_prodotti(termine)

    def cambia_stato_ordine(self, numero_tavolo, nuovo_stato):
        ordine = self.get_ordine_attivo(numero_tavolo)
        if ordine:
            ordine.cambia_stato(nuovo_stato)
            self.db.salva_ordine(ordine)
            return True
        return False

    def sposta_ordine(self, da_tavolo, a_tavolo):
        t_origine = self.get_tavolo(da_tavolo)
        t_dest = self.get_tavolo(a_tavolo)
        if not t_origine or not t_dest:
            return False
        if not t_origine.ordine_attivo or t_dest.occupato:
            return False
        t_dest.ordine_attivo = t_origine.ordine_attivo
        t_dest.ordine_attivo.id_tavolo = a_tavolo
        t_dest.occupato = True
        t_dest.in_attesa = t_origine.in_attesa
        t_origine.ordine_attivo = None
        t_origine.occupato = False
        t_origine.in_attesa = False
        return True

    def unisci_tavoli(self, tavolo1, tavolo2):
        t1 = self.get_tavolo(tavolo1)
        t2 = self.get_tavolo(tavolo2)
        if not t1 or not t2:
            return False
        if not t1.ordine_attivo or not t2.ordine_attivo:
            return False
        t1.ordine_attivo.righe_ordinare += t2.ordine_attivo.righe_ordinare
        t1.ordine_attivo.righe_ordinato += t2.ordine_attivo.righe_ordinato
        t1.ordine_attivo.numero_persone += t2.ordine_attivo.numero_persone
        t2.ordine_attivo = None
        t2.occupato = False
        t2.in_attesa = False
        return True

# ============================================================================
# INTERFACCIA PRINCIPALE
# ============================================================================

class InterfacciaMobile(QMainWindow):
    def __init__(self):
        super().__init__()
        self.gestione = GestioneOrdini(numero_tavoli=30)
        self.tavolo_attuale = 0
        self.categoria_attuale = ""
        self.prodotto_selezionato_idx = None
        self.prodotto_selezionato_ordinato_idx = None
        self.setWindowTitle("Gestione Ordini")
        self.setGeometry(0, 0, 1080, 1920)
        self.configura_stili()
        self.crea_schermata_principale()

    def configura_stili(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QPushButton { background-color: #3498db; color: white; border: none;
                          border-radius: 8px; padding: 12px; font-size: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
            QLineEdit { font-size: 14px; padding: 10px; border: 2px solid #bdc3c7; border-radius: 8px; }
        """)

    # =========================================================================
    # SCHERMATA TAVOLI
    # =========================================================================

    def crea_schermata_principale(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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
            tw = QWidget()
            tl = QVBoxLayout(tw)
            tl.setContentsMargins(0, 0, 0, 0)
            tl.setSpacing(0)

            btn = QPushButton(f"Tavolo {tavolo.numero_tavolo}")
            btn.setMinimumHeight(100)
            btn.setFont(QFont("Arial", 14, QFont.Bold))

            if tavolo.in_attesa:
                btn.setStyleSheet("background-color: #e74c3c; color: white; border: none; border-radius: 8px 8px 0px 0px; padding: 12px;")
            elif tavolo.occupato:
                btn.setStyleSheet("background-color: #f39c12; color: white; border: none; border-radius: 8px 8px 0px 0px; padding: 12px;")
            else:
                btn.setStyleSheet("background-color: #3498db; color: white; border: none; border-radius: 8px 8px 0px 0px; padding: 12px;")

            btn.clicked.connect(lambda checked, num=tavolo.numero_tavolo: self.clicca_tavolo(num))
            tl.addWidget(btn)

            info_widget = QWidget()
            info_layout = QHBoxLayout(info_widget)
            info_layout.setContentsMargins(8, 5, 8, 5)
            info_layout.setSpacing(0)

            if tavolo.in_attesa:
                info_widget.setStyleSheet("background-color: #e74c3c; border-radius: 0px 0px 8px 8px;")
                if tavolo.ordine_attivo:
                    p = QLabel(str(tavolo.ordine_attivo.numero_persone))
                    p.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                    info_layout.addWidget(p)
                    info_layout.addStretch()
                    pr = QLabel(f"€{tavolo.ordine_attivo.get_totale():.2f}")
                    pr.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                    info_layout.addWidget(pr)
            elif tavolo.occupato and tavolo.ordine_attivo:
                info_widget.setStyleSheet("background-color: #f39c12; border-radius: 0px 0px 8px 8px;")
                p = QLabel(str(tavolo.ordine_attivo.numero_persone))
                p.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                info_layout.addWidget(p)
                info_layout.addStretch()
                pr = QLabel(f"€{tavolo.ordine_attivo.get_totale():.2f}")
                pr.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                info_layout.addWidget(pr)
            else:
                info_widget.setStyleSheet("background-color: #3498db; border-radius: 0px 0px 8px 8px;")
                info_layout.addStretch()

            info_widget.setLayout(info_layout)
            tl.addWidget(info_widget)
            tw.setLayout(tl)
            tw.setMinimumHeight(120)
            tw.setMinimumWidth(120)
            self.pulsanti_tavoli[tavolo.numero_tavolo] = btn
            grid_tavoli.addWidget(tw, i // 3, i % 3)

        scroll.setWidget(widget_tavoli)
        layout.addWidget(scroll)

    def clicca_tavolo(self, numero_tavolo: int):
        self.tavolo_attuale = numero_tavolo
        tavolo = self.gestione.get_tavolo(numero_tavolo)
        if tavolo.occupato:
            self.mostra_schermata_ordine(numero_tavolo, tab_ordinato=True)
        else:
            self.mostra_overlay_persone(numero_tavolo)

    def ordina_asporto(self):
        self.gestione.crea_ordine(0, 1)
        self.mostra_schermata_ordine(0)

    def mostra_overlay_persone(self, numero_tavolo: int):
        self.overlay = QWidget(self)
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setStyleSheet("background-color: rgba(0,0,0,0.5);")

        pw, ph = 700, 400
        pannello = QWidget(self.overlay)
        pannello.setGeometry((self.width()-pw)//2, (self.height()-ph)//2, pw, ph)
        pannello.setStyleSheet("background-color: #f5f5f5; border-radius: 15px;")

        layout = QVBoxLayout(pannello)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        titolo = QLabel(f"Tavolo {numero_tavolo}")
        titolo.setStyleSheet("font-size: 32px; font-weight: bold; color: #34495e;")
        titolo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titolo)

        domanda = QLabel("Quante persone?")
        domanda.setStyleSheet("font-size: 22px; color: #2c3e50;")
        domanda.setAlignment(Qt.AlignCenter)
        layout.addWidget(domanda)

        tastiera_layout = QGridLayout()
        tastiera_layout.setSpacing(10)
        for i in range(1, 11):
            btn = QPushButton(str(i))
            btn.setMinimumHeight(70)
            btn.setMinimumWidth(70)
            btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; border-radius: 10px; font-size: 20px; font-weight: bold; } QPushButton:hover { background-color: #2980b9; }")
            btn.clicked.connect(lambda checked, n=i, t=numero_tavolo: self.conferma_persone(n, t))
            tastiera_layout.addWidget(btn, (i-1)//5, (i-1)%5)
        layout.addLayout(tastiera_layout)
        layout.addStretch()

        self.overlay.mousePressEvent = lambda e: self.chiudi_overlay()
        pannello.mousePressEvent = lambda e: None
        self.overlay.show()

    def conferma_persone(self, numero_persone: int, numero_tavolo: int):
        self.chiudi_overlay()
        self.gestione.crea_ordine(numero_tavolo, numero_persone)
        self.aggiorna_colori_tavoli()
        self.mostra_schermata_ordine(numero_tavolo)

    def chiudi_overlay(self):
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.deleteLater()
            self.overlay = None

    def chiudi_tavolo(self, numero_tavolo: int):
        self.gestione.libera_tavolo(numero_tavolo)
        self.aggiorna_colori_tavoli()
        self.torna_a_tavoli()

    # =========================================================================
    # SCHERMATA ORDINE
    # =========================================================================

    def mostra_schermata_ordine(self, numero_tavolo: int, tab_ordinato: bool = False):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        ordine = self.gestione.get_ordine_attivo(numero_tavolo)

        # ── HEADER TOP ───────────────────────────────────────────────────
        header_top = QHBoxLayout()
        header_top.setContentsMargins(15, 10, 15, 10)
        header_top.setSpacing(15)

        btn_back = QPushButton("←")
        btn_back.setMinimumHeight(40)
        btn_back.setMaximumWidth(50)
        btn_back.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
        btn_back.clicked.connect(self.torna_a_tavoli)
        header_top.addWidget(btn_back)
        header_top.addStretch()

        header_top_widget = QWidget()
        header_top_widget.setLayout(header_top)
        header_top_widget.setStyleSheet("background-color: #34495e;")
        header_top_widget.setFixedHeight(60)
        layout.addWidget(header_top_widget)

        # ── MAIN SPLIT ───────────────────────────────────────────────────
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── SINISTRA 1/3 ─────────────────────────────────────────────────
        sinistra_widget = QWidget()
        sinistra_widget.setStyleSheet("background-color: #2c3e50;")
        sinistra_layout = QVBoxLayout(sinistra_widget)
        sinistra_layout.setContentsMargins(10, 10, 10, 10)
        sinistra_layout.setSpacing(10)

        header_label = QLabel("📋 Ordine")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; padding: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        sinistra_layout.addWidget(header_label)

        info_label = QLabel(f"Tavolo: {numero_tavolo}\nPersone: {ordine.numero_persone}")
        info_label.setStyleSheet("font-size: 12px; color: white; padding: 8px; background-color: #34495e; border-radius: 6px;")
        info_label.setAlignment(Qt.AlignCenter)
        sinistra_layout.addWidget(info_label)

        # TAB Ordinato / Ordinare
        tab_button_layout = QHBoxLayout()
        tab_button_layout.setContentsMargins(0, 0, 0, 0)
        tab_button_layout.setSpacing(2)

        stile_ordinato_inattivo = "QPushButton { background-color: #34495e; color: white; border: none; border-bottom: 3px solid #34495e; padding: 8px; font-size: 11px; font-weight: bold; border-radius: 4px 0px 0px 4px; } QPushButton:hover { background-color: #2c3e50; }"
        stile_ordinato_attivo   = "QPushButton { background-color: #34495e; color: white; border: none; border-bottom: 4px solid #f39c12; padding: 8px; font-size: 11px; font-weight: bold; border-radius: 4px 0px 0px 4px; } QPushButton:hover { background-color: #2c3e50; }"
        stile_ordinare_inattivo = "QPushButton { background-color: #3498db; color: white; border: none; border-bottom: 3px solid #3498db; padding: 8px; font-size: 11px; font-weight: bold; border-radius: 0px 4px 4px 0px; } QPushButton:hover { background-color: #2980b9; }"
        stile_ordinare_attivo   = "QPushButton { background-color: #3498db; color: white; border: none; border-bottom: 4px solid #f39c12; padding: 8px; font-size: 11px; font-weight: bold; border-radius: 0px 4px 4px 0px; } QPushButton:hover { background-color: #2980b9; }"

        btn_ordinato = QPushButton("✓ Ordinato")
        btn_ordinato.setStyleSheet(stile_ordinato_attivo if tab_ordinato else stile_ordinato_inattivo)
        btn_ordinato.setMinimumHeight(35)
        btn_ordinato.clicked.connect(lambda: self.cambia_tab_ordinato(numero_tavolo, btn_ordinato, btn_ordinare))
        tab_button_layout.addWidget(btn_ordinato, 1)

        btn_ordinare = QPushButton("+ Ordinare")
        btn_ordinare.setStyleSheet(stile_ordinare_attivo if not tab_ordinato else stile_ordinare_inattivo)
        btn_ordinare.setMinimumHeight(35)
        btn_ordinare.clicked.connect(lambda: self.cambia_tab_ordinare(numero_tavolo, btn_ordinato, btn_ordinare))
        tab_button_layout.addWidget(btn_ordinare, 1)

        self.btn_ordinato_tab = btn_ordinato
        self.btn_ordinare_tab = btn_ordinare
        self.stile_ordinato_attivo = stile_ordinato_attivo
        self.stile_ordinato_inattivo = stile_ordinato_inattivo
        self.stile_ordinare_attivo = stile_ordinare_attivo
        self.stile_ordinare_inattivo = stile_ordinare_inattivo

        sinistra_layout.addLayout(tab_button_layout)

        self.scroll_ordine = QScrollArea()
        self.scroll_ordine.setWidgetResizable(True)
        self.scroll_ordine.setStyleSheet("QScrollArea { border: none; background-color: #2c3e50; } QScrollBar:vertical { width: 6px; background-color: #34495e; } QScrollBar::handle:vertical { background-color: #95a5a6; border-radius: 3px; }")
        self.container_ordine = QWidget()
        self.container_ordine.setStyleSheet("background-color: #2c3e50;")
        self.layout_ordine = QVBoxLayout(self.container_ordine)
        self.layout_ordine.setContentsMargins(0, 0, 0, 0)
        self.layout_ordine.setSpacing(1)
        self.scroll_ordine.setWidget(self.container_ordine)
        sinistra_layout.addWidget(self.scroll_ordine, 1)

        totale = QLabel(f"€{ordine.get_totale():.2f}")
        totale.setStyleSheet("font-size: 22px; font-weight: bold; color: #27ae60; padding: 12px;")
        totale.setAlignment(Qt.AlignCenter)
        sinistra_layout.addWidget(totale)
        self.label_totale = totale

        self.btn_layout_ordini = QHBoxLayout()
        self.btn_layout_ordini.setSpacing(6)
        self.aggiorna_bottoni_ordini(numero_tavolo, tab_ordinato)
        sinistra_layout.addLayout(self.btn_layout_ordini)

        # ── DESTRA 2/3 ───────────────────────────────────────────────────
        destra_widget = QWidget()
        destra_widget.setStyleSheet("background-color: white;")
        destra_layout = QVBoxLayout(destra_widget)
        self.destra_layout = destra_layout
        destra_layout.setContentsMargins(0, 0, 0, 0)
        destra_layout.setSpacing(0)

        header_destra_layout = QHBoxLayout()
        header_destra_layout.setContentsMargins(15, 12, 15, 12)
        header_destra_layout.setSpacing(10)

        header_label2 = QLabel(f"Tavolo {numero_tavolo} ({ordine.numero_persone})")
        header_label2.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        header_destra_layout.addWidget(header_label2)
        header_destra_layout.addStretch()

        btn_ricerca = QPushButton("🔍")
        btn_ricerca.setMaximumWidth(45)
        btn_ricerca.setMinimumHeight(38)
        btn_ricerca.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 6px; font-size: 20px; font-weight: bold; } QPushButton:hover { background-color: #2980b9; }")
        btn_ricerca.clicked.connect(lambda: self.apri_popup_ricerca(numero_tavolo))
        header_destra_layout.addWidget(btn_ricerca)

        # ── BOTTONE 3 PUNTINI (ora con sposta/unisci/chiudi DENTRO il tavolo) ──
        btn_tre_puntini = QPushButton("⋮")
        btn_tre_puntini.setMaximumWidth(45)
        btn_tre_puntini.setMinimumHeight(38)
        btn_tre_puntini.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 6px; font-size: 20px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
        btn_tre_puntini.clicked.connect(lambda: self.mostra_menu_tre_puntini(numero_tavolo))
        header_destra_layout.addWidget(btn_tre_puntini)

        header_destra_widget = QWidget()
        header_destra_widget.setLayout(header_destra_layout)
        header_destra_widget.setStyleSheet("background-color: #34495e;")
        header_destra_widget.setFixedHeight(60)
        destra_layout.addWidget(header_destra_widget)

        menu_layout = QHBoxLayout()
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)

        # categorie
        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setMaximumWidth(90)
        cat_scroll.setStyleSheet("QScrollArea { border: none; background-color: #ecf0f1; }")
        cat_widget = QWidget()
        cat_layout = QVBoxLayout(cat_widget)
        cat_layout.setContentsMargins(5, 5, 5, 5)
        cat_layout.setSpacing(3)
        self.pulsanti_categorie = {}
        for categoria in self.gestione.get_categorie():
            btn = QPushButton(categoria)
            btn.setMinimumHeight(38)
            btn.setMaximumHeight(38)
            btn.setStyleSheet("QPushButton { background-color: #f39c12; color: white; border: none; border-radius: 5px; padding: 5px; font-size: 9px; font-weight: bold; } QPushButton:hover { background-color: #e67e22; }")
            btn.clicked.connect(lambda checked, cat=categoria, n=numero_tavolo: self.cambia_categoria(cat, n))
            cat_layout.addWidget(btn)
            self.pulsanti_categorie[categoria] = btn
        cat_layout.addStretch()
        cat_widget.setLayout(cat_layout)
        cat_scroll.setWidget(cat_widget)
        menu_layout.addWidget(cat_scroll)

        # prodotti
        self.scroll_prodotti = QScrollArea()
        self.scroll_prodotti.setWidgetResizable(True)
        self.scroll_prodotti.setStyleSheet("QScrollArea { border: none; background-color: white; }")
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

        # sezione destra
        self.sezione_destra_widget = QWidget()
        self.sezione_destra_widget.setStyleSheet("background-color: #ecf0f1; border-left: 2px solid #bdc3c7;")
        self.sezione_destra_widget.setMaximumWidth(250)
        self.sezione_destra_layout = QVBoxLayout(self.sezione_destra_widget)
        self.sezione_destra_layout.setContentsMargins(15, 15, 15, 15)
        self.sezione_destra_layout.setSpacing(10)
        lbl_vuoto = QLabel("Seleziona un prodotto")
        lbl_vuoto.setStyleSheet("color: #95a5a6; font-size: 12px; padding: 20px;")
        lbl_vuoto.setAlignment(Qt.AlignCenter)
        self.sezione_destra_layout.addWidget(lbl_vuoto)
        self.sezione_destra_layout.addStretch()
        destra_layout.addWidget(self.sezione_destra_widget)

        main_layout.addWidget(sinistra_widget, 1)
        main_layout.addWidget(destra_widget, 2)
        layout.addLayout(main_layout)

        self.tavolo_attuale = numero_tavolo
        self.categoria_attuale = "Bevande"
        self.note_prodotti = {}
        self.prodotto_selezionato_idx = None
        self.prodotto_selezionato_ordinato_idx = None
        QApplication.processEvents()

        if tab_ordinato:
            self.cambia_tab_ordinato(numero_tavolo, self.btn_ordinato_tab, self.btn_ordinare_tab)
        else:
            self.cambia_tab_ordinare(numero_tavolo, self.btn_ordinato_tab, self.btn_ordinare_tab)

        self.mostra_prodotti_card("Bevande", numero_tavolo)

    # ── MENU 3 PUNTINI (dentro il tavolo) ───────────────────────────────────
    def mostra_menu_tre_puntini(self, numero_tavolo: int):
        """Menu ⋮ con: Attesa prodotto, Sposta tavolo, Unisci tavolo, Chiudi tavolo"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: white; color: #2c3e50; border: 1px solid #bdc3c7; border-radius: 6px; }
            QMenu::item { padding: 10px 20px; font-size: 13px; }
            QMenu::item:selected { background-color: #3498db; color: white; }
            QMenu::separator { height: 1px; background-color: #bdc3c7; margin: 4px 0; }
        """)

        # -- prodotto in attesa (solo se c'è un prodotto selezionato in ordinare) --
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if self.prodotto_selezionato_idx is not None and ordine and \
                self.prodotto_selezionato_idx < len(ordine.righe_ordinare):
            riga = ordine.righe_ordinare[self.prodotto_selezionato_idx]
            if riga.in_attesa:
                act_attesa = menu.addAction("🔓 Sblocca Prodotto")
                act_attesa.triggered.connect(lambda: self.sblocca_prodotto(numero_tavolo, self.prodotto_selezionato_idx, True))
            else:
                act_attesa = menu.addAction("⏸️ Metti in Attesa")
                act_attesa.triggered.connect(lambda: self.metti_attesa(numero_tavolo, self.prodotto_selezionato_idx, True))
            menu.addSeparator()

        # -- se in ordinato e c'è un prodotto selezionato --
        if self.prodotto_selezionato_ordinato_idx is not None and ordine and \
                self.prodotto_selezionato_ordinato_idx < len(ordine.righe_ordinato):
            riga_ord = ordine.righe_ordinato[self.prodotto_selezionato_ordinato_idx]
            if riga_ord.in_attesa:
                act_sblocca = menu.addAction("🔓 Sblocca Prodotto Ordinato")
                act_sblocca.triggered.connect(lambda: self.sblocca_prodotto(numero_tavolo, self.prodotto_selezionato_ordinato_idx, False))
                menu.addSeparator()

        # -- azioni tavolo --
        act_sposta = menu.addAction("🔄 Sposta Tavolo")
        act_sposta.triggered.connect(lambda: self.apri_sposta_tavolo(numero_tavolo))

        act_unisci = menu.addAction("🔗 Unisci Tavolo")
        act_unisci.triggered.connect(lambda: self.apri_unisci_tavolo(numero_tavolo))

        menu.addSeparator()

        act_chiudi = menu.addAction("❌ Chiudi Tavolo")
        act_chiudi.triggered.connect(lambda: self.chiudi_tavolo_con_conferma(numero_tavolo))

        menu.exec_(QCursor.pos())

    def apri_sposta_tavolo(self, numero_tavolo: int):
        tavoli = [str(t.numero_tavolo) for t in self.gestione.get_tutti_tavoli() if not t.occupato]
        if not tavoli:
            QMessageBox.warning(self, "Errore", "Nessun tavolo libero disponibile!")
            return
        scelta, ok = QInputDialog.getItem(self, "Sposta Tavolo", "Seleziona tavolo di destinazione:", tavoli, 0, False)
        if ok:
            ok2 = self.gestione.sposta_ordine(numero_tavolo, int(scelta))
            if ok2:
                QMessageBox.information(self, "Successo", f"Ordine spostato al Tavolo {scelta}!")
                self.torna_a_tavoli()
            else:
                QMessageBox.warning(self, "Errore", "Impossibile spostare l'ordine!")

    def apri_unisci_tavolo(self, numero_tavolo: int):
        tavoli = [str(t.numero_tavolo) for t in self.gestione.get_tutti_tavoli() if t.occupato and t.numero_tavolo != numero_tavolo]
        if not tavoli:
            QMessageBox.warning(self, "Errore", "Nessun altro tavolo occupato!")
            return
        scelta, ok = QInputDialog.getItem(self, "Unisci Tavoli", "Seleziona tavolo da unire:", tavoli, 0, False)
        if ok:
            ok2 = self.gestione.unisci_tavoli(numero_tavolo, int(scelta))
            if ok2:
                QMessageBox.information(self, "Successo", f"Tavolo {scelta} unito al Tavolo {numero_tavolo}!")
                self.mostra_schermata_ordine(numero_tavolo, tab_ordinato=True)
            else:
                QMessageBox.warning(self, "Errore", "Impossibile unire i tavoli!")

    def chiudi_tavolo_con_conferma(self, numero_tavolo: int):
        reply = QMessageBox.question(self, "Chiudi Tavolo",
            f"Sei sicuro di voler chiudere il Tavolo {numero_tavolo}?\n\nL'ordine verrà perso!",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.chiudi_tavolo(numero_tavolo)

    # =========================================================================
    # BOTTONI ORDINE
    # =========================================================================

    def aggiorna_bottoni_ordini(self, numero_tavolo: int, tab_ordinato: bool):
        while self.btn_layout_ordini.count():
            child = self.btn_layout_ordini.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if tab_ordinato:
            btn_vuoto = QPushButton("🗑️ Vuoto")
            btn_vuoto.setMinimumHeight(45)
            btn_vuoto.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
            btn_vuoto.clicked.connect(lambda: self.mostra_motivo_rifiuto(numero_tavolo))
            self.btn_layout_ordini.addWidget(btn_vuoto)

            btn_pagare = QPushButton("💳 Pagare")
            btn_pagare.setMinimumHeight(45)
            btn_pagare.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
            btn_pagare.clicked.connect(lambda: self.paga_ordine(numero_tavolo))
            self.btn_layout_ordini.addWidget(btn_pagare)
        else:
            btn_conf = QPushButton("✓ Conferma")
            btn_conf.setMinimumHeight(45)
            btn_conf.setStyleSheet("QPushButton { background-color: #27ae60; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #229954; }")
            btn_conf.clicked.connect(lambda: self.conferma_ordine_final(numero_tavolo))
            self.btn_layout_ordini.addWidget(btn_conf)

    # =========================================================================
    # TAB ORDINARE / ORDINATO
    # =========================================================================

    def cambia_tab_ordinato(self, numero_tavolo, btn_ordinato, btn_ordinare):
        btn_ordinato.setStyleSheet(self.stile_ordinato_attivo)
        btn_ordinare.setStyleSheet(self.stile_ordinare_inattivo)
        self.mostra_tab_ordinato(numero_tavolo)
        self.aggiorna_bottoni_ordini(numero_tavolo, True)

    def cambia_tab_ordinare(self, numero_tavolo, btn_ordinato, btn_ordinare):
        btn_ordinato.setStyleSheet(self.stile_ordinato_inattivo)
        btn_ordinare.setStyleSheet(self.stile_ordinare_attivo)
        self.mostra_tab_ordinare(numero_tavolo)
        self.aggiorna_bottoni_ordini(numero_tavolo, False)

    def mostra_tab_ordinare(self, numero_tavolo: int):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        while self.layout_ordine.count():
            child = self.layout_ordine.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        self.righe_ordinare_widget = {}
        self.prodotto_selezionato_idx = None

        for i, riga in enumerate(ordine.righe_ordinare):
            container = QWidget()
            cl = QVBoxLayout(container)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(0)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(8)

            nome_testo = f"⏸️ {riga.prodotto.nome}" if riga.in_attesa else riga.prodotto.nome
            nome = QLabel(nome_testo)
            nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
            nome.mousePressEvent = lambda e, idx=i, p=riga.prodotto: self.seleziona_prodotto(numero_tavolo, idx, p)
            row_layout.addWidget(nome, 1)

            qtd = QLabel(f"x{riga.quantita}")
            qtd.setStyleSheet("color: white; font-size: 12px; font-weight: bold; min-width: 28px;")
            row_layout.addWidget(qtd)

            btn_minus = QPushButton("-")
            btn_minus.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 14px; font-weight: bold; min-width: 25px; min-height: 25px; } QPushButton:hover { background-color: #c0392b; }")
            btn_minus.clicked.connect(lambda checked, idx=i: self.diminuisci_quantita(numero_tavolo, idx))
            row_layout.addWidget(btn_minus)

            btn_plus = QPushButton("+")
            btn_plus.setStyleSheet("QPushButton { background-color: #27ae60; color: white; border: none; border-radius: 4px; font-size: 14px; font-weight: bold; min-width: 25px; min-height: 25px; } QPushButton:hover { background-color: #229954; }")
            btn_plus.clicked.connect(lambda checked, idx=i, p=riga.prodotto: self.aumenta_quantita(numero_tavolo, idx, p))
            row_layout.addWidget(btn_plus)

            prezzo = QLabel(f"€{riga.get_subtotale():.2f}")
            prezzo.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; min-width: 60px;")
            row_layout.addWidget(prezzo)

            row_widget.setLayout(row_layout)
            row_widget.setStyleSheet("background-color: #34495e;")
            cl.addWidget(row_widget)

            if riga.nota_cucina.strip():
                n_lbl = QLabel(f"📝 {riga.nota_cucina}")
                n_lbl.setStyleSheet("color: #3498db; font-size: 10px; padding: 4px 8px; background-color: #2c3e50;")
                n_lbl.setWordWrap(True)
                cl.addWidget(n_lbl)

            if riga.ingredienti.strip():
                i_lbl = QLabel(f"🥘 {riga.ingredienti}")
                i_lbl.setStyleSheet("color: #f39c12; font-size: 10px; padding: 4px 8px; background-color: #2c3e50;")
                i_lbl.setWordWrap(True)
                cl.addWidget(i_lbl)

            container.setLayout(cl)
            self.layout_ordine.addWidget(container)
            self.righe_ordinare_widget[i] = container

        self.layout_ordine.addStretch()

    def mostra_tab_ordinato(self, numero_tavolo: int):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        while self.layout_ordine.count():
            child = self.layout_ordine.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if not ordine or not ordine.righe_ordinato:
            lbl = QLabel("Nessun ordine confermato")
            lbl.setStyleSheet("color: #95a5a6; font-size: 11px; padding: 20px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.layout_ordine.addWidget(lbl)
            self.layout_ordine.addStretch()
            return

        for i, riga in enumerate(ordine.righe_ordinato):
            container = QWidget()
            cl = QVBoxLayout(container)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(2)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(10)

            nome_testo = f"⏸️ {riga.prodotto.nome}" if riga.in_attesa else riga.prodotto.nome
            nome = QLabel(nome_testo)

            selezionato = (hasattr(self, 'prodotto_selezionato_ordinato_idx') and
                           self.prodotto_selezionato_ordinato_idx == i)
            if selezionato:
                nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background-color: #3498db; padding: 4px; border-radius: 3px;")
                row_widget.setStyleSheet("background-color: #2980b9;")
            else:
                # se annullato, mostra grigio
                if riga.motivo_rifiuto == "Annullato":
                    nome.setStyleSheet("color: #95a5a6; font-size: 12px; font-weight: bold; text-decoration: line-through;")
                    row_widget.setStyleSheet("background-color: #34495e;")
                else:
                    nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
                    row_widget.setStyleSheet("background-color: #34495e;")

            nome.mousePressEvent = lambda e, idx=i: self.seleziona_prodotto_ordinato(numero_tavolo, idx)
            row_layout.addWidget(nome, 1)

            qtd = QLabel(f"x{riga.quantita}")
            qtd.setStyleSheet("color: white; font-size: 12px; font-weight: bold; min-width: 28px;")
            row_layout.addWidget(qtd)

            # prezzo: barrato se annullato
            prezzo_str = f"€{riga.get_subtotale():.2f}"
            prezzo = QLabel(prezzo_str)
            if riga.motivo_rifiuto == "Annullato":
                prezzo.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold; min-width: 60px; text-decoration: line-through;")
            else:
                prezzo.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; min-width: 60px;")
            row_layout.addWidget(prezzo)

            row_widget.setLayout(row_layout)
            cl.addWidget(row_widget)

            if riga.in_attesa:
                al = QLabel("⏸️ In Attesa")
                al.setStyleSheet("color: #e74c3c; font-size: 10px; font-weight: bold; padding: 4px 8px; background-color: #2c3e50;")
                cl.addWidget(al)

            if riga.motivo_rifiuto.strip():
                ml = QLabel(f"❌ {riga.motivo_rifiuto}")
                ml.setStyleSheet("color: #e74c3c; font-size: 10px; font-weight: bold; padding: 4px 8px; background-color: #2c3e50;")
                cl.addWidget(ml)

            if riga.nota_cucina.strip():
                nl = QLabel(f"📝 {riga.nota_cucina}")
                nl.setStyleSheet("color: #3498db; font-size: 10px; padding: 4px 8px; background-color: #2c3e50;")
                nl.setWordWrap(True)
                cl.addWidget(nl)

            if riga.ingredienti.strip():
                il = QLabel(f"🥘 {riga.ingredienti}")
                il.setStyleSheet("color: #f39c12; font-size: 10px; padding: 4px 8px; background-color: #2c3e50;")
                il.setWordWrap(True)
                cl.addWidget(il)

            container.setLayout(cl)
            self.layout_ordine.addWidget(container)

        self.layout_ordine.addStretch()

    # =========================================================================
    # SELEZIONE PRODOTTI
    # =========================================================================

    def seleziona_prodotto(self, numero_tavolo: int, idx: int, prodotto: Prodotto):
        if self.prodotto_selezionato_idx == idx:
            self.prodotto_selezionato_idx = None
            self.mostra_sezione_destra(None)
            if idx in self.righe_ordinare_widget:
                self.righe_ordinare_widget[idx].setStyleSheet("background-color: #34495e;")
        else:
            if self.prodotto_selezionato_idx is not None and self.prodotto_selezionato_idx in self.righe_ordinare_widget:
                self.righe_ordinare_widget[self.prodotto_selezionato_idx].setStyleSheet("background-color: #34495e;")
            self.prodotto_selezionato_idx = idx
            if idx in self.righe_ordinare_widget:
                self.righe_ordinare_widget[idx].setStyleSheet("background-color: #2980b9;")
            self.mostra_sezione_destra(prodotto)

    def seleziona_prodotto_ordinato(self, numero_tavolo: int, idx: int):
        if not hasattr(self, 'prodotto_selezionato_ordinato_idx'):
            self.prodotto_selezionato_ordinato_idx = None
        self.prodotto_selezionato_ordinato_idx = None if self.prodotto_selezionato_ordinato_idx == idx else idx
        self.mostra_tab_ordinato(numero_tavolo)

    # =========================================================================
    # MOTIVO RIFIUTO (prezzo detratto automaticamente)
    # =========================================================================

    def mostra_motivo_rifiuto(self, numero_tavolo: int):
        if not hasattr(self, 'prodotto_selezionato_ordinato_idx') or self.prodotto_selezionato_ordinato_idx is None:
            QMessageBox.warning(self, "Errore", "Seleziona prima un prodotto nel TAB Ordinato!")
            return
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if self.prodotto_selezionato_ordinato_idx >= len(ordine.righe_ordinato):
            QMessageBox.warning(self, "Errore", "Prodotto non trovato!")
            return
        riga = ordine.righe_ordinato[self.prodotto_selezionato_ordinato_idx]

        dialog = QDialog(self, Qt.FramelessWindowHint)
        dialog.setStyleSheet("QDialog { background-color: white; border: 2px solid #34495e; border-radius: 10px; }")
        dialog.setFixedSize(380, 230)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        titolo = QLabel(f"Motivo per: {riga.prodotto.nome}")
        titolo.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold;")
        layout.addWidget(titolo)

        sottotitolo = QLabel("Se annulli, il prezzo verrà detratto dal totale.")
        sottotitolo.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(sottotitolo)

        btn_annullato = QPushButton("❌ Annullato  (detrai prezzo)")
        btn_annullato.setMinimumHeight(45)
        btn_annullato.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        btn_annullato.clicked.connect(lambda: self.salva_motivo_rifiuto(dialog, riga, "Annullato", numero_tavolo))
        layout.addWidget(btn_annullato)

        btn_sostituzione = QPushButton("🔄 Sostituzione Prodotto")
        btn_sostituzione.setMinimumHeight(45)
        btn_sostituzione.setStyleSheet("QPushButton { background-color: #f39c12; color: white; border: none; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #d68910; }")
        btn_sostituzione.clicked.connect(lambda: self.salva_motivo_rifiuto(dialog, riga, "Sostituzione Prodotto", numero_tavolo))
        layout.addWidget(btn_sostituzione)

        x = (self.width() - dialog.width()) // 2
        y = (self.height() - dialog.height()) // 2
        dialog.setGeometry(x, y, dialog.width(), dialog.height())
        dialog.exec_()

    def salva_motivo_rifiuto(self, dialog, riga, motivo: str, numero_tavolo: int):
        riga.motivo_rifiuto = motivo
        dialog.accept()
        # Aggiorna totale
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        self.label_totale.setText(f"€{ordine.get_totale():.2f}")
        self.mostra_tab_ordinato(numero_tavolo)

    # =========================================================================
    # ATTESA PRODOTTI
    # =========================================================================

    def metti_attesa(self, numero_tavolo: int, idx: int, is_ordinare: bool = True):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if is_ordinare and idx < len(ordine.righe_ordinare):
            ordine.righe_ordinare[idx].in_attesa = True
        elif not is_ordinare and idx < len(ordine.righe_ordinato):
            ordine.righe_ordinato[idx].in_attesa = True
        tavolo = self.gestione.get_tavolo(numero_tavolo)
        if tavolo: tavolo.in_attesa = True
        self.mostra_tab_ordinare(numero_tavolo)
        self.mostra_tab_ordinato(numero_tavolo)
        self.aggiorna_colori_tavoli()

    def sblocca_prodotto(self, numero_tavolo: int, idx: int, is_ordinare: bool = True):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if is_ordinare and idx < len(ordine.righe_ordinare):
            ordine.righe_ordinare[idx].in_attesa = False
        elif not is_ordinare and idx < len(ordine.righe_ordinato):
            ordine.righe_ordinato[idx].in_attesa = False
        ha_attesa = any(r.in_attesa for r in ordine.righe_ordinare) or \
                    any(r.in_attesa for r in ordine.righe_ordinato)
        if not ha_attesa:
            tavolo = self.gestione.get_tavolo(numero_tavolo)
            if tavolo: tavolo.in_attesa = False
        self.mostra_tab_ordinare(numero_tavolo)
        self.mostra_tab_ordinato(numero_tavolo)
        self.aggiorna_colori_tavoli()

    # =========================================================================
    # PRODOTTI / MENU
    # =========================================================================

    def mostra_prodotti_card(self, categoria: str, numero_tavolo: int, search: bool = False, termine_ricerca: str = ""):

        # PULIZIA LAYOUT
        while self.layout_prodotti.count():
            child = self.layout_prodotti.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # PRENDO PRODOTTI
        if search and termine_ricerca:
            tutti = self.gestione.get_tutti_prodotti()
            prodotti = [p for p in tutti if termine_ricerca.lower() in p.nome.lower()]
        else:
            prodotti = self.gestione.get_categoria_prodotti(categoria)

        # SCROLL
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")

        container = QWidget()
        container.setStyleSheet("background-color: white;")
        grid = QGridLayout(container)
        grid.setSpacing(10)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        COLS = 3
        for i, prodotto in enumerate(prodotti):
            row = i // COLS
            col = i % COLS

            # Contenitore card cliccabile
            card_widget = QWidget()
            card_widget.setFixedSize(150, 90)
            card_widget.setStyleSheet("""
                QWidget {
                    background-color: #5dade2;
                    border-radius: 10px;
                    border: 1px solid #2e86c1;
                }
                QWidget:hover {
                    background-color: #3498db;
                    border: 1px solid #1a6fa8;
                }
            """)

            card_layout = QVBoxLayout(card_widget)
            card_layout.setContentsMargins(10, 10, 10, 10)
            card_layout.setSpacing(4)
            card_layout.setAlignment(Qt.AlignTop)

            lbl_nome = QLabel(prodotto.nome)
            lbl_nome.setWordWrap(True)
            lbl_nome.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: transparent; border: none;")
            lbl_nome.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            card_layout.addWidget(lbl_nome)

            lbl_prezzo = QLabel(f"€ {prodotto.prezzo:.2f}")
            lbl_prezzo.setStyleSheet("color: #d6eaf8; font-size: 13px; font-weight: bold; background: transparent; border: none;")
            lbl_prezzo.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
            card_layout.addStretch()
            card_layout.addWidget(lbl_prezzo)

            # Click su tutta la card
            card_widget.mousePressEvent = lambda e, p=prodotto: self.card_cliccata(numero_tavolo, p)

            grid.addWidget(card_widget, row, col, Qt.AlignTop | Qt.AlignLeft)

        # Riempi colonne vuote nell'ultima riga per allineamento sinistra
        total = len(prodotti)
        remainder = total % COLS
        if remainder != 0:
            for fill_col in range(remainder, COLS):
                spacer = QWidget()
                spacer.setFixedSize(150, 90)
                spacer.setStyleSheet("background: transparent; border: none;")
                grid.addWidget(spacer, total // COLS, fill_col)

        scroll.setWidget(container)
        self.layout_prodotti.addWidget(scroll)

    def cambia_categoria(self, categoria: str, numero_tavolo: int):
        self.categoria_attuale = categoria
        for cat, btn in self.pulsanti_categorie.items():
            if cat == categoria:
                btn.setStyleSheet("QPushButton { background-color: #e67e22; color: white; border: none; border-radius: 5px; padding: 5px; font-size: 9px; font-weight: bold; border-bottom: 3px solid #d35400; } QPushButton:hover { background-color: #d35400; }")
            else:
                btn.setStyleSheet("QPushButton { background-color: #f39c12; color: white; border: none; border-radius: 5px; padding: 5px; font-size: 9px; font-weight: bold; } QPushButton:hover { background-color: #e67e22; }")
        self.mostra_prodotti_card(categoria, numero_tavolo)

    def card_cliccata(self, numero_tavolo: int, prodotto: Prodotto):
        self.gestione.aggiungi_al_ordine(numero_tavolo, prodotto, 1)
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine:
            self.label_totale.setText(f"€{ordine.get_totale():.2f}")
        self.mostra_tab_ordinare(numero_tavolo)

    # =========================================================================
    # SEZIONE DESTRA (Nota / Ingredienti)
    # =========================================================================

    def mostra_sezione_destra(self, prodotto):
        while self.sezione_destra_layout.count():
            child = self.sezione_destra_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if prodotto is None:
            lbl = QLabel("Seleziona un prodotto")
            lbl.setStyleSheet("color: #95a5a6; font-size: 12px; padding: 20px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.sezione_destra_layout.addWidget(lbl)
            self.sezione_destra_layout.addStretch()
            return

        btn_nota = QPushButton("📝 Nota Cucina")
        btn_nota.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 12px; font-size: 12px; font-weight: bold; border-radius: 6px; min-height: 45px; } QPushButton:hover { background-color: #2980b9; }")
        btn_nota.clicked.connect(self.apri_popup_nota)
        self.sezione_destra_layout.addWidget(btn_nota)

        if prodotto.categoria in ["Pizze", "Primi piatti", "Panini"]:
            btn_ing = QPushButton("🥘 Ingredienti")
            btn_ing.setStyleSheet("QPushButton { background-color: #f39c12; color: white; border: none; padding: 12px; font-size: 12px; font-weight: bold; border-radius: 6px; min-height: 45px; } QPushButton:hover { background-color: #e67e22; }")
            btn_ing.clicked.connect(self.apri_popup_ingredienti)
            self.sezione_destra_layout.addWidget(btn_ing)

        self.sezione_destra_layout.addStretch()

    def apri_popup_nota(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nota Cucina")
        dialog.setGeometry(500, 400, 500, 300)
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout()
        title = QLabel("📝 Nota Cucina")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        text_nota = QTextEdit()
        text_nota.setStyleSheet("QTextEdit { font-size: 13px; border: 2px solid #3498db; border-radius: 6px; padding: 10px; background-color: white; }")
        text_nota.setPlaceholderText("Es: Senza sale, ben cotto, con salsa a parte...")
        layout.addWidget(text_nota)
        bl = QHBoxLayout()
        btn_c = QPushButton("Chiudi")
        btn_c.setMinimumHeight(40)
        btn_c.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_c.clicked.connect(dialog.reject)
        bl.addWidget(btn_c)
        btn_s = QPushButton("✓ Salva")
        btn_s.setMinimumHeight(40)
        btn_s.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_s.clicked.connect(lambda: self.salva_nota(dialog, text_nota.toPlainText()))
        bl.addWidget(btn_s)
        layout.addLayout(bl)
        dialog.setLayout(layout)
        dialog.exec_()

    def apri_popup_ingredienti(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ingredienti")
        dialog.setGeometry(500, 400, 500, 300)
        dialog.setModal(True)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout()
        title = QLabel("🥘 Ingredienti")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        text_ing = QTextEdit()
        text_ing.setStyleSheet("QTextEdit { font-size: 13px; border: 2px solid #f39c12; border-radius: 6px; padding: 10px; background-color: white; }")
        text_ing.setPlaceholderText("Es: Aggiungi mozzarella, pomodoro, basilico...")
        layout.addWidget(text_ing)
        bl = QHBoxLayout()
        btn_c = QPushButton("Chiudi")
        btn_c.setMinimumHeight(40)
        btn_c.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_c.clicked.connect(dialog.reject)
        bl.addWidget(btn_c)
        btn_s = QPushButton("✓ Salva")
        btn_s.setMinimumHeight(40)
        btn_s.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        btn_s.clicked.connect(lambda: self.salva_ingredienti(dialog, text_ing.toPlainText()))
        bl.addWidget(btn_s)
        layout.addLayout(bl)
        dialog.setLayout(layout)
        dialog.exec_()

    def salva_nota(self, dialog, nota: str):
        if nota.strip():
            ordine = self.gestione.get_ordine_attivo(self.tavolo_attuale)
            if self.prodotto_selezionato_idx is not None and self.prodotto_selezionato_idx < len(ordine.righe_ordinare):
                ordine.righe_ordinare[self.prodotto_selezionato_idx].nota_cucina = nota
                self.mostra_tab_ordinare(self.tavolo_attuale)
            dialog.accept()
        else:
            QMessageBox.warning(self, "Errore", "Scrivi una nota!")

    def salva_ingredienti(self, dialog, ingredienti: str):
        if ingredienti.strip():
            ordine = self.gestione.get_ordine_attivo(self.tavolo_attuale)
            if self.prodotto_selezionato_idx is not None and self.prodotto_selezionato_idx < len(ordine.righe_ordinare):
                ordine.righe_ordinare[self.prodotto_selezionato_idx].ingredienti = ingredienti
                self.mostra_tab_ordinare(self.tavolo_attuale)
            dialog.accept()
        else:
            QMessageBox.warning(self, "Errore", "Scrivi gli ingredienti!")

    # =========================================================================
    # RICERCA
    # =========================================================================

    def apri_popup_ricerca(self, numero_tavolo: int):
        if hasattr(self, 'ricerca_barra') and self.ricerca_barra:
            if self.ricerca_barra.isVisible():
                self.ricerca_barra.hide()
                self.ricerca_input.clear()
                self.mostra_prodotti_card(self.categoria_attuale, numero_tavolo, search=False)
            else:
                self.ricerca_barra.show()
                self.ricerca_input.setFocus()
            return

        self.ricerca_barra = QLineEdit()
        self.ricerca_barra.setPlaceholderText("Cerca prodotto...")
        self.ricerca_barra.setStyleSheet("QLineEdit { font-size: 12px; padding: 8px; border: 2px solid #3498db; border-radius: 6px; background-color: white; min-height: 35px; }")
        self.ricerca_input = self.ricerca_barra

        if hasattr(self, 'destra_layout'):
            self.ricerca_barra.hide()
            self.destra_layout.insertWidget(1, self.ricerca_barra)

        def filtra(testo):
            if testo.strip():
                self.mostra_prodotti_card(self.categoria_attuale, numero_tavolo, search=True, termine_ricerca=testo)
            else:
                self.mostra_prodotti_card(self.categoria_attuale, numero_tavolo, search=False)

        self.ricerca_input.textChanged.connect(lambda: filtra(self.ricerca_input.text()))
        self.ricerca_barra.show()
        self.ricerca_input.setFocus()

    # =========================================================================
    # CONFERMA / QUANTITÀ
    # =========================================================================

    def conferma_ordine_final(self, numero_tavolo: int):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if not ordine.righe_ordinare:
            QMessageBox.warning(self, "Errore", "Non ci sono prodotti da ordinare!")
            return
        ordine.righe_ordinato.extend(ordine.righe_ordinare)
        ordine.righe_ordinare.clear()
        ordine.stato = StatoOrdine.IN_PREPARAZIONE
        self.torna_a_tavoli()

    def aumenta_quantita(self, numero_tavolo: int, idx: int, prodotto: Prodotto):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine and idx < len(ordine.righe_ordinare):
            ordine.righe_ordinare[idx].quantita += 1
            self.mostra_tab_ordinare(numero_tavolo)
            self.label_totale.setText(f"€{ordine.get_totale():.2f}")

    def diminuisci_quantita(self, numero_tavolo: int, idx: int):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        if ordine and idx < len(ordine.righe_ordinare):
            if ordine.righe_ordinare[idx].quantita > 1:
                ordine.righe_ordinare[idx].quantita -= 1
            else:
                ordine.righe_ordinare.pop(idx)
            self.mostra_tab_ordinare(numero_tavolo)
            self.label_totale.setText(f"€{ordine.get_totale():.2f}")

    # =========================================================================
    # PAGAMENTO
    # =========================================================================

    def paga_ordine(self, numero_tavolo: int):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("💳 PAGAMENTO")
        header.setStyleSheet("font-size: 32px; font-weight: bold; color: white; padding: 25px; background-color: #34495e;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        centrale = QWidget()
        cl = QVBoxLayout(centrale)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(30)

        info = QLabel(f"Tavolo: {numero_tavolo} | Persone: {ordine.numero_persone}")
        info.setStyleSheet("font-size: 18px; color: white; padding: 15px; background-color: #2c3e50; border-radius: 4px;")
        info.setAlignment(Qt.AlignCenter)
        cl.addWidget(info)

        totale_val = ordine.get_totale()
        totale_label = QLabel(f"TOTALE: €{totale_val:.2f}")
        totale_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #27ae60; padding: 30px;")
        totale_label.setAlignment(Qt.AlignCenter)
        cl.addWidget(totale_label)

        # Mostra prodotti annullati se ce ne sono
        annullati = [r for r in ordine.righe_ordinato if r.motivo_rifiuto == "Annullato"]
        if annullati:
            testo_ann = "⚠️ Prodotti annullati (già detratti): " + ", ".join(
                f"{r.prodotto.nome} (-€{r.prodotto.prezzo * r.quantita:.2f})" for r in annullati)
            lbl_ann = QLabel(testo_ann)
            lbl_ann.setStyleSheet("color: #e74c3c; font-size: 12px; padding: 8px; background-color: #fdecea; border-radius: 6px;")
            lbl_ann.setWordWrap(True)
            cl.addWidget(lbl_ann)

        pag_layout = QHBoxLayout()
        pag_layout.setSpacing(20)

        for testo, colore, metodo in [
            ("💵 CONTANTI", "#27ae60", "Contanti"),
            ("💳 CARTA",    "#3498db", "Carta"),
            ("🖨️ STAMPA",   "#f39c12", "Stampa"),
        ]:
            btn = QPushButton(testo)
            btn.setMinimumHeight(120)
            btn.setMinimumWidth(250)
            btn.setStyleSheet(f"QPushButton {{ background-color: {colore}; color: white; border: none; border-radius: 12px; font-size: 20px; font-weight: bold; }} QPushButton:hover {{ background-color: {colore}cc; }}")
            if metodo == "Stampa":
                btn.clicked.connect(lambda: self.stampa_scontrino(numero_tavolo))
            else:
                btn.clicked.connect(lambda checked, m=metodo: self.completa_pagamento_fullscreen(numero_tavolo, m))
            pag_layout.addWidget(btn)

        cl.addLayout(pag_layout)
        cl.addStretch()

        btn_back = QPushButton("← INDIETRO")
        btn_back.setMinimumHeight(60)
        btn_back.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #7f8c8d; }")
        btn_back.clicked.connect(lambda: self.mostra_schermata_ordine(numero_tavolo, tab_ordinato=True))
        cl.addWidget(btn_back)

        centrale.setLayout(cl)
        layout.addWidget(centrale)

    def completa_pagamento_fullscreen(self, numero_tavolo: int, metodo: str):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        tutte_righe = ordine.righe_ordinare + ordine.righe_ordinato
        db = DatabaseOrdini()
        db.salva_pagamento_cronologia(numero_tavolo, ordine.numero_persone, metodo, ordine.get_totale(), tutte_righe)
        db.chiudi()
        QMessageBox.information(self, "Pagamento Completato",
                                f"Pagamento ricevuto in {metodo}!\n\nTotale pagato: €{ordine.get_totale():.2f}")
        self.gestione.libera_tavolo(numero_tavolo)
        self.torna_a_tavoli()

    def stampa_scontrino(self, numero_tavolo: int):
        ordine = self.gestione.get_ordine_attivo(numero_tavolo)
        scontrino = "=" * 40 + "\nSCONTRINO TAVOLO\n" + "=" * 40 + "\n\n"
        scontrino += f"Tavolo: {numero_tavolo}\nPersone: {ordine.numero_persone}\n"
        scontrino += f"Data: {ordine.data_creazione.strftime('%d/%m/%Y %H:%M')}\n\n"
        scontrino += "-" * 40 + "\n"
        scontrino += f"{'Prodotto':<25} {'Qtà':<5} {'Prezzo':>8}\n"
        scontrino += "-" * 40 + "\n"
        for riga in (ordine.righe_ordinare + ordine.righe_ordinato):
            if riga.motivo_rifiuto == "Annullato":
                scontrino += f"[ANNULLATO] {riga.prodotto.nome[:20]}\n"
            else:
                scontrino += f"{riga.prodotto.nome[:24]:<25} {riga.quantita:<5} €{riga.get_subtotale():>7.2f}\n"
        scontrino += "-" * 40 + f"\n{'TOTALE':<30} €{ordine.get_totale():>8.2f}\n" + "=" * 40 + "\nGrazie della visita!\n" + "=" * 40 + "\n"

        dialog = QDialog(self)
        dialog.setWindowTitle("Scontrino")
        dialog.setGeometry(400, 300, 500, 600)
        dialog.setModal(True)
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setText(scontrino)
        text.setReadOnly(True)
        text.setStyleSheet("QTextEdit { font-family: Courier; font-size: 10px; padding: 10px; }")
        layout.addWidget(text)
        btn_print = QPushButton("🖨️ Stampa Scontrino")
        btn_print.setMinimumHeight(40)
        btn_print.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_print.clicked.connect(lambda: QMessageBox.information(self, "Stampa", "Scontrino inviato alla stampante!"))
        layout.addWidget(btn_print)
        btn_close = QPushButton("Chiudi")
        btn_close.setMinimumHeight(40)
        btn_close.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold;")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.setLayout(layout)
        dialog.exec_()

    # =========================================================================
    # PANNELLO ADMIN
    # =========================================================================

    def mostra_pannello_admin(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)
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

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #bdc3c7; } QTabBar::tab { background-color: #ecf0f1; padding: 8px 20px; } QTabBar::tab:selected { background-color: #3498db; color: white; }")
        tabs.addTab(self.crea_tab_prodotti(), "📦 Prodotti")
        tabs.addTab(self.crea_tab_categorie(), "📂 Categorie")
        tabs.addTab(self.crea_tab_csv(), "📄 CSV")
        tabs.addTab(self.crea_tab_tavoli(), "🍽️ Tavoli")
        tabs.addTab(self.crea_tab_cronologia(), "📋 Cronologia")
        layout.addWidget(tabs)

    def crea_tab_prodotti(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.tabella_prodotti = QTableWidget()
        self.tabella_prodotti.setColumnCount(5)
        self.tabella_prodotti.setHorizontalHeaderLabels(["ID","Nome","Categoria","Prezzo","Azioni"])
        self.tabella_prodotti.setColumnWidth(0,50); self.tabella_prodotti.setColumnWidth(1,150)
        self.tabella_prodotti.setColumnWidth(2,120); self.tabella_prodotti.setColumnWidth(3,100); self.tabella_prodotti.setColumnWidth(4,100)
        self.aggiorna_tabella_prodotti()
        layout.addWidget(self.tabella_prodotti)
        bl = QHBoxLayout()
        btn_n = QPushButton("➕ Nuovo Prodotto")
        btn_n.setMinimumHeight(40)
        btn_n.setStyleSheet("background-color: #27ae60; font-size: 14px;")
        btn_n.clicked.connect(self.dialogo_nuovo_prodotto)
        bl.addWidget(btn_n)
        btn_s = QPushButton("💾 Salva")
        btn_s.setMinimumHeight(40)
        btn_s.setStyleSheet("background-color: #3498db; font-size: 14px;")
        btn_s.clicked.connect(lambda: QMessageBox.information(self,"Successo","Prodotti salvati!"))
        bl.addWidget(btn_s)
        layout.addLayout(bl)
        return widget

    def crea_tab_categorie(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        lbl = QLabel("Gestione Categorie")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl)
        self.lista_categorie = QListWidget()
        for cat in self.gestione.get_categorie():
            self.lista_categorie.addItem(cat)
        layout.addWidget(self.lista_categorie)
        bl = QHBoxLayout()
        btn_a = QPushButton("➕ Nuova Categoria")
        btn_a.setMinimumHeight(40)
        btn_a.setStyleSheet("background-color: #27ae60; font-size: 14px;")
        btn_a.clicked.connect(self.dialogo_nuova_categoria)
        bl.addWidget(btn_a)
        btn_e = QPushButton("🗑️ Elimina")
        btn_e.setMinimumHeight(40)
        btn_e.setStyleSheet("background-color: #e74c3c; font-size: 14px;")
        btn_e.clicked.connect(self.elimina_categoria)
        bl.addWidget(btn_e)
        layout.addLayout(bl)
        return widget

    def crea_tab_csv(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        lbl = QLabel("Import/Export CSV")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl)
        info = QLabel("Esporta il menu in CSV per modificarlo in Excel.\nFormato: id,nome,categoria,prezzo")
        info.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(info)
        bl = QVBoxLayout()
        for testo, colore, fn in [("📥 Esporta Menu (CSV)","#3498db",self.esporta_csv),("📤 Importa Menu (CSV)","#27ae60",self.importa_csv)]:
            btn = QPushButton(testo)
            btn.setMinimumHeight(50)
            btn.setStyleSheet(f"background-color: {colore}; font-size: 14px;")
            btn.clicked.connect(fn)
            bl.addWidget(btn)
        layout.addLayout(bl)
        layout.addStretch()
        return widget

    def crea_tab_tavoli(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("⚙️ Gestione Tavoli")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e;")
        layout.addWidget(title)

        info = QLabel("Aggiungi, elimina o regola il numero dei tavoli.")
        info.setStyleSheet("font-size: 12px; color: #555; padding: 10px;")
        layout.addWidget(info)

        numero_layout = QHBoxLayout()
        lbl = QLabel("Numero totale tavoli:")
        lbl.setStyleSheet("font-size: 13px; font-weight: bold;")
        numero_layout.addWidget(lbl)
        self.spin_tavoli = QSpinBox()
        self.spin_tavoli.setMinimum(1)
        self.spin_tavoli.setMaximum(100)
        self.spin_tavoli.setValue(len([t for t in self.gestione.get_tutti_tavoli() if t.numero_tavolo > 0]))
        self.spin_tavoli.setMinimumHeight(40)
        self.spin_tavoli.setMinimumWidth(100)
        self.spin_tavoli.setStyleSheet("QSpinBox { font-size: 14px; padding: 8px; border: 2px solid #3498db; border-radius: 6px; }")
        numero_layout.addWidget(self.spin_tavoli)
        numero_layout.addStretch()
        btn_applica = QPushButton("✓ Applica")
        btn_applica.setMinimumHeight(40)
        btn_applica.setMinimumWidth(100)
        btn_applica.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_applica.clicked.connect(self.applica_numero_tavoli)
        numero_layout.addWidget(btn_applica)
        layout.addLayout(numero_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #bdc3c7; border-radius: 6px; background-color: white; }")
        self.container_tavoli = QWidget()
        self.container_tavoli.setStyleSheet("background-color: white;")
        self.layout_tavoli = QVBoxLayout(self.container_tavoli)
        self.layout_tavoli.setSpacing(8)
        self.layout_tavoli.setContentsMargins(10, 10, 10, 10)
        self.aggiorna_lista_tavoli()
        self.layout_tavoli.addStretch()
        self.container_tavoli.setLayout(self.layout_tavoli)
        scroll.setWidget(self.container_tavoli)
        layout.addWidget(scroll, 1)

        bl = QHBoxLayout()
        bl.setSpacing(10)
        btn_ag = QPushButton("➕ Aggiungi Tavolo")
        btn_ag.setMinimumHeight(45)
        btn_ag.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_ag.clicked.connect(self.aggiungi_tavolo)
        bl.addWidget(btn_ag)
        btn_rs = QPushButton("🔄 Reset a Default (30 Tavoli)")
        btn_rs.setMinimumHeight(45)
        btn_rs.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        btn_rs.clicked.connect(self.reset_tavoli_default)
        bl.addWidget(btn_rs)
        layout.addLayout(bl)
        return widget

    def aggiorna_lista_tavoli(self):
        while self.layout_tavoli.count() > 1:
            child = self.layout_tavoli.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        tavoli = [t for t in self.gestione.get_tutti_tavoli() if t.numero_tavolo > 0]
        self.tavolo_inputs = {}
        for tavolo in tavoli:
            rw = QWidget()
            rl = QHBoxLayout(rw)
            rl.setContentsMargins(10, 8, 10, 8)
            rl.setSpacing(10)
            nl = QLabel(f"#{tavolo.numero_tavolo}")
            nl.setStyleSheet("QLabel { font-size: 13px; font-weight: bold; background-color: #3498db; color: white; padding: 8px 12px; border-radius: 4px; min-width: 50px; }")
            nl.setAlignment(Qt.AlignCenter)
            rl.addWidget(nl)
            ni = QLineEdit()
            ni.setText(f"Tavolo {tavolo.numero_tavolo}")
            ni.setStyleSheet("QLineEdit { font-size: 13px; padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px; }")
            rl.addWidget(ni, 1)
            self.tavolo_inputs[tavolo.numero_tavolo] = ni
            stato = "In Attesa" if tavolo.in_attesa else ("Occupato" if tavolo.occupato else "Libero")
            colore = "#e74c3c" if tavolo.in_attesa else ("#f39c12" if tavolo.occupato else "#27ae60")
            sl = QLabel(stato)
            sl.setStyleSheet(f"QLabel {{ font-size: 11px; font-weight: bold; background-color: {colore}; color: white; padding: 6px 10px; border-radius: 4px; min-width: 70px; }}")
            sl.setAlignment(Qt.AlignCenter)
            rl.addWidget(sl)
            pl = QLabel(f"€{tavolo.ordine_attivo.get_totale():.2f}" if tavolo.ordine_attivo else "€0.00")
            pl.setStyleSheet("font-size: 13px; font-weight: bold; color: #27ae60; min-width: 70px;")
            pl.setAlignment(Qt.AlignRight)
            rl.addWidget(pl)
            btn_el = QPushButton("🗑️")
            btn_el.setMaximumWidth(45)
            btn_el.setMinimumHeight(35)
            btn_el.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 16px; } QPushButton:hover { background-color: #c0392b; }")
            btn_el.clicked.connect(lambda checked, n=tavolo.numero_tavolo: self.elimina_tavolo(n))
            rl.addWidget(btn_el)
            rw.setLayout(rl)
            rw.setStyleSheet("QWidget { background-color: #f9f9f9; border: 1px solid #ecf0f1; border-radius: 6px; }")
            self.layout_tavoli.insertWidget(len(self.tavolo_inputs)-1, rw)

    def applica_numero_tavoli(self):
        nuovo = self.spin_tavoli.value()
        attuale = len([t for t in self.gestione.get_tutti_tavoli() if t.numero_tavolo > 0])
        if nuovo == attuale:
            QMessageBox.information(self, "Info", "Nessun cambiamento!")
            return
        if nuovo > attuale:
            for i in range(attuale+1, nuovo+1):
                self.gestione.tavoli[i] = Tavolo(i)
        else:
            for i in range(attuale, nuovo, -1):
                if i in self.gestione.tavoli:
                    del self.gestione.tavoli[i]
        self.aggiorna_lista_tavoli()
        QMessageBox.information(self, "Successo", f"Tavoli aggiornati a {nuovo}!")

    def aggiungi_tavolo(self):
        num_max = max([t.numero_tavolo for t in self.gestione.get_tutti_tavoli()])
        nuovo = num_max + 1
        self.gestione.tavoli[nuovo] = Tavolo(nuovo)
        self.spin_tavoli.setValue(self.spin_tavoli.value()+1)
        self.aggiorna_lista_tavoli()
        QMessageBox.information(self, "Successo", f"Tavolo #{nuovo} aggiunto!")

    def elimina_tavolo(self, numero_tavolo: int):
        tavolo = self.gestione.get_tavolo(numero_tavolo)
        if tavolo and tavolo.occupato:
            QMessageBox.warning(self, "Errore", "Non puoi eliminare un tavolo occupato!")
            return
        reply = QMessageBox.question(self, "Conferma", f"Eliminare il Tavolo #{numero_tavolo}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.gestione.tavoli[numero_tavolo]
            self.spin_tavoli.setValue(self.spin_tavoli.value()-1)
            self.aggiorna_lista_tavoli()

    def reset_tavoli_default(self):
        reply = QMessageBox.question(self, "Conferma Reset", "Reset a 30 tavoli di default?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if any(t.occupato for t in self.gestione.get_tutti_tavoli()):
                QMessageBox.warning(self, "Errore", "Ci sono tavoli occupati! Libera tutto prima.")
                return
            self.gestione.tavoli = {i: Tavolo(i) for i in range(0, 31)}
            self.spin_tavoli.setValue(30)
            self.aggiorna_lista_tavoli()
            QMessageBox.information(self, "Successo", "Reset completato!")

    def crea_tab_cronologia(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        db = DatabaseOrdini()
        stats = db.get_statistiche_giornaliere()
        db.chiudi()

        stats_widget = QWidget()
        stats_widget.setStyleSheet("QWidget { background-color: #2c3e50; border-radius: 8px; }")
        sl = QHBoxLayout(stats_widget)
        sl.setContentsMargins(15, 10, 15, 10)
        sl.setSpacing(20)

        def stat_box(titolo, valore, colore):
            box = QWidget()
            box.setStyleSheet(f"QWidget {{ background-color: {colore}; border-radius: 6px; }}")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(12, 8, 12, 8)
            t = QLabel(titolo)
            t.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 10px; font-weight: bold;")
            t.setAlignment(Qt.AlignCenter)
            v = QLabel(valore)
            v.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
            v.setAlignment(Qt.AlignCenter)
            bl.addWidget(t)
            bl.addWidget(v)
            return box

        sl.addWidget(stat_box("ORDINI OGGI", str(stats['num_ordini']), "#27ae60"))
        sl.addWidget(stat_box("TOTALE OGGI", f"€{stats['totale_giorno']:.2f}", "#2980b9"))
        sl.addWidget(stat_box("PERSONE", str(stats['tot_persone']), "#8e44ad"))
        sl.addWidget(stat_box("CONTANTI", f"€{stats['tot_contanti']:.2f}", "#e67e22"))
        sl.addWidget(stat_box("CARTA", f"€{stats['tot_carta']:.2f}", "#16a085"))
        layout.addWidget(stats_widget)

        filtri_layout = QHBoxLayout()
        self.filtro_metodo = QComboBox()
        self.filtro_metodo.addItems(["Tutti","Contanti","Carta"])
        self.filtro_metodo.setMinimumHeight(35)
        filtri_layout.addWidget(QLabel("Metodo:"))
        filtri_layout.addWidget(self.filtro_metodo)
        self.filtro_tavolo = QLineEdit()
        self.filtro_tavolo.setPlaceholderText("N° Tavolo...")
        self.filtro_tavolo.setMaximumWidth(120)
        self.filtro_tavolo.setMinimumHeight(35)
        filtri_layout.addWidget(self.filtro_tavolo)
        btn_f = QPushButton("🔍 Filtra")
        btn_f.setMinimumHeight(35)
        btn_f.setMaximumWidth(100)
        btn_f.setStyleSheet("background-color: #3498db; color: white; font-size: 13px; border-radius: 6px;")
        btn_f.clicked.connect(self.aggiorna_tabella_cronologia)
        filtri_layout.addWidget(btn_f)
        btn_r = QPushButton("✕ Reset")
        btn_r.setMinimumHeight(35)
        btn_r.setMaximumWidth(90)
        btn_r.setStyleSheet("background-color: #95a5a6; color: white; font-size: 13px; border-radius: 6px;")
        btn_r.clicked.connect(lambda: (self.filtro_metodo.setCurrentIndex(0), self.filtro_tavolo.clear(), self.aggiorna_tabella_cronologia()))
        filtri_layout.addWidget(btn_r)
        filtri_layout.addStretch()
        btn_exp = QPushButton("📥 Esporta CSV")
        btn_exp.setMinimumHeight(35)
        btn_exp.setStyleSheet("background-color: #27ae60; color: white; font-size: 13px; border-radius: 6px;")
        btn_exp.clicked.connect(self.esporta_cronologia_csv)
        filtri_layout.addWidget(btn_exp)
        layout.addLayout(filtri_layout)

        self.tabella_cronologia = QTableWidget()
        self.tabella_cronologia.setColumnCount(7)
        self.tabella_cronologia.setHorizontalHeaderLabels(["Data/Ora","Tavolo","Persone","Metodo","Totale","Prodotti","Dettaglio"])
        self.tabella_cronologia.setColumnWidth(0,130); self.tabella_cronologia.setColumnWidth(1,65)
        self.tabella_cronologia.setColumnWidth(2,60); self.tabella_cronologia.setColumnWidth(3,80)
        self.tabella_cronologia.setColumnWidth(4,80); self.tabella_cronologia.setColumnWidth(5,350); self.tabella_cronologia.setColumnWidth(6,80)
        self.tabella_cronologia.setStyleSheet("QTableWidget { background-color: white; alternate-background-color: #f5f8ff; border: 1px solid #bdc3c7; } QTableWidget::item { padding: 6px; font-size: 12px; } QHeaderView::section { background-color: #2c3e50; color: white; padding: 8px; border: none; font-size: 12px; font-weight: bold; }")
        self.tabella_cronologia.setAlternatingRowColors(True)
        self.tabella_cronologia.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabella_cronologia.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabella_cronologia.verticalHeader().setVisible(False)
        layout.addWidget(self.tabella_cronologia, 1)
        self.aggiorna_tabella_cronologia()
        return widget

    def aggiorna_tabella_cronologia(self):
        db = DatabaseOrdini()
        righe = db.get_cronologia(500)
        db.chiudi()
        filtro_metodo = self.filtro_metodo.currentText() if hasattr(self, 'filtro_metodo') else "Tutti"
        filtro_tavolo = self.filtro_tavolo.text().strip() if hasattr(self, 'filtro_tavolo') else ""
        if filtro_metodo != "Tutti":
            righe = [r for r in righe if r['metodo_pagamento'] == filtro_metodo]
        if filtro_tavolo:
            try:
                n = int(filtro_tavolo)
                righe = [r for r in righe if r['numero_tavolo'] == n]
            except: pass
        self.tabella_cronologia.setRowCount(0)
        ICONA = {"Contanti":"💵","Carta":"💳"}
        for i, riga in enumerate(righe):
            self.tabella_cronologia.insertRow(i)
            try:
                dt = datetime.fromisoformat(riga['data_ora'])
                data_str = dt.strftime("%d/%m/%Y %H:%M")
            except: data_str = str(riga['data_ora'])
            tavolo_str = "Asporto" if riga['numero_tavolo'] == 0 else f"T. {riga['numero_tavolo']}"
            metodo = riga['metodo_pagamento'] or ""
            metodo_str = f"{ICONA.get(metodo,'💰')} {metodo}"
            colore = QColor("#eafaf1") if metodo == "Contanti" else QColor("#eaf4fb")
            for j, val in enumerate([data_str, tavolo_str, str(riga['numero_persone']), metodo_str, f"€{riga['totale']:.2f}", riga['dettaglio_prodotti'] or ""]):
                item = QTableWidgetItem(val)
                item.setBackground(colore)
                if j == 4:
                    item.setForeground(QColor("#27ae60"))
                    item.setFont(QFont("Arial", 11, QFont.Bold))
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabella_cronologia.setItem(i, j, item)
            btn_det = QPushButton("🔍 Vedi")
            btn_det.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; border-radius: 4px; font-size: 11px; padding: 4px 8px; } QPushButton:hover { background-color: #2980b9; }")
            ds=riga['dettaglio_prodotti'] or ""
            d=data_str; t=tavolo_str; p=riga['numero_persone']; m=metodo; tot=riga['totale']
            btn_det.clicked.connect(lambda _, ds=ds,d=d,t=t,p=p,m=m,tot=tot: self.mostra_dettaglio_cronologia(d,t,p,m,tot,ds))
            self.tabella_cronologia.setCellWidget(i, 6, btn_det)
            self.tabella_cronologia.setRowHeight(i, 38)

    def mostra_dettaglio_cronologia(self, data, tavolo, persone, metodo, totale, dettaglio):
        dialog = QDialog(self)
        dialog.setWindowTitle("Dettaglio Ordine")
        dialog.setMinimumSize(520, 480)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        lbl = QLabel(f"📅 {data}  |  🍽️ {tavolo}  |  👥 {persone} persone  |  💳 {metodo}  |  💰 €{totale:.2f}")
        lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: white; background-color: #2c3e50; padding: 12px; border-radius: 8px;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #bdc3c7; border-radius: 6px; background: white; }")
        contenuto = QWidget()
        cl = QVBoxLayout(contenuto)
        cl.setContentsMargins(10, 10, 10, 10)
        for prod_str in (dettaglio.split(" | ") if dettaglio else []):
            rw = QWidget()
            rw.setStyleSheet("QWidget { background-color: #f8f9fa; border: 1px solid #ecf0f1; border-radius: 5px; }")
            rl = QHBoxLayout(rw)
            rl.setContentsMargins(10, 6, 10, 6)
            lbl2 = QLabel(prod_str)
            lbl2.setStyleSheet("font-size: 13px; color: #2c3e50;")
            lbl2.setWordWrap(True)
            rl.addWidget(lbl2)
            cl.addWidget(rw)
        if not dettaglio:
            cl.addWidget(QLabel("Nessun dettaglio"))
        cl.addStretch()
        scroll.setWidget(contenuto)
        layout.addWidget(scroll, 1)
        btn_c = QPushButton("✕ Chiudi")
        btn_c.setMinimumHeight(42)
        btn_c.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold; border-radius: 6px;")
        btn_c.clicked.connect(dialog.accept)
        layout.addWidget(btn_c)
        dialog.exec_()

    def esporta_cronologia_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Esporta Cronologia", "cronologia_pagamenti.csv", "CSV (*.csv)")
        if not file_path: return
        try:
            db = DatabaseOrdini()
            righe = db.get_cronologia(10000)
            db.chiudi()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("data_ora,tavolo,persone,metodo,totale,prodotti\n")
                for r in righe:
                    ts = "Asporto" if r['numero_tavolo'] == 0 else str(r['numero_tavolo'])
                    d = (r['dettaglio_prodotti'] or "").replace(",", ";")
                    f.write(f"{r['data_ora']},{ts},{r['numero_persone']},{r['metodo_pagamento']},{r['totale']:.2f},{d}\n")
            QMessageBox.information(self, "Successo", f"Cronologia esportata in:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", str(e))

    def aggiorna_tabella_prodotti(self):
        self.tabella_prodotti.setRowCount(0)
        db = DatabaseOrdini()
        prodotti = db.get_all_products()
        db.chiudi()
        for i, prod in enumerate(prodotti):
            self.tabella_prodotti.insertRow(i)
            self.tabella_prodotti.setItem(i,0,QTableWidgetItem(str(prod.id_prodotto)))
            self.tabella_prodotti.setItem(i,1,QTableWidgetItem(prod.nome))
            self.tabella_prodotti.setItem(i,2,QTableWidgetItem(prod.categoria))
            self.tabella_prodotti.setItem(i,3,QTableWidgetItem(f"€{prod.prezzo:.2f}"))
            btn = QPushButton("🗑️")
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, id=prod.id_prodotto: self.elimina_prodotto(id))
            self.tabella_prodotti.setCellWidget(i,4,btn)

    def dialogo_nuovo_prodotto(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuovo Prodotto")
        dialog.setGeometry(200,200,400,300)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nome:"))
        nome_input = QLineEdit()
        layout.addWidget(nome_input)
        layout.addWidget(QLabel("Categoria:"))
        cat_combo = QComboBox()
        cat_combo.addItems(self.gestione.get_categorie())
        layout.addWidget(cat_combo)
        layout.addWidget(QLabel("Prezzo:"))
        prezzo_input = QDoubleSpinBox()
        prezzo_input.setMaximum(999.99)
        prezzo_input.setDecimals(2)
        layout.addWidget(prezzo_input)
        bl = QHBoxLayout()
        btn_n = QPushButton("Annulla"); btn_n.clicked.connect(dialog.reject); bl.addWidget(btn_n)
        btn_o = QPushButton("✓ Aggiungi")
        btn_o.setStyleSheet("background-color: #27ae60; color: white;")
        btn_o.clicked.connect(lambda: self._aggiungi_prodotto_db(nome_input.text(), cat_combo.currentText(), prezzo_input.value(), dialog))
        bl.addWidget(btn_o)
        layout.addLayout(bl)
        dialog.setLayout(layout)
        dialog.exec_()

    def _aggiungi_prodotto_db(self, nome, categoria, prezzo, dialog):
        if not nome or prezzo <= 0:
            QMessageBox.warning(self,"Errore","Compila tutti i campi!")
            return
        db = DatabaseOrdini()
        db.add_product(nome, categoria, prezzo)
        db.chiudi()
        self.aggiorna_tabella_prodotti()
        QMessageBox.information(self,"Successo",f"Prodotto '{nome}' aggiunto!")
        dialog.accept()

    def elimina_prodotto(self, id_prodotto):
        if QMessageBox.question(self,"Conferma","Eliminare questo prodotto?") == QMessageBox.Yes:
            db = DatabaseOrdini()
            db.delete_product(id_prodotto)
            db.chiudi()
            self.aggiorna_tabella_prodotti()

    def dialogo_nuova_categoria(self):
        nome, ok = QInputDialog.getText(self,"Nuova Categoria","Nome categoria:")
        if ok and nome:
            db = DatabaseOrdini()
            db.add_category(nome)
            db.chiudi()
            self.lista_categorie.addItem(nome)

    def elimina_categoria(self):
        item = self.lista_categorie.currentItem()
        if not item:
            QMessageBox.warning(self,"Errore","Seleziona una categoria!")
            return
        cat = item.text()
        if QMessageBox.question(self,"Conferma",f"Elimina categoria '{cat}'?") == QMessageBox.Yes:
            db = DatabaseOrdini()
            db.delete_category(cat)
            db.chiudi()
            self.lista_categorie.takeItem(self.lista_categorie.row(item))

    def esporta_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(self,"Esporta Menu","menu.csv","CSV (*.csv)")
        if not file_path: return
        db = DatabaseOrdini()
        prodotti = db.get_all_products()
        db.chiudi()
        try:
            with open(file_path,'w',encoding='utf-8') as f:
                f.write("id,nome,categoria,prezzo\n")
                for prod in prodotti:
                    f.write(f"{prod.id_prodotto},{prod.nome},{prod.categoria},{prod.prezzo:.2f}\n")
            QMessageBox.information(self,"Successo",f"Menu esportato in:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self,"Errore",str(e))

    def importa_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self,"Importa Menu","","CSV (*.csv)")
        if not file_path: return
        try:
            db = DatabaseOrdini()
            with open(file_path,'r',encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]:
                    parts = line.strip().split(',')
                    if len(parts) == 4:
                        try:
                            db.add_or_update_product(int(parts[0]),parts[1],parts[2],float(parts[3]))
                        except: continue
            db.chiudi()
            self.aggiorna_tabella_prodotti()
            QMessageBox.information(self,"Successo","Menu importato!")
        except Exception as e:
            QMessageBox.critical(self,"Errore",str(e))

    # =========================================================================
    # NAVIGAZIONE
    # =========================================================================

    def torna_a_tavoli(self):
        if self.tavolo_attuale > 0:
            ordine = self.gestione.get_ordine_attivo(self.tavolo_attuale)
            if ordine and ordine.is_vuoto():
                self.gestione.libera_tavolo(self.tavolo_attuale)
        self.crea_schermata_principale()

    def aggiorna_colori_tavoli(self):
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