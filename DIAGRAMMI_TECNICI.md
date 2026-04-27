# Diagrammi Tecnici - Gestione Ordini Ristorante

## 1️⃣ DIAGRAMMA UML - CLASSI PRINCIPALI

```
┌──────────────────────────────────────────────────────────────────────┐
│                          MODELLI                                     │
└──────────────────────────────────────────────────────────────────────┘

                            Prodotto
                        ─────────────────
                        - id_prodotto: int
                        - nome: str
                        - categoria: str
                        - prezzo: float
                        - descrizione: str
                        
                        + __init__()
                        + to_dict()
                        + __repr__()


    RigaOrdine              Ordine              Tavolo
  ─────────────────    ─────────────────    ─────────────────
  - prodotto: Prod     - id_ordine: int     - numero: int
  - quantita: int      - id_tavolo: int     - posti: int
  - note: str          - righe: List        - ordine_attivo: Ord
                       - stato: StatoOrdine - occupato: bool
                       - data_creazione
                       - data_modifica      + crea_nuovo_ordine()
                                           + chiudi_ordine()
  + get_subtotale()    + aggiungi_prodotto()
                       + rimuovi_prodotto()
                       + modifica_quantita()
                       + get_totale()
                       + get_numero_articoli()
                       + cambia_stato()
                       + is_vuoto()
```

---

## 2️⃣ ARCHITETTURA LAYERS

```
┌───────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (GUI)                        │
│              InterfacciaOrdini (PyQt5)                            │
│  - Visualizzazione tavoli                                         │
│  - Visualizzazione menu                                           │
│  - Visualizzazione ordine attivo                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ interact
                          ▼
┌───────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                             │
│              GestioneOrdini                                        │
│  - Gestione tavoli                                                │
│  - Gestione ordini                                                │
│  - Validazioni                                                    │
│  - Calcoli (totali, statistiche)                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │ uses
                          ▼
┌───────────────────────────────────────────────────────────────────┐
│                 DATA ACCESS LAYER (DAO)                            │
│              DatabaseOrdini                                        │
│  - Salva/recupera ordini                                          │
│  - Gestisce prodotti                                              │
│  - Query database                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │ uses
                          ▼
┌───────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                      │
│           SQLite Database (ristorante_ordini.db)                  │
│  - Tabella prodotti                                               │
│  - Tabella ordini                                                 │
│  - Tabella righe_ordini                                           │
└───────────────────────────────────────────────────────────────────┘
```

---

## 3️⃣ RELAZIONI DATABASE

```
                    PRODOTTI
                   ──────────
                   id_prodotto (PK)
                   nome
                   categoria
                   prezzo
                   descrizione
                       │
                       │ 1:N
                       │
    ORDINI          RIGHE_ORDINI        
   ────────────     ──────────────      
   id_ordine (PK)   id_riga (PK)        
   id_tavolo        id_ordine (FK)  ───┐
   stato            id_prodotto (FK)──┐ │
   totale           quantita          │ │
   data_creazione   prezzo_unitario   │ │
   data_modifica    note              │ │
   data_chiusura                      │ │
                                  ┌───┴─┘
                                  │
                                  └─────► FK a PRODOTTI
```

---

## 4️⃣ FLUSSO DI UTILIZZO - USE CASE DIAGRAM

```
                          Cameriere
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
    ┌────────────┐    ┌──────────────┐    ┌─────────────┐
    │ Seleziona  │    │  Aggiunge    │    │   Modifica  │
    │  Tavolo    │    │  Prodotto    │    │   Ordine    │
    └────────────┘    └──────────────┘    └─────────────┘
        │                     │                     │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Cambia Stato     │
                    │  Ordine           │
                    └───────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
                [Preparaz] [Servito] [Pagato]
                    │         │         │
                    └─────────┼─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Libera Tavolo     │
                    └───────────────────┘
                              │
                              ▼
                    [Salva in Database]
```

---

## 5️⃣ FLUSSO DATI - SEQUENZA OPERAZIONE

```
Cameriere          GUI              GestioneOrdini        Database
    │               │                       │                │
    │─ Seleziona ──→│                       │                │
    │  Tavolo       │                       │                │
    │               │─ occupa_tavolo() ───→│                │
    │               │                       │                │
    │               │◄─ ordine_nuovo ──────│                │
    │               │                       │                │
    │─ Aggiungi ───→│                       │                │
    │  Prodotto     │─ aggiungi_al_ordine()→│                │
    │               │  (modelli.py)         │                │
    │               │◄─ ordine_aggiornato ─│                │
    │               │                       │                │
    │               │ [ripeti per altri     │                │
    │               │  prodotti]            │                │
    │               │                       │                │
    │─ Cambia ─────→│                       │                │
    │  Stato        │─ cambia_stato() ─────→│                │
    │  "In Prep"    │                       │                │
    │               │                       │─ aggiorna ────→│
    │               │                       │  ordini        │
    │               │                       │◄─ success ─────│
    │               │◄─ stato_aggiornato ──│                │
    │               │                       │                │
    │─ Libera ─────→│                       │                │
    │  Tavolo       │─ libera_tavolo() ────→│                │
    │               │                       │─ salva ───────→│
    │               │                       │  ordine        │
    │               │                       │◄─ success ─────│
    │               │◄─ tavolo_libero ──────│                │
    │               │                       │                │
```

---

## 6️⃣ STATI ORDINE - STATE MACHINE

```
              ┌─────────────────────┐
              │   IN SOSPESO        │  ◄─── Creazione ordine
              │  (Nuovo Ordine)     │
              └──────────┬──────────┘
                         │
                         │ click "In Preparazione"
                         ▼
              ┌─────────────────────┐
              │  IN PREPARAZIONE    │
              │ (Mandato in cucina) │
              └──────────┬──────────┘
                         │
                         │ click "Servito"
                         ▼
              ┌─────────────────────┐
              │     SERVITO         │
              │  (Piatto al tavolo) │
              └──────────┬──────────┘
                         │
                         │ click "Pagato"
                         ▼
              ┌─────────────────────┐
              │     PAGATO          │  ◄─── Ordine Chiuso
              │  (Ordine Concluso)  │
              └─────────────────────┘

              (Transizione possibile da qualsiasi stato)
                         │
                         ▼
              ┌─────────────────────┐
              │    ANNULLATO        │
              │  (Ordine Eliminato) │
              └─────────────────────┘
```

---

## 7️⃣ LAYOUT GUI - WIREFRAME DETTAGLIATO

```
┌────────────────────────────────────────────────────────────────────────┐
│  GESTIONE ORDINI RISTORANTE                                    Min Max ◄─┤
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐   │
│  │   TAVOLI    │  │      MENU        │  │   ORDINE ATTIVO        │   │
│  │             │  │                  │  │                        │   │
│  │  [T1] [T2]  │  │ Categoria ▼      │  │ Tavolo 3 - €50.00      │   │
│  │  [T3] [T4]  │  │ [Bevande       ]  │  │                        │   │
│  │  [T5] [T6]  │  │                  │  │ ┌────────────────────┐ │   │
│  │             │  │ Coca Cola   €2   │  │ │ Nome│€│ Qtà│Tot│   │ │   │
│  │ ┌─────────┐ │  │ [Aggiungi]       │  │ │    │ │    │   │   │ │   │
│  │ │ Occupa  │ │  │                  │  │ │ Coke│2│ 2 │€4 │X  │ │   │
│  │ │ Tavolo  │ │  │ Prosecco    €5   │  │ │ Spag│1│ 1 │€9 │X  │ │   │
│  │ └─────────┘ │  │ [Aggiungi]       │  │ │    │ │    │   │   │ │   │
│  │             │  │                  │  │ └────────────────────┘ │   │
│  │ ┌─────────┐ │  │ Caffè       €1   │  │                        │   │
│  │ │ Libera  │ │  │ [Aggiungi]       │  │ TOTALE: €13.00         │   │
│  │ │ Tavolo  │ │  │                  │  │                        │   │
│  │ └─────────┘ │  │ [Scorri Giù]     │  │ ┌──────────────┐       │   │
│  │             │  │                  │  │ │ In Preparaz. │ ┌──┐ │   │
│  │  [Scorri]   │  │                  │  │ │ Servito      │ │  │ │   │
│  │             │  │                  │  │ │ Pagato       │ │  │ │   │
│  │             │  │                  │  │ └──────────────┘ └──┘ │   │
│  └─────────────┘  └──────────────────┘  └────────────────────────┘   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 8️⃣ SCHEMA DIRECTORY PROGETTO

```
ristorante-ordini/
│
├── modelli.py
│   ├── Prodotto
│   ├── RigaOrdine
│   ├── Ordine
│   ├── Tavolo
│   └── StatoOrdine (Enum)
│
├── database.py
│   └── DatabaseOrdini
│       ├── Tabella prodotti
│       ├── Tabella ordini
│       └── Tabella righe_ordini
│
├── gestione_ordini.py
│   └── GestioneOrdini
│       ├── Gestione tavoli
│       ├── Gestione ordini
│       └── Interfaccia con DB
│
├── interfaccia_grafica.py
│   └── InterfacciaOrdini (PyQt5)
│       ├── Panel Tavoli
│       ├── Panel Menu
│       └── Panel Ordine Attivo
│
├── setup_database.py
│   └── Inizializzazione menu demo
│
├── ristorante_ordini.db
│   ├── prodotti (30 items)
│   ├── ordini
│   └── righe_ordini
│
├── DOCUMENTAZIONE.md
│   └── Guida completa
│
└── README.md
    └── Quick start
```

---

## 9️⃣ INTERAZIONI CLASSI

```
┌─────────────────────────────────────────────────────────────────┐
│                 InterfacciaOrdini (GUI)                         │
│  Utente interagisce qui ◄───────────────────────────────────┐   │
└──────────────────────────┬──────────────────────────────────┘   │
                          │                                        │
                         uses                                      │
                          │                                        │
                          ▼                                        │
         ┌────────────────────────────────────┐                   │
         │    GestioneOrdini                  │                   │
         │  - Orchestrazione logica           │                   │
         │  - Validazioni                     │                   │
         │  - Calcoli                         │                   │
         └────────────┬───────────────────────┘                   │
                      │                                           │
           ┌──────────┼──────────┐                                │
           │          │          │                               │
        uses       uses       uses                               │
           │          │          │                               │
           ▼          ▼          ▼                               │
      ┌────────┐┌────────┐┌────────────────┐                    │
      │ Tavolo ││Ordine  ││DatabaseOrdini  │                    │
      └────────┘└────────┘│  (DAO)         │                    │
           │          │   │ - Salva        │                    │
           │       contains  - Carica      │                    │
           │          │   │ - Elimina      │                    │
           ▼          ▼   └─────┬──────────┘                    │
      ┌────────────────────┐    │                               │
      │   RigaOrdine       │    │ uses                          │
      │ - Prodotto         │    │    │                          │
      │ - Quantita         │    │    ▼                          │
      │ - Note             │    │ ┌──────────────────┐          │
      └────────────────────┘    │ │ SQLite Database  │          │
           │                    │ │ ristorante.db    │          │
        contains                │ │                  │          │
           │                    │ │ - prodotti       │          │
           ▼                    │ │ - ordini         │          │
      ┌─────────────────┐      │ │ - righe_ordini   │          │
      │   Prodotto      │      │ └──────────────────┘          │
      │ - id_prodotto   │      │                               │
      │ - nome          │      │                               │
      │ - categoria     │      └───────────────────────────────┘
      │ - prezzo        │
      └─────────────────┘
```

---

## 🔟 TABELLA TRANSIZIONI STATO

```
┌────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  DA STATO      │ → Preparaz   │ → Servito    │ → Pagato     │ → Annullato  │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ IN SOSPESO     │ ✓ Permesso   │ ✓ Permesso   │ ✓ Permesso   │ ✓ Permesso   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ IN PREPARAZ.   │ ✓ Permesso   │ ✓ Permesso   │ ✓ Permesso   │ ✓ Permesso   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ SERVITO        │ ✓ Permesso   │ ✓ Permesso   │ ✓ Permesso   │ ✓ Permesso   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ PAGATO         │ ✗ No         │ ✗ No         │ ✓ Permesso   │ ✓ Permesso   │
├────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ ANNULLATO      │ ✗ No         │ ✗ No         │ ✗ No         │ ✓ (già qui)  │
└────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 1️⃣1️⃣ FLUSSO DATI MODULO DATABASE

```
┌──────────────────────────────────────────────────────────────────┐
│           DatabaseOrdini - Data Access Object (DAO)              │
│                                                                  │
│  SQL Queries ◄──────────────────────────────────────────────    │
│      │                                                      │    │
│      ├─ INSERT prodotto                                   │    │
│      ├─ SELECT prodotti by categoria                      │    │
│      ├─ INSERT ordine + righe                             │    │
│      ├─ UPDATE ordine stato                               │    │
│      ├─ DELETE righe_ordini                               │    │
│      ├─ SELECT ordine by id                               │    │
│      ├─ SELECT ordini by stato                            │    │
│      └─ DELETE ordine                                     │    │
│      │                                                     │    │
│      ▼                                                     │    │
│  ┌─────────────────────────────────────┐                 │    │
│  │   sqlite3.Connection                │                 │    │
│  │ (ristorante_ordini.db)              │                 │    │
│  └──────────────┬──────────────────────┘                 │    │
│                 │                                         │    │
│                 ▼                                         │    │
│  ┌────────────────────────────────────────────────────┐  │    │
│  │  SQLite File Database                             │  │    │
│  │                                                    │  │    │
│  │  ┌──────────────────────────────────────────────┐ │  │    │
│  │  │ TABLE prodotti                               │ │  │    │
│  │  │ - id_prodotto (PK)                           │ │  │    │
│  │  │ - nome, categoria, prezzo, descrizione       │ │  │    │
│  │  │ - 30 righe iniziali                          │ │  │    │
│  │  └──────────────────────────────────────────────┘ │  │    │
│  │                                                    │  │    │
│  │  ┌──────────────────────────────────────────────┐ │  │    │
│  │  │ TABLE ordini                                 │ │  │    │
│  │  │ - id_ordine (PK auto-increment)              │ │  │    │
│  │  │ - id_tavolo, stato, totale                   │ │  │    │
│  │  │ - data_creazione, data_modifica, chiusura    │ │  │    │
│  │  └──────────────────────────────────────────────┘ │  │    │
│  │                                                    │  │    │
│  │  ┌──────────────────────────────────────────────┐ │  │    │
│  │  │ TABLE righe_ordini                           │ │  │    │
│  │  │ - id_riga (PK auto-increment)                │ │  │    │
│  │  │ - id_ordine (FK), id_prodotto (FK)           │ │  │    │
│  │  │ - quantita, prezzo_unitario, note            │ │  │    │
│  │  └──────────────────────────────────────────────┘ │  │    │
│  │                                                    │  │    │
│  └────────────────────────────────────────────────────┘  │    │
│                 ▲                                         │    │
│                 │ persists/loads                          │    │
│                 └──────────────────────────────────────────┘    │
│                                                                  │
│  GestioneOrdini ◄── Reads/Writes Objects ────────────────────   │
│      │                                                           │
│      ▼                                                           │
│   GUI Updates                                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1️⃣2️⃣ ANALISI DI COMPLESSITÀ

| Operazione | Complessità | Descrizione |
|------------|------------|-------------|
| Aggiungi prodotto | O(1) | Inserimento singolo DB |
| Carica categoria | O(n) | n = prodotti in categoria |
| Crea ordine | O(1) | Creazione semplice |
| Aggiungi a ordine | O(m) | m = righe in ordine (cerca duplicate) |
| Salva ordine | O(m) | m = righe da salvare |
| Carica ordine | O(m) | m = righe dell'ordine |
| Modifica stato | O(1) | Update singolo record |
| Statistiche | O(k) | k = ordini totali |

---

Questa documentazione tecnica fornisce una vista completa della struttura, flussi dati e relazioni tra i componenti del sistema.