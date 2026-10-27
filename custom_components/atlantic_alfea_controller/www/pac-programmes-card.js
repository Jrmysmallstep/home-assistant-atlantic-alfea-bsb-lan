/**
 * Programmes PAC v0.2.0 — lecture seule des programmes horaires natifs BSB-LAN.
 * Les barres représentent les créneaux natifs ; aucun horaire n'est simulé.
 */
(() => {
  'use strict';
  const TAG = 'pac-programmes-card';
  if (customElements.get(TAG)) return;

  const PROGRAMS = [
    {key:'chauffage_c1',label:'Chauffage RDC',base:'501',color:'var(--warning-color,#e6a23c)'},
    {key:'chauffage_c2',label:'Chauffage étage',base:'521',color:'var(--info-color,#039be5)'},
    {key:'ecs',label:'Eau chaude sanitaire',base:'561',color:'var(--success-color,#43a047)'},
    {key:'rafraichissement_c1',label:'Rafraîchissement RDC',base:'11000',color:'#0891b2'},
    {key:'rafraichissement_c2',label:'Rafraîchissement étage',base:'11010',color:'#7c3aed'}
  ];
  const DAYS = [
    ['lundi','Lundi'],['mardi','Mardi'],['mercredi','Mercredi'],
    ['jeudi','Jeudi'],['vendredi','Vendredi'],['samedi','Samedi'],['dimanche','Dimanche']
  ];
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  })[c]);
  function toMinutes(value) {
    if (typeof value !== 'string' || !/^\d{2}:\d{2}$/.test(value)) return null;
    const [h,m] = value.split(':').map(Number);
    if (h > 24 || m > 59 || (h === 24 && m !== 0)) return null;
    return h*60+m;
  }

  class PacProgrammesCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({mode:'open'});
      this._config = {};
      this._selected = 'chauffage_c1';
      this._hass = null;
      this._refreshing = false;
    }
    setConfig(config) {
      this._config = config || {};
      if (!PROGRAMS.some(p => p.key === this._selected)) this._selected = 'chauffage_c1';
      this._render();
    }
    set hass(hass) {
      this._hass = hass;
      this._render();
    }
    getCardSize() { return 5; }

    _sensor(program) {
      const configured = this._config[program.key];
      if (configured) return this._hass?.states[configured] || null;
      return Object.values(this._hass?.states || {}).find(s =>
        s.entity_id.startsWith('sensor.') &&
        s.attributes?.parametre_lundi === program.base &&
        s.attributes?.source === 'BSB-LAN JSON /JQ'
      ) || null;
    }
    _button() {
      const configured = this._config.refresh_button;
      if (configured) return this._hass?.states[configured] || null;
      return Object.values(this._hass?.states || {}).find(s =>
        s.entity_id.startsWith('button.') &&
        (s.attributes?.friendly_name || '').includes('Programmes natifs - Actualiser')
      ) || null;
    }
    async _refresh() {
      const button = this._button();
      if (!button || button.state === 'unavailable' || this._refreshing) return;
      this._refreshing = true;
      this._render();
      try {
        await this._hass.callService('button','press',{entity_id:button.entity_id});
      } catch (err) {
        // Les capteurs conservent le détail des erreurs d'importation.
        this._lastError = String(err?.message || err);
      } finally {
        this._refreshing = false;
        this._render();
      }
    }
    _render() {
      if (!this.shadowRoot) return;
      const selected = PROGRAMS.find(p => p.key === this._selected) || PROGRAMS[0];
      const sensor = this._sensor(selected);
      const button = this._button();
      const days = sensor?.attributes?.jours || {};
      const status = sensor?.state || 'Capteur non trouvé';
      const today = (new Date().getDay() + 6) % 7;
      const updated = sensor?.attributes?.derniere_importation;
      const error = sensor?.attributes?.erreur_derniere_lecture;
      const rows = DAYS.map(([key,label],index) => {
        const ranges = Array.isArray(days[key]) ? days[key] : [];
        const bars = ranges.map(range => {
          const start = toMinutes(range.debut), end = toMinutes(range.fin);
          if (start === null || end === null || end <= start) return '';
          const left = Math.max(0,Math.min(100,start/1440*100));
          const width = Math.max(0,Math.min(100-left,(end-start)/1440*100));
          return `<span class="slot" style="left:${left}%;width:${width}%"></span>`;
        }).join('');
        const labels = ranges.length
          ? ranges.map(r => `<span class="range">${esc(r.debut)}–${esc(r.fin)}</span>`).join('')
          : (Array.isArray(days[key]) ? '<span class="empty">Aucune plage</span>' : '<span class="empty">Non chargé</span>');
        return `<div class="day ${index === today ? 'today' : ''}">
          <div class="day-name">${esc(label)}${index === today ? '<small>Aujourd’hui</small>' : ''}</div>
          <div class="day-detail">
            <div class="timeline">${bars}</div>
            <div class="ranges">${labels}</div>
          </div>
        </div>`;
      }).join('');
      const tabs = PROGRAMS.map(p => {
        const s = this._sensor(p);
        return `<button class="tab ${p.key === selected.key ? 'selected' : ''}" data-tab="${p.key}"
          type="button" aria-pressed="${p.key === selected.key}">${esc(p.label)}${s?.state === 'Erreur' ? ' ⚠' : ''}</button>`;
      }).join('');
      this.shadowRoot.innerHTML = `
        <style>
          :host{display:block;--program-color:${selected.color}}
          ha-card{padding:18px 18px 16px;color:var(--primary-text-color);background:var(--ha-card-background,var(--card-background-color))}
          .header{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
          h2{font-size:18px;font-weight:650;margin:0}
          .refresh{border:1px solid var(--divider-color);background:var(--secondary-background-color);
            color:var(--primary-text-color);padding:8px 12px;border-radius:10px;cursor:pointer}
          .refresh:disabled{opacity:.45;cursor:default}
          .tabs{display:flex;gap:7px;flex-wrap:wrap;margin:17px 0 14px}
          .tab{border:1px solid var(--divider-color);border-radius:11px;background:transparent;
            color:var(--primary-text-color);padding:10px 12px;cursor:pointer;font-size:13px}
          .tab.selected{border-color:var(--program-color);background:color-mix(in srgb,var(--program-color) 12%,transparent);font-weight:700}
          .meta{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--secondary-text-color);margin-bottom:13px}
          .state{font-weight:650;color:var(--primary-text-color)}
          .scale{display:grid;grid-template-columns:105px 1fr;gap:12px;align-items:center;margin:0 0 6px}
          .ticks{display:flex;justify-content:space-between;font-size:10px;color:var(--secondary-text-color)}
          .days{display:grid;gap:5px}
          .day{display:grid;grid-template-columns:105px minmax(0,1fr);gap:12px;align-items:center;
            border-radius:10px;padding:9px 8px}
          .day:nth-child(odd){background:var(--secondary-background-color)}
          .day.today{outline:1px solid var(--program-color)}
          .day-name{font-size:13px;font-weight:600}
          .day-name small{display:block;font-size:10px;color:var(--secondary-text-color);font-weight:400}
          .day-detail{min-width:0}
          .timeline{position:relative;height:14px;background:var(--divider-color);border-radius:6px;overflow:hidden}
          .slot{position:absolute;top:0;bottom:0;background:var(--program-color);border-radius:4px}
          .ranges{display:flex;flex-wrap:wrap;gap:5px 11px;margin-top:6px;font-size:11px;font-variant-numeric:tabular-nums}
          .range{white-space:nowrap}
          .empty{color:var(--secondary-text-color)}
          .warning{font-size:12px;color:var(--error-color);margin-top:10px;overflow-wrap:anywhere}
          .foot{font-size:11px;color:var(--secondary-text-color);margin-top:14px}
          @media(max-width:440px){
            ha-card{padding:14px 10px}
            .day,.scale{grid-template-columns:72px minmax(0,1fr);gap:6px}
            .day{padding:9px 5px}
            .day-name{font-size:12px}
            .tab{padding:9px 8px;font-size:12px}
          }
        </style>
        <ha-card>
          <div class="header"><h2>${esc(this._config.title || 'Programmes horaires PAC')}</h2>
            <button type="button" class="refresh" ${!button || button.state === 'unavailable' || this._refreshing ? 'disabled' : ''}>
              ${this._refreshing ? 'Actualisation…' : '↻ Actualiser'}
            </button>
          </div>
          <div class="tabs">${tabs}</div>
          <div class="meta"><span class="state">${esc(status)}</span>
            <span>${updated ? 'Dernière importation : '+esc(updated.replace('T',' ')) : 'Aucune importation'}</span>
          </div>
          <div class="scale"><span></span><div class="ticks"><span>00h</span><span>06h</span><span>12h</span><span>18h</span><span>24h</span></div></div>
          <div class="days">${rows}</div>
          ${error ? `<div class="warning">Dernière lecture : ${esc(error)}</div>` : ''}
          ${this._lastError ? `<div class="warning">Actualisation : ${esc(this._lastError)}</div>` : ''}
          <div class="foot">Horaires natifs de la PAC · consultation uniquement · aucune programmation Home Assistant</div>
        </ha-card>`;
      this.shadowRoot.querySelectorAll('[data-tab]').forEach(el =>
        el.addEventListener('click', () => {this._selected=el.dataset.tab;this._render();})
      );
      this.shadowRoot.querySelector('.refresh')?.addEventListener('click', () => this._refresh());
    }
  }
  customElements.define(TAG,PacProgrammesCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type:TAG,name:'PAC — Programmes horaires natifs',
    description:'Affichage hebdomadaire des programmes chauffage RDC, étage et ECS via BSB-LAN (lecture seule).'
  });
})();