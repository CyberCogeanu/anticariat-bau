/**
 * Anticariat Albert - Executive Operator Portal Logic
 * Implements low-friction daily workflows for Marius's mother:
 * 1. Daily order packing with shelf coordinates and 1-click AWB generation
 * 2. Rapid book intake (<30 seconds) with bibliographic autocomplete and shelf locking
 * 3. Daily/monthly sales pulse
 * 4. Competitor Power Index & feature approval cards
 * 
 * Zero Unicode em dash (U+2014) is used in this file.
 */

import {
  INITIAL_ORDERS,
  CATALOG_AUTOCOMPLETE_KNOWLEDGE,
  COMPETITOR_LEADERBOARD,
  FEATURE_RADAR_CARDS,
  SALES_PULSE_SUMMARY
} from './mock_data.js?v=20261003_v4';

class OperatorPortalApp {
  constructor() {
    this.storageKeyOrders = 'anticariat_orders_v1';
    this.storageKeyFeatures = 'anticariat_features_v1';
    this.storageKeyIngested = 'anticariat_ingested_books_v1';
    this.storageKeyShelf = 'anticariat_active_shelf_v1';

    this.orders = this.loadState(this.storageKeyOrders, INITIAL_ORDERS);
    this.featureCards = this.loadState(this.storageKeyFeatures, FEATURE_RADAR_CARDS);
    this.ingestedBooks = this.loadState(this.storageKeyIngested, []);
    this.activeShelf = localStorage.getItem(this.storageKeyShelf) || 'C1-R04-S2';

    this.currentScore = SALES_PULSE_SUMMARY.albert_points + (this.ingestedBooks.length * 5);

    this.initElements();
    this.attachEventListeners();
    this.renderAll();
  }

  loadState(key, fallback) {
    try {
      const saved = localStorage.getItem(key);
      if (!saved) return JSON.parse(JSON.stringify(fallback));
      const parsed = JSON.parse(saved);
      if (Array.isArray(fallback) && fallback.length > 0 && fallback[0].id) {
        const existingIds = new Set(parsed.map(item => item.id));
        fallback.forEach(item => {
          if (!existingIds.has(item.id)) {
            parsed.push(JSON.parse(JSON.stringify(item)));
          }
        });
      }
      return parsed;
    } catch (e) {
      console.warn('Error loading localStorage key', key, e);
      return JSON.parse(JSON.stringify(fallback));
    }
  }

  saveState(key, data) {
    try {
      localStorage.setItem(key, JSON.stringify(data));
    } catch (e) {
      console.warn('Error saving localStorage key', key, e);
    }
  }

  initElements() {
    // Navigation Tabs
    this.tabButtons = document.querySelectorAll('.nav-tab-btn');
    this.tabPanes = document.querySelectorAll('.tab-pane');

    // Orders Containers
    this.ordersListEl = document.getElementById('ordersList');
    this.badgeOrdersPending = document.getElementById('badgeOrdersPending');
    this.metricOrdersToday = document.getElementById('metricOrdersToday');

    // Ingestion Elements
    this.shelfLockTag = document.getElementById('shelfLockTag');
    this.btnChangeShelf = document.getElementById('btnChangeShelf');
    this.inputTitle = document.getElementById('inputBookTitle');
    this.autocompleteList = document.getElementById('autocompleteList');
    this.inputAuthor = document.getElementById('inputBookAuthor');
    this.inputPublisher = document.getElementById('inputBookPublisher');
    this.inputYear = document.getElementById('inputBookYear');
    this.inputPages = document.getElementById('inputBookPages');
    this.inputPrice = document.getElementById('inputBookPrice');
    this.bindingSelect = document.getElementById('selectBookBinding');
    this.conditionChips = document.querySelectorAll('#conditionChips .chip-option');
    this.flawChips = document.querySelectorAll('#flawChips .chip-option');
    this.photoInput = document.getElementById('photoInput');
    this.photoPreview = document.getElementById('photoPreview');
    this.btnSaveBook = document.getElementById('btnSaveBook');
    this.ingestedCounter = document.getElementById('ingestedCounter');
    this.selectedCondition = 'Buna';

    // Power Index & Radar
    this.powerScoreEl = document.getElementById('albertPowerScore');
    this.leaderboardTableBody = document.getElementById('leaderboardTableBody');
    this.featureRadarGrid = document.getElementById('featureRadarGrid');

    // Modal
    this.modalOverlay = document.getElementById('modalOverlay');
    this.modalTitle = document.getElementById('modalTitle');
    this.modalBody = document.getElementById('modalBody');
    this.modalCloseBtn = document.getElementById('modalCloseBtn');
  }

  attachEventListeners() {
    // Tab switching
    this.tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        this.switchTab(targetTab);
      });
    });

    // Modal close
    if (this.modalCloseBtn) {
      this.modalCloseBtn.addEventListener('click', () => this.closeModal());
    }
    if (this.modalOverlay) {
      this.modalOverlay.addEventListener('click', (e) => {
        if (e.target === this.modalOverlay) this.closeModal();
      });
    }

    // Shelf change button
    if (this.btnChangeShelf) {
      this.btnChangeShelf.addEventListener('click', () => {
        const newShelf = prompt('Introduceți noul cod de raft (ex: C1-R02-S3):', this.activeShelf);
        if (newShelf && newShelf.trim()) {
          this.activeShelf = newShelf.trim().toUpperCase();
          localStorage.setItem(this.storageKeyShelf, this.activeShelf);
          this.shelfLockTag.textContent = this.activeShelf;
          this.showToast(`Raft activ setat la: ${this.activeShelf}`);
        }
      });
    }

    // Autocomplete for title input
    if (this.inputTitle) {
      this.inputTitle.addEventListener('input', (e) => this.handleTitleInput(e.target.value));
      document.addEventListener('click', (e) => {
        if (!e.target.closest('#titleFormGroup')) {
          this.autocompleteList.style.display = 'none';
        }
      });
    }

    // Condition chips
    this.conditionChips.forEach(chip => {
      chip.addEventListener('click', () => {
        this.conditionChips.forEach(c => c.classList.remove('selected'));
        chip.classList.add('selected');
        this.selectedCondition = chip.getAttribute('data-value');
      });
    });

    // Flaw chips toggle
    this.flawChips.forEach(chip => {
      chip.addEventListener('click', () => {
        chip.classList.toggle('selected');
      });
    });

    // Photo input preview
    if (this.photoInput) {
      this.photoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = (event) => {
            this.photoPreview.src = event.target.result;
            this.photoPreview.style.display = 'block';
          };
          reader.readAsDataURL(file);
        }
      });
    }

    // Save Book Intake
    if (this.btnSaveBook) {
      this.btnSaveBook.addEventListener('click', () => this.handleBookSave());
    }
  }

  switchTab(tabId) {
    this.tabButtons.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });
    this.tabPanes.forEach(pane => {
      pane.classList.toggle('active', pane.id === tabId);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  showToast(message) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
      <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  openModal(titleHtml, bodyHtml) {
    if (!this.modalOverlay) return;
    this.modalTitle.innerHTML = titleHtml;
    this.modalBody.innerHTML = bodyHtml;
    this.modalOverlay.classList.add('active');
  }

  closeModal() {
    if (!this.modalOverlay) return;
    this.modalOverlay.classList.remove('active');
  }

  renderAll() {
    this.renderOrders();
    this.renderLeaderboard();
    this.renderFeatureRadar();
    this.updateMetrics();
  }

  /* 1. Orders and Packing Module */
  renderOrders() {
    if (!this.ordersListEl) return;
    this.ordersListEl.innerHTML = '';

    const pendingOrders = this.orders.filter(o => o.status === 'pending_pack');
    if (this.badgeOrdersPending) {
      this.badgeOrdersPending.textContent = pendingOrders.length;
    }
    if (this.metricOrdersToday) {
      this.metricOrdersToday.textContent = pendingOrders.length;
    }

    if (this.orders.length === 0) {
      this.ordersListEl.innerHTML = `
        <div style="text-align: center; padding: 40px; color: var(--text-muted);">
          <p>Nu există comenzi noi pentru astăzi.</p>
        </div>
      `;
      return;
    }

    this.orders.forEach(order => {
      const allPicked = order.items.every(item => item.packed);
      const isShipped = order.status === 'shipped';

      const card = document.createElement('div');
      card.className = `order-ticket ${allPicked ? 'ready-to-ship' : ''}`;
      card.id = `order-${order.id}`;

      let itemsHtml = order.items.map((item, idx) => `
        <div class="book-pick-row ${item.packed ? 'checked' : ''}" data-order="${order.id}" data-item="${idx}">
          <input 
            type="checkbox" 
            class="book-pick-checkbox" 
            ${item.packed ? 'checked' : ''} 
            ${isShipped ? 'disabled' : ''}
            data-order="${order.id}" 
            data-item="${idx}"
          />
          <div class="book-pick-details">
            <div class="book-pick-title">${item.title}</div>
            <div class="book-pick-author">${item.author} (${item.publication_year || 'An necunoscut'}, Ed. ${item.publisher || 'Nespecificată'})</div>
            <div class="book-pick-specs">Legătură: ${item.binding} | Stare: ${item.condition_grade}</div>
          </div>
          <div class="book-shelf-badge">
            <div class="shelf-coordinate" title="Locație fizică în librărie">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="3" width="20" height="14" rx="2"></rect>
                <line x1="8" y1="21" x2="16" y2="21"></line>
                <line x1="12" y1="17" x2="12" y2="21"></line>
              </svg>
              ${item.location_id || 'Fără raft'}
            </div>
            <span class="barcode-reference">Cod: ${item.cod_reference}</span>
          </div>
        </div>
      `).join('');

      card.innerHTML = `
        <div class="order-header">
          <div class="order-id-badge">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="1" y="3" width="15" height="13"></rect>
              <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
              <circle cx="5.5" cy="18.5" r="2.5"></circle>
              <circle cx="18.5" cy="18.5" r="2.5"></circle>
            </svg>
            ${order.id}
          </div>
          <div class="order-meta-chips">
            <span class="chip chip-city">${order.customer_display}</span>
            <span class="chip chip-delivery">${order.delivery_method}</span>
            <span class="chip chip-payment">${order.payment_status}</span>
          </div>
        </div>

        <div class="order-books-list">
          ${itemsHtml}
        </div>

        <div class="order-footer">
          <div class="order-total-block">
            Valoare comandă: <strong>${order.total_ron.toFixed(2)} RON</strong>
          </div>
          <div class="order-action-buttons">
            ${isShipped ? `
              <span style="color: var(--status-green); font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                AWB Generat: ${order.awb_code}
              </span>
              <button class="btn-secondary" onclick="window.portalApp.printMockAWB('${order.id}')">
                Retipărește AWB
              </button>
            ` : `
              <button 
                class="btn-primary" 
                id="btn-awb-${order.id}" 
                ${!allPicked ? 'style="opacity: 0.5;"' : ''}
                onclick="window.portalApp.generateAWB('${order.id}')"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 9V2h12v7"></path>
                  <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                  <rect x="6" y="14" width="12" height="8"></rect>
                </svg>
                ${allPicked ? 'Generează AWB & Confirmă' : 'Bifați cărțile culese'}
              </button>
            `}
          </div>
        </div>
      `;

      this.ordersListEl.appendChild(card);
    });

    // Add checkbox event listeners
    this.ordersListEl.querySelectorAll('.book-pick-checkbox').forEach(cb => {
      cb.addEventListener('change', (e) => {
        const orderId = e.target.getAttribute('data-order');
        const itemIdx = parseInt(e.target.getAttribute('data-item'), 10);
        this.toggleBookPacked(orderId, itemIdx, e.target.checked);
      });
    });
  }

  toggleBookPacked(orderId, itemIdx, isChecked) {
    const order = this.orders.find(o => o.id === orderId);
    if (!order) return;

    order.items[itemIdx].packed = isChecked;
    this.saveState(this.storageKeyOrders, this.orders);
    this.renderOrders();

    if (isChecked) {
      this.showToast('Carte bifată ca culeasă din raft.');
    }
  }

  generateAWB(orderId) {
    const order = this.orders.find(o => o.id === orderId);
    if (!order) return;

    const allPicked = order.items.every(i => i.packed);
    if (!allPicked) {
      alert('Vă rugăm să bifați toate cărțile din comandă înainte de a genera eticheta de curier.');
      return;
    }

    const mockAWB = 'FAN-' + Math.floor(10000000 + Math.random() * 90000000);
    order.status = 'shipped';
    order.awb_code = mockAWB;
    this.saveState(this.storageKeyOrders, this.orders);
    this.renderOrders();

    this.printMockAWB(orderId);
  }

  printMockAWB(orderId) {
    const order = this.orders.find(o => o.id === orderId);
    if (!order) return;

    const modalTitle = `
      <div style="display: flex; align-items: center; gap: 10px;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--status-green)" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        Etichetă AWB Generată cu Succes
      </div>
    `;

    const modalBody = `
      <div style="background: #ffffff; color: #111827; padding: 20px; border-radius: 8px; font-family: sans-serif;">
        <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #111827; padding-bottom: 10px; margin-bottom: 12px;">
          <div>
            <h4 style="font-size: 1.2rem; font-weight: 800; margin: 0;">FAN COURIER</h4>
            <p style="font-size: 0.75rem; margin: 0; color: #4b5563;">STANDARD EXPRESS LIVRARE</p>
          </div>
          <div style="text-align: right;">
            <p style="font-family: monospace; font-size: 1.1rem; font-weight: bold; margin: 0;">${order.awb_code}</p>
            <p style="font-size: 0.75rem; margin: 0; color: #4b5563;">Ref: ${order.id}</p>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.82rem; margin-bottom: 14px;">
          <div style="background: #f3f4f6; padding: 8px; border-radius: 4px;">
            <strong>EXPEDITOR:</strong><br>
            Anticariat Albert<br>
            Str. Alexandru Lăpușneanu 11<br>
            Iași, 700259<br>
            Tel: 0760806656
          </div>
          <div style="background: #f3f4f6; padding: 8px; border-radius: 4px;">
            <strong>DESTINATAR:</strong><br>
            ${order.customer_display}<br>
            Oraș: ${order.destination_city}<br>
            Plată: ${order.payment_status}
          </div>
        </div>

        <div style="border-top: 1px dashed #9ca3af; padding-top: 8px; font-size: 0.8rem; margin-bottom: 16px;">
          <strong>Conținut colet:</strong>
          <ul style="margin: 4px 0 0 16px; padding: 0;">
            ${order.items.map(i => `<li>${i.title} (Cod sticker: ${i.cod_reference})</li>`).join('')}
          </ul>
        </div>

        <div style="text-align: center; padding: 10px 0; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 4px;">
          <div style="font-family: monospace; font-size: 1.4rem; letter-spacing: 4px; font-weight: bold;">
            ||| | |||| || ||||| |||| |
          </div>
          <div style="font-family: monospace; font-size: 0.8rem; color: #374151;">*${order.awb_code}*</div>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
        <button class="btn-secondary" onclick="window.portalApp.closeModal()">Închide</button>
        <button class="btn-success" onclick="window.print();">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 6 2 18 2 18 9"></polyline>
            <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
            <rect x="6" y="14" width="12" height="8"></rect>
          </svg>
          Tipărește Etichetă AWB
        </button>
      </div>
    `;

    this.openModal(modalTitle, modalBody);
  }

  /* 2. Rapid Book Ingestion (<30 Seconds) */
  handleTitleInput(query) {
    if (!query || query.trim().length < 2) {
      this.autocompleteList.style.display = 'none';
      return;
    }

    const clean = query.trim().toLowerCase();
    const matches = CATALOG_AUTOCOMPLETE_KNOWLEDGE.filter(book => 
      book.title.toLowerCase().includes(clean) || book.author.toLowerCase().includes(clean)
    );

    if (matches.length === 0) {
      this.autocompleteList.style.display = 'none';
      return;
    }

    this.autocompleteList.innerHTML = matches.map((book, idx) => `
      <div class="autocomplete-item" data-index="${idx}">
        <div class="autocomplete-item-title">${book.title}</div>
        <div class="autocomplete-item-meta">${book.author} | Ed. ${book.publisher} (${book.publication_year}) | ${book.binding}</div>
      </div>
    `).join('');

    this.autocompleteList.style.display = 'block';

    this.autocompleteList.querySelectorAll('.autocomplete-item').forEach(item => {
      item.addEventListener('click', () => {
        const idx = parseInt(item.getAttribute('data-index'), 10);
        this.selectAutocompleteBook(matches[idx]);
      });
    });
  }

  selectAutocompleteBook(book) {
    this.inputTitle.value = book.title;
    this.inputAuthor.value = book.author;
    this.inputPublisher.value = book.publisher;
    this.inputYear.value = book.publication_year;
    this.inputPages.value = book.page_count;
    this.bindingSelect.value = book.binding;
    this.inputPrice.value = book.suggested_price_ron.toFixed(2);
    this.autocompleteList.style.display = 'none';

    this.showToast(`Autocompletat bibliografic din catalog: ${book.author}`);
  }

  handleBookSave() {
    const title = this.inputTitle.value.trim();
    const author = this.inputAuthor.value.trim();
    const price = parseFloat(this.inputPrice.value);

    if (!title || !author || isNaN(price) || price <= 0) {
      alert('Vă rugăm să introduceți cel puțin Titlul, Autorul și un Preț valid în RON.');
      return;
    }

    const nextId = 37380 + this.ingestedBooks.length + 1;
    const nextCod = '1' + nextId;

    const selectedFlaws = [];
    document.querySelectorAll('#flawChips .chip-option.selected').forEach(c => {
      selectedFlaws.push(c.getAttribute('data-value'));
    });

    const newBook = {
      id_legacy: nextId,
      cod_reference: nextCod,
      title: title,
      author: author,
      publisher: this.inputPublisher.value.trim() || 'Nespecificată',
      publication_year: parseInt(this.inputYear.value, 10) || null,
      page_count: parseInt(this.inputPages.value, 10) || null,
      binding: this.bindingSelect.value,
      condition_grade: this.selectedCondition,
      condition_notes: selectedFlaws.join(', ') || 'Fără defecte majore',
      price_ron: price,
      location_id: this.activeShelf,
      created_at: new Date().toISOString()
    };

    this.ingestedBooks.unshift(newBook);
    this.saveState(this.storageKeyIngested, this.ingestedBooks);

    // Increase Power Index score by 5 pts per book
    this.currentScore += 5;
    this.updateMetrics();
    this.renderLeaderboard();

    // Show sticker print modal
    this.showPrintStickerModal(newBook);

    // Clear form while preserving the locked shelf
    this.inputTitle.value = '';
    this.inputAuthor.value = '';
    this.inputPublisher.value = '';
    this.inputYear.value = '';
    this.inputPages.value = '';
    this.inputPrice.value = '';
    this.photoInput.value = '';
    this.photoPreview.style.display = 'none';
    document.querySelectorAll('#flawChips .chip-option').forEach(c => c.classList.remove('selected'));
  }

  showPrintStickerModal(book) {
    const modalTitle = `
      <div style="display: flex; align-items: center; gap: 10px;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent-gold)" stroke-width="2">
          <polyline points="6 9 6 2 18 2 18 9"></polyline>
          <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
          <rect x="6" y="14" width="12" height="8"></rect>
        </svg>
        Etichetă Sticker Raft Generată
      </div>
    `;

    const modalBody = `
      <div style="background: #ffffff; color: #111827; padding: 18px; border-radius: 8px; text-align: center; border: 2px solid #111827;">
        <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: bold; letter-spacing: 1px; color: #4b5563;">
          ANTICARIAT ALBERT - IAȘI
        </div>
        <div style="font-family: serif; font-size: 1.15rem; font-weight: bold; margin: 6px 0 2px;">
          ${book.title}
        </div>
        <div style="font-size: 0.85rem; color: #374151; margin-bottom: 8px;">
          ${book.author} (${book.publication_year || ''})
        </div>
        
        <div style="display: flex; justify-content: space-around; align-items: center; background: #f3f4f6; padding: 8px; border-radius: 4px; margin-bottom: 10px;">
          <div>
            <div style="font-size: 0.7rem; color: #6b7280;">RAFT FIZIC</div>
            <div style="font-family: monospace; font-size: 1.1rem; font-weight: bold; color: #1e40af;">
              ${book.location_id}
            </div>
          </div>
          <div>
            <div style="font-size: 0.7rem; color: #6b7280;">PREȚ</div>
            <div style="font-family: monospace; font-size: 1.25rem; font-weight: 800; color: #b45309;">
              ${book.price_ron.toFixed(2)} LEI
            </div>
          </div>
        </div>

        <div style="font-family: monospace; font-size: 1.6rem; letter-spacing: 4px; font-weight: bold;">
          ||| |||| | ||| |||| || |
        </div>
        <div style="font-family: monospace; font-size: 0.85rem; font-weight: bold; color: #111827;">
          COD: ${book.cod_reference}
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
        <span style="font-size: 0.85rem; color: var(--status-green);">
          +5 Puncte Index adăugate în clasament!
        </span>
        <div style="display: flex; gap: 10px;">
          <button class="btn-secondary" onclick="window.portalApp.closeModal()">Gata / Următoarea</button>
          <button class="btn-primary" onclick="window.print();">Tipărește Sticker</button>
        </div>
      </div>
    `;

    this.openModal(modalTitle, modalBody);
  }

  /* 3. Competitor Power Index & Leaderboard */
  renderLeaderboard() {
    if (!this.leaderboardTableBody) return;

    // Update Albert's score
    const updatedLeaderboard = COMPETITOR_LEADERBOARD.map(c => {
      if (c.domain === 'anticariatalbert.com') {
        return {
          ...c,
          score: this.currentScore,
          score_display: this.currentScore.toLocaleString('ro-RO'),
          catalog_volume: `${(12488 + this.ingestedBooks.length).toLocaleString('ro-RO')} în stoc activ`
        };
      }
      return c;
    });

    // Sort by score descending
    updatedLeaderboard.sort((a, b) => b.score - a.score);

    this.leaderboardTableBody.innerHTML = updatedLeaderboard.map((item, idx) => {
      const isAlbert = item.domain === 'anticariatalbert.com';
      let rankBadgeClass = '';
      if (idx === 0) rankBadgeClass = 'rank-gold';
      else if (idx === 1) rankBadgeClass = 'rank-silver';
      else if (idx === 2) rankBadgeClass = 'rank-bronze';

      return `
        <tr class="${isAlbert ? 'row-albert' : ''}">
          <td style="width: 50px;">
            <span class="rank-badge ${rankBadgeClass}">${idx + 1}</span>
          </td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
              <strong style="${isAlbert ? 'color: var(--accent-gold); font-size: 1.02rem;' : ''}">${item.name}</strong>
              ${item.badge ? `<span style="font-size: 0.72rem; padding: 2px 7px; border-radius: 10px; background: ${isAlbert ? 'rgba(212, 163, 115, 0.25)' : 'rgba(255,255,255,0.06)'}; color: ${isAlbert ? 'var(--accent-gold-light)' : 'var(--text-dim)'}; border: 1px solid ${isAlbert ? 'var(--accent-gold)' : 'var(--border-subtle)'};">${item.badge}</span>` : ''}
            </div>
            <div style="font-size: 0.78rem; color: var(--text-dim); margin-top: 2px;">${item.domain} • ${item.headquarters}</div>
          </td>
          <td>${item.catalog_volume}</td>
          <td>${item.monthly_traffic}</td>
          <td style="font-family: var(--font-mono); font-weight: 700; color: ${isAlbert ? 'var(--accent-gold)' : 'var(--text-main)'};">
            ${item.score_display} pts
          </td>
        </tr>
      `;
    }).join('');
  }

  /* 4. Feature Radar Approval Cards */
  renderFeatureRadar() {
    if (!this.featureRadarGrid) return;

    this.featureRadarGrid.innerHTML = this.featureCards.map(card => {
      let statusClass = '';
      if (card.status === 'approved') statusClass = 'decided-yes';
      if (card.status === 'rejected') statusClass = 'decided-no';

      return `
        <div class="feature-card ${statusClass}" id="card-${card.id}">
          <div>
            <span class="feature-source-badge">Inspirat de: ${card.competitor}</span>
            <div class="feature-title">${card.title}</div>
            <div class="feature-benefit">${card.benefit_summary}</div>
            <div class="feature-impact">Impact estimat: ${card.impact_score}</div>
          </div>

          <div class="feature-actions-row">
            ${card.status === 'approved' ? `
              <span style="color: var(--status-green); font-weight: 700; font-size: 0.9rem; display: flex; align-items: center; gap: 6px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Aprobat pentru Tema Shopify!
              </span>
            ` : card.status === 'rejected' ? `
              <span style="color: var(--text-dim); font-size: 0.85rem;">Respins de către operator</span>
            ` : `
              <button class="btn-card-decision btn-card-yes" onclick="window.portalApp.decideFeature('${card.id}', 'approved')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Vreau pe Shopify: DA
              </button>
              <button class="btn-card-decision btn-card-no" onclick="window.portalApp.decideFeature('${card.id}', 'rejected')">
                NU
              </button>
            `}
          </div>
        </div>
      `;
    }).join('');
  }

  decideFeature(featureId, decision) {
    const card = this.featureCards.find(f => f.id === featureId);
    if (!card) return;

    card.status = decision;
    this.saveState(this.storageKeyFeatures, this.featureCards);

    if (decision === 'approved') {
      this.currentScore += 10000;
      this.showToast('Funcționalitate aprobată! +10.000 puncte index adăugate.');
    } else {
      this.showToast('Opțiune marcată ca respinsă.');
    }

    this.updateMetrics();
    this.renderFeatureRadar();
    this.renderLeaderboard();
  }

  updateMetrics() {
    if (this.powerScoreEl) {
      this.powerScoreEl.textContent = this.currentScore.toLocaleString('ro-RO');
    }
    if (this.ingestedCounter) {
      this.ingestedCounter.textContent = this.ingestedBooks.length;
    }
    if (this.shelfLockTag) {
      this.shelfLockTag.textContent = this.activeShelf;
    }

    const progressFill = document.getElementById('powerProgressFill');
    if (progressFill) {
      const pct = Math.min(100, Math.round((this.currentScore / SALES_PULSE_SUMMARY.target_stage_points) * 100));
      progressFill.style.width = `${pct}%`;
    }
  }
}

// Global bootstrap
document.addEventListener('DOMContentLoaded', () => {
  window.portalApp = new OperatorPortalApp();
});
