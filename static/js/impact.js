/**
 * PRANVYRA Impact Tracker, Receipts Ledger & Sustainable Alternatives
 * Feature 6: Verified Environmental Impact Accounting & Personal Receipt Modal
 */
window.PranvyraImpact = {
  init() {
    this.bindReceiptModal();
    this.loadSummary();
    this.loadReceipts();
    this.loadAlternatives();

    // Listen for receipt events from BreathRoute & Life-Switch
    if (window.PranvyraState) {
      window.PranvyraState.subscribe('receipt:opened', (receipt) => {
        if (receipt) this.openReceiptModal(receipt);
      });
    }
  },

  bindReceiptModal() {
    const closeBtn = document.getElementById('closeReceiptModalBtn');
    const printBtn = document.getElementById('printReceiptBtn');
    const backdrop = document.getElementById('receiptModalBackdrop');

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        if (backdrop) backdrop.style.display = 'none';
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) backdrop.style.display = 'none';
      });
    }

    if (printBtn) {
      printBtn.addEventListener('click', () => {
        window.print();
      });
    }
  },

  openReceiptModal(receipt) {
    const backdrop = document.getElementById('receiptModalBackdrop');
    if (!backdrop || !receipt) return;

    document.getElementById('modalReceiptId').textContent = receipt.receipt_id || 'PRAN-RCPT-XXXXXXXX';
    document.getElementById('modalReceiptDate').textContent = receipt.issued_at || new Date().toISOString().split('T')[0];
    document.getElementById('modalReceiptDecision').textContent = receipt.decision_title || '--';
    document.getElementById('modalReceiptBefore').textContent = receipt.before_desc || '--';
    document.getElementById('modalReceiptAfter').textContent = receipt.after_desc || '--';
    document.getElementById('modalReceiptSavings').textContent = `${receipt.savings_kg || 0} kg CO₂e Avoided`;
    document.getElementById('modalReceiptWhy').textContent = receipt.why_it_matters || '--';
    document.getElementById('modalReceiptMethodology').textContent = receipt.methodology || 'UK DEFRA 2023 & US EPA Conversion Factors.';

    const disclaimer = document.getElementById('modalReceiptDisclaimer');
    if (disclaimer) {
      disclaimer.textContent = receipt.disclaimer || 'Estimated Avoided Emissions (Not a direct measurement of citywide air quality).';
    }

    backdrop.style.display = 'flex';

    if (window.lucide) window.lucide.createIcons();
  },

  async loadSummary() {
    try {
      const res = await window.PranvyraAPI.getImpactSummary();
      if (res.success && res.metrics) {
        const m = res.metrics;
        const co2El = document.getElementById('impactCo2Total');
        const carEl = document.getElementById('impactCarKmEquiv');
        const nrgEl = document.getElementById('impactEnergySaved');
        const rcpEl = document.getElementById('impactReceiptsCount');
        const ptsEl = document.getElementById('impactGreenPoints');

        if (co2El) co2El.innerHTML = `${m.co2_saved_kg} <span class="unit">kg</span>`;
        if (carEl) carEl.innerHTML = `${m.equiv_car_km} <span class="unit">km</span>`;
        if (nrgEl) nrgEl.innerHTML = `${m.energy_saved_kwh} <span class="unit">kWh</span>`;
        if (rcpEl) rcpEl.textContent = m.receipts_issued || 0;
        if (ptsEl) ptsEl.innerHTML = `${m.green_points} <span class="unit">pts</span>`;
      }
    } catch (e) {
      console.warn("Could not load impact summary:", e);
    }
  },

  async loadReceipts() {
    try {
      const res = await window.PranvyraAPI.getImpactReceipts();
      if (res.success && res.receipts) {
        const list = document.getElementById('receiptsLedgerList');
        if (!list) return;

        if (res.receipts.length === 0) {
          list.innerHTML = '<p class="text-muted" style="font-size: 0.88rem;">No receipts generated yet. Use BreathRoute or Life-Switch to log your first verified decision!</p>';
          return;
        }

        list.innerHTML = '';
        res.receipts.forEach(r => {
          const row = document.createElement('div');
          row.className = 'receipt-ledger-item';
          row.innerHTML = `
            <div class="rcpt-left">
              <span class="rcpt-id-badge">${this.escapeHtml(r.receipt_id)}</span>
              <div class="rcpt-title">${this.escapeHtml(r.decision_title)}</div>
              <div class="rcpt-date">${r.issued_at}</div>
            </div>
            <div class="rcpt-right">
              <span class="rcpt-savings text-emerald">${r.savings_kg} kg CO₂e</span>
              <button class="btn btn-outline btn-sm view-receipt-btn">View Receipt</button>
            </div>
          `;

          const viewBtn = row.querySelector('.view-receipt-btn');
          viewBtn.addEventListener('click', () => {
            this.openReceiptModal(r);
          });

          list.appendChild(row);
        });
      }
    } catch (e) {
      console.warn("Could not load receipts:", e);
    }
  },

  async loadAlternatives() {
    try {
      const res = await window.PranvyraAPI.getAlternatives();
      if (res.success && res.alternatives) {
        const grid = document.getElementById('alternativesCatalogGrid');
        if (!grid) return;

        grid.innerHTML = '';
        res.alternatives.forEach(alt => {
          const card = document.createElement('div');
          card.className = 'alt-card glass-card';
          card.innerHTML = `
            <div class="alt-category">${alt.category}</div>
            <div class="alt-switch-box">
              <div class="alt-current">Instead of: ${this.escapeHtml(alt.current_habit)}</div>
              <div class="alt-proposed">&rarr; ${this.escapeHtml(alt.suggested_alternative)}</div>
            </div>
            <p class="alt-reason">${this.escapeHtml(alt.why_better)}</p>
            <div class="alt-benefit"><i data-lucide="check-circle-2"></i> ${this.escapeHtml(alt.estimated_benefit)}</div>
            <div class="alt-footer">
              <span>Difficulty: <strong>${alt.difficulty}</strong></span>
              <button class="btn btn-outline btn-sm adopt-btn">Adopt Switch</button>
            </div>
          `;

          const btn = card.querySelector('.adopt-btn');
          btn.addEventListener('click', async () => {
            await window.PranvyraAPI.logImpactAction({
              action_type: 'sustainable_switch',
              title: `Adopted: ${alt.suggested_alternative}`,
              description: alt.estimated_benefit,
              co2_saved_kg: 0.8,
              points: 25
            });
            window.PranvyraState.addPoints(25);
            window.PranvyraAPI.showToast(`Adopted '${alt.suggested_alternative}'! +25 Green Points.`, 'success');
            this.loadSummary();
            this.loadReceipts();
          });

          grid.appendChild(card);
        });

        if (window.lucide) {
          window.lucide.createIcons();
        }
      }
    } catch (e) {
      console.warn("Could not load alternatives:", e);
    }
  },

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
};
