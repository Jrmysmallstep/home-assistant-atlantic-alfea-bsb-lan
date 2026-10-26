/**
 * PAC Synoptique v2.9.3 (intégration V1.5.25 bêta 1) — Atlantic Alféa Extensa Duo / BSB-LAN
 * Home Assistant Lovelace custom card (sans dependance) • lecture seule
 * Inclus dans atlantic_alfea_controller 1.5.25
 * Aucun appel de service Home Assistant, aucune commande à la PAC.
 */
(() => {
'use strict';
const TAG = 'pac-synoptique-card';
const EDITOR_TAG = 'pac-synoptique-card-editor';

// Noms définis par le code de l'intégration et non par une capture Lovelace.
// Les entités de diagnostic peuvent être absentes ou désactivées dans HA.
const FIELDS = {
  globalMode:      ['select','Mode global'],
  pacState:        ['sensor','PAC - État'],
  outdoor:         ['sensor','PAC - T. extérieure'],
  compressor:      ['binary_sensor','COMP - État'],
  modulation:      ['sensor','COMP - Modulation'],
  defrost:         ['binary_sensor','PAC - Dégivrage DI6'],
  flow:            ['sensor','PAC - T. départ'],
  returnTemp:      ['sensor','PAC - T. retour'],
  targetFlow:      ['sensor','PAC - T. départ cible'],
  flowGap:         ['sensor','PAC - Écart départ / consigne'],
  energy:          ['sensor','PAC - Énergie totale'],
  circuit1:        ['climate','C1 - Circuit 1'],
  circuit2:        ['climate','C2 - Circuit 2'],
  circuit1State:   ['sensor','C1 - État actuel'],
  circuit2State:   ['sensor','C2 - État actuel'],
  pump1:           ['binary_sensor','C1 - Circulateur'],
  pump2:           ['binary_sensor','C2 - Circulateur'],
  program1:        ['sensor','C1 - Programme actif'],
  program2:        ['sensor','C2 - Programme actif'],
  regime1:         ['sensor','C1 - Régime temporaire'],
  regime2:         ['sensor','C2 - Régime temporaire'],
  override1:       ['binary_sensor','C1 - Dérogation'],
  override2:       ['binary_sensor','C2 - Dérogation'],
  heatState1:      ['sensor','C1 - Chauffage État'],
  heatState2:      ['sensor','C2 - Chauffage État'],
  coolState1:      ['sensor','C1 - Rafraîch. État'],
  coolState2:      ['sensor','C2 - Rafraîch. État'],
  heatFlowTarget1: ['sensor','C1 - Chauffage T. départ cible'],
  heatFlowTarget2: ['sensor','C2 - Chauffage T. départ cible'],
  heatComfort1:    ['sensor','C1 - Chauffage Cons. Conf'],
  heatEco1:        ['sensor','C1 - Chauffage Cons. Éco'],
  coolComfort1:    ['sensor','C1 - Rafraîch. Cons. Conf'],
  coolEco1:        ['sensor','C1 - Rafraîch. Cons. Éco'],
  heatComfort2:    ['sensor','C2 - Chauffage Cons. Conf'],
  heatEco2:        ['sensor','C2 - Chauffage Cons. Éco'],
  coolComfort2:    ['sensor','C2 - Rafraîch. Cons. Conf'],
  coolEco2:        ['sensor','C2 - Rafraîch. Cons. Éco'],
  ecsHeater:       ['water_heater','Eau chaude sanitaire'],
  ecsProduction:   ['sensor','ECS - Production'],
  ecsState:        ['sensor','ECS - État'],
  ecsTemp:         ['sensor','ECS - T. ballon'],
  ecsComfort:      ['sensor','ECS - T. Confort'],
  ecsEco:          ['sensor','ECS - T. Éco'],
  ecsPump:         ['binary_sensor','ECS - Pompe'],
  v3v:             ['sensor','V3V - Commande'],
  ecsElectric:     ['binary_sensor','ECS - Appoint électrique'],
  compressorHours: ['sensor','COMP - Heures de fonctionnement'],
  compressorStarts:['sensor','COMP - Nombre de démarrages'],
  minimumRun:      ['sensor','COMP - Temps de marche minimum'],
  minimumOff:      ['sensor','COMP - Temps d’arrêt minimum'],
  startsMaxRate:   ['sensor','COMP - Seuil de démarrages régulateur'],
  startsActualRate:['sensor','COMP - Démarrages régulateur'],
  cycleAverage:    ['sensor','COMP - Durée moyenne historique d’un cycle'],
  cycleLast:       ['sensor','COMP - Durée du dernier cycle'],
  stopLast:        ['sensor','COMP - Durée du dernier arrêt'],
  startsToday:     ['sensor','COMP - Démarrages aujourd’hui'],
  startsLastHour:  ['sensor','COMP - Démarrages sur la dernière heure'],
  shortCycles6h:   ['sensor','COMP - Cycles courts sur 6 heures'],
  clockTime:       ['sensor','Horloge PAC - Date et heure'],
  clockOffset:     ['sensor','Horloge PAC - Décalage'],
  alarmCycles:     ['binary_sensor','Alarme - COMP  Cycles courts répétés'],
  alarmRestart:    ['binary_sensor','Alarme - COMP  Redémarrages trop rapprochés'],
  alarmStarts:     ['binary_sensor','Alarme - COMP  Démarrages fréquents'],
  alarmGap:        ['binary_sensor','Alarme - PAC - Écart de température anormal'],
  alarmSummary:    ['binary_sensor','Alarme - COMP  Synthèse'],
  alarmClock:      ['binary_sensor','Alarme - Horloge PAC désynchronisée']
};
const ALERTS = [
  ['alarmCycles','Cycles courts répétés'],
  ['alarmRestart','Redémarrages trop rapprochés'],
  ['alarmStarts','Démarrages fréquents'],
  ['alarmGap','Écart départ / consigne anormal'],
  ['alarmClock','Horloge PAC désynchronisée']
];
// Attributs de contexte déjà fournis par les capteurs d'alarmes de l'intégration.
// Lecture seule et facultatifs : ne rien afficher si l'attribut est absent.
const ALERT_CONTEXT = {
  alarmCycles: [
    ['Dernier cycle', 'dernier_cycle_minutes', 'min'],
    ['Seuil cycle court', 'seuil_cycle_minutes', 'min'],
    ['Cycles courts sur 1 h', 'cycles_courts_derniere_heure', ''],
    ['Cycles courts sur 6 h', 'cycles_courts_6_heures', ''],
    ['Règle de déclenchement', 'regle_alerte', '']
  ],
  alarmRestart: [
    ['Dernier arrêt', 'dernier_arret_minutes', 'min'],
    ['Arrêt minimum', 'temps_arret_minimum_minutes', 'min'],
    ['Redémarrages rapprochés sur 1 h', 'redemarrages_rapproches_derniere_heure', ''],
    ['Règle de déclenchement', 'regle_alerte', '']
  ],
  alarmStarts: [
    ['Démarrages dernière heure', 'demarrages_derniere_heure', ''],
    ['Seuil par heure', 'seuil_par_heure', '']
  ],
  alarmGap: [
    ['Écart mesuré', 'ecart_actuel_degC', '°C'],
    ['Seuil écart', 'seuil_ecart_degC', '°C'],
    ['Temporisation', 'temporisation_minutes', 'min']
  ],
  alarmClock: [
    ['Décalage', 'decalage_secondes', 's'],
    ['Seuil', 'seuil_secondes', 's']
  ],
  alarmSummary: [
    ['Supervision complète', 'supervision_complete', '']
  ]
};
// Mapping natif validé sur RVS21.831F : 10112/10122, 1 = Réduit (Éco), 2 = Confort.
// Le programme ne prouve pas qu'un circuit est en chauffe. Ne pas confondre avec hvac_action.
const programmedRegime = raw => {
  if (isMissing(raw)) return null;
  const n=norm(raw);
  const m=/^([0-9]+)(?:\s|$)/.exec(String(raw).trim());
  if (m?.[1]==='1') return 'Éco';
  if (m?.[1]==='2') return 'Confort';
  if (n.includes('allure confort')) return 'Confort';
  if (n.includes('allure reduit') || n.includes('allure eco')) return 'Éco';
  return null;
};
const norm = value => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
  .toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const html = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const isMissing = value => value === undefined || value === null || ['','unknown','unavailable','none','null'].includes(String(value).trim().toLowerCase());
const decimal = new Intl.NumberFormat('fr-FR',{minimumFractionDigits:1,maximumFractionDigits:1});
const integer = new Intl.NumberFormat('fr-FR',{maximumFractionDigits:0});
const nvalue = value => {
  if (isMissing(value)) return null;
  const result = Number(String(value).replace(',','.'));
  return Number.isFinite(result) ? result : null;
};
const temp = value => {const n=nvalue(value);return n===null?'—':`${decimal.format(n)} °C`;};
const formatted = (value,unit='',decimals=1) => {
  const n=nvalue(value);
  if (n===null) return '—';
  return `${decimals===0?integer.format(n):decimal.format(n)}${unit?' '+unit:''}`;
};
const bool = state => !state || isMissing(state.state) ? null : state.state==='on'?true:state.state==='off'?false:null;
const clean = (value,max=80) => {
  if(isMissing(value)) return '—';
  const text=String(value);
  return text.length>max?text.slice(0,max-1)+'…':text;
};
const entry = (caption,value) => `<div class="datum"><span>${html(caption)}</span><strong>${html(value)}</strong></div>`;
const chip = (text,tone='dim') => `<span class="chip ${tone}">${html(text)}</span>`;
const icon = (name) => {
  const icons = {
    fan:'<circle cx="24" cy="24" r="19"/><circle cx="24" cy="24" r="5"/><path d="M24 19c-3-6-7-13-1-15 8-3 13 8 6 17 M29 24c7-1 15 0 14 6-1 9-13 10-17 0 M22 29c-3 7-9 13-14 8-7-7 1-16 11-15"/>',
    therm:'<path d="M28 28V9a5 5 0 0 0-10 0v19a10 10 0 1 0 10 0Z"/><path d="M23 16v21"/>',
    radiant:'<rect x="8" y="22" width="32" height="15" rx="4"/><path d="M12 27h24M12 32h24M15 17c-3-4 3-5 0-9M24 17c-3-4 3-5 0-9M33 17c-3-4 3-5 0-9"/>',
    water:'<path d="M24 4C16 15 10 22 10 29a14 14 0 0 0 28 0C38 22 32 14 24 4Z"/><path d="M17 32c1 4 4 6 8 6"/>',
    snow:'<path d="M24 4v40M4 24h40M10 10l28 28M38 10 10 38M18 10l6 6 6-6M18 38l6-6 6 6M10 18l6 6-6 6M38 18l-6 6 6 6"/>',
    heat:'<path d="M24 4v6M24 38v6M4 24h6M38 24h6M10 10l5 5M33 33l5 5M38 10l-5 5M15 33l-5 5"/><circle cx="24" cy="24" r="10"/>',
    alert:'<path d="M24 5 3 42h42L24 5Z"/><path d="M24 17v12M24 35v1"/>',
    bolt:'<path d="m28 4-16 23h12l-4 17 17-24H25l3-16Z"/>',
    pause:'<rect x="11" y="10" width="9" height="28" rx="2"/><rect x="28" y="10" width="9" height="28" rx="2"/>',
    clock:'<circle cx="24" cy="24" r="19"/><path d="M24 12v13l8 5"/>'
  };
  return `<svg class="symbol" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.therm}</svg>`;
};

class PacSynoptiqueCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:'open'});
    this._ids=null;
    this._lastSignature='';
    this._lastDiscovery=0;
    this._resolvedThemeMode=null;
    this._lastThemeName=null;
    this._programTab='chauffage_c1';
  }
  static getStubConfig() {return {theme_mode:'auto',layout_orientation:'auto',show_diagnostics:true};}
  static getConfigElement() {return document.createElement(EDITOR_TAG);}
  setConfig(config) {
    if(!config || typeof config!=='object') throw new Error('Configuration de la carte absente');
    if(config.entities && (typeof config.entities!=='object' || Array.isArray(config.entities))) throw new Error('entities doit être un objet de correspondance');
    if(config.show_links != null && typeof config.show_links !== 'boolean') throw new Error('show_links doit être un booléen');
    if(config.animate_flows != null && typeof config.animate_flows !== 'boolean') throw new Error('animate_flows doit être un booléen');
    if(config.show_pump_badges != null && typeof config.show_pump_badges !== 'boolean') throw new Error('show_pump_badges doit être un booléen');
    if(config.layout_style != null && !['classic','clean','aerien'].includes(config.layout_style)) {
      throw new Error('layout_style doit être classic, clean ou aerien');
    }
    if(config.layout_orientation != null && !['auto','landscape','portrait'].includes(config.layout_orientation)) {
      throw new Error('layout_orientation doit être auto, landscape ou portrait');
    }
    if(config.theme_mode != null && !['auto','light','dark'].includes(config.theme_mode)) {
      throw new Error('theme_mode doit être auto, light ou dark');
    }
    this._config={title:'Atlantic Alféa Extensa Duo',show_diagnostics:true,theme_mode:'auto',layout_orientation:'auto',layout_style:'classic',...config};
    this._ids=null;
    this._lastSignature='';
    if(this._hass) this.hass=this._hass;
  }
  getCardSize(){return this._config?.show_diagnostics?9:7;}
  getGridOptions(){return {columns:"full",rows:"auto"};}
  set hass(hass) {
    this._hass=hass;
    if(!this._config) return;
    // La palette suit automatiquement le thème HA, même sans changement des capteurs.
    const selected = this._config.theme_mode || 'auto';
    const actual = typeof hass.themes?.darkMode === 'boolean'
      ? (hass.themes.darkMode ? 'dark' : 'light')
      : (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const rendered = selected === 'auto' ? actual : selected;
    const changed = this._resolvedThemeMode !== rendered || this._lastThemeName !== hass.themes?.theme;
    this._resolvedThemeMode = rendered;
    this._lastThemeName = hass.themes?.theme;
    this.dataset.pacTheme = selected === 'auto' ? 'auto' : selected;
    this.dataset.pacScheme = rendered;
    this.dataset.layoutStyle = ['classic','clean','aerien'].includes(this._config.layout_style) ? this._config.layout_style : 'classic';
    this.dataset.orientation = this._config.layout_orientation || 'auto';
    this.dataset.showLinks = this._config.show_links === false ? 'false' : 'true';
    this.dataset.animateFlows = this._config.animate_flows === false ? 'false' : 'true';
    // Recensement des entités au démarrage et toutes les 30 s pour prendre en compte les capteurs activés.
    if(!this._ids || Date.now()-this._lastDiscovery>30000) {
      this._ids=this._discover();this._lastDiscovery=Date.now();
    }
    const signature=JSON.stringify(Object.entries(this._ids).map(([key,id])=> {
      const st=id?hass.states[id]:null;
      return [key,id,st?.state,st?.attributes?.hvac_action,st?.attributes?.current_temperature,
        st?.attributes?.temperature,st?.attributes?.production,st?.attributes?.regime_consigne,
        st?.attributes?.phase_apprentissage,st?.attributes?.pompe_ecs,st?.attributes?.appoint_electrique];
    }));
    // Les programmes natifs sont des capteurs à la demande : inclure leur
    // état et leur horodatage dans la signature pour rafraîchir le synoptique.
    const programSignature=JSON.stringify(Object.values(hass.states).filter(st=>
      st.entity_id.startsWith('sensor.') &&
      st.attributes?.source==='BSB-LAN JSON /JQ' &&
      ['501','521','561'].includes(String(st.attributes?.parametre_lundi))
    ).map(st=>[st.entity_id,st.state,st.attributes?.derniere_importation,st.attributes?.erreur_derniere_lecture]));
    const fullSignature=signature+'|'+programSignature;
    if(changed||fullSignature!==this._lastSignature){this._lastSignature=fullSignature;this._render();}
  }
  _discover(){
    const states=this._hass?.states||{};
    const items=Object.entries(states).map(([id,st])=>({
      id, domain:id.split('.')[0], friendly:norm(st.attributes?.friendly_name), tail:norm(id.split('.')[1]||''),
      fromAlfea:/atlantic|alfea|bsb/.test(norm(id+' '+(st.attributes?.friendly_name||'')))
    }));
    const found={};
    for(const [key,[domain,label]] of Object.entries(FIELDS)){
      const override=this._config?.entities?.[key];
      if(typeof override==='string' && override.trim()) {found[key]=override.trim();continue;}
      const target=norm(label);
      let max=0, winner=null;
      for(const it of items){
        if(it.domain!==domain) continue;
        let score=0;
        if(it.friendly===target) score=110;
        else if(it.friendly.endsWith(' '+target)) score=100;
        else if(it.tail===target) score=85;
        else if(it.tail.endsWith(' '+target)) score=75;
        if(score && it.fromAlfea) score+=5;
        if(score>max){max=score;winner=it.id;}
      }
      found[key]=winner;
    }
    return found;
  }
  _s(key){return this._ids?.[key] ? this._hass?.states[this._ids[key]] : null;}
  _v(key){const st=this._s(key);return st&&!isMissing(st.state)?st.state:null;}
  _a(key,attr){const st=this._s(key);return st ? st.attributes?.[attr] : null;}
  _b(key){return bool(this._s(key));}
  _resolveMode(){
    const raw=norm(this._v('globalMode'));
    const c1=this._v('circuit1');
    const c2=this._v('circuit2');
    if(raw.includes('refroid')) return 'cool';
    if(raw.includes('chauff')) return 'heat';
    if(raw==='off'||raw==='arret') return 'off';
    if(c1==='cool'||c2==='cool') return 'cool';
    if(c1==='heat'||c2==='heat') return 'heat';
    if(c1==='off'&&c2==='off') return 'off';
    return 'unknown';
  }
  _nativePreset(st, off){
    if(off) return {label:'OFF',tone:'dim'};
    const raw=st?.attributes?.preset_mode;
    if(isMissing(raw)) return {label:'Régime indisponible',tone:'dim'};
    const value=norm(String(raw));
    if(value==='auto') return {label:'AUTO',tone:'positive'};
    if(value==='eco' || value==='reduit') return {label:'ECO forcé',tone:'warning'};
    if(value==='confort' || value==='comfort') return {label:'Confort forcé',tone:'warning'};
    return {label:'Régime indisponible',tone:'dim'};
  }
  _circuit(i){
    const key=`circuit${i}`;
    const st=this._s(key);
    const mode=this._v(key);
    const action=st?.attributes?.hvac_action;
    const isHeating=action==='heating';
    const isCooling=action==='cooling';
    const active=isHeating||isCooling;
    const off=mode==='off'||action==='off';
    const actionText=isHeating?'Chauffe actuellement':isCooling?'Rafraîchit actuellement':off?'Arrêt':
      (isMissing(mode)?'État indisponible':'En attente');
    return {
      number:i, key, mode, action, active, off, isHeating, isCooling, actionText,
      nativePreset:this._nativePreset(st,off),
      current:st?.attributes?.current_temperature,target:st?.attributes?.temperature,
      regime:st?.attributes?.regime_consigne, native:this._v(`circuit${i}State`),
      program:this._v(`program${i}`), pump:this._b(`pump${i}`),
      override:this._b(`override${i}`),
      targetFlow:this._v(`heatFlowTarget${i}`)
    };
  }
  _ecs(){
    const production=this._v('ecsProduction')||this._a('ecsHeater','production');
    const p=norm(production);
    const pump=this._b('ecsPump')??(typeof this._a('ecsHeater','pompe_ecs')==='boolean'?this._a('ecsHeater','pompe_ecs'):null);
    const electric=this._b('ecsElectric')??(typeof this._a('ecsHeater','appoint_electrique')==='boolean'?this._a('ecsHeater','appoint_electrique'):null);
    const viaPac=(p.includes('chauffe par pac')||p.includes('pac appoint electrique')) && pump!==false && this._b('compressor')!==false;
    const withElectric=electric===true||p==='appoint electrique'||p.includes('pac appoint electrique');
    const tempBallon=this._v('ecsTemp') ?? this._a('ecsHeater','current_temperature');
    const target=this._a('ecsHeater','temperature');
    return {production:clean(production||this._v('ecsState')||'Indisponible',56),
      viaPac,withElectric,pump,electric,tempBallon,target};
  }
  _pipe(tone='idle',vertical=false){
    return `<div class="pipe ${vertical?'vertical':''} ${tone}"><span class="pipe-light"></span></div>`;
  }
  _label(key){return FIELDS[key]?.[1] || key;}
  _detailRow(label,key,unit='',decimals=1){
    const st=this._s(key);
    const raw=this._v(key);
    const value=(['compressorStarts','startsToday','startsLastHour','shortCycles6h','cycleAverage','cycleLast','stopLast','minimumRun','minimumOff','startsActualRate','startsMaxRate','compressorHours'].includes(key) && nvalue(raw)!==null) ? formatted(raw,unit,0) : unit ? formatted(raw,unit,decimals) : (key.startsWith('alarm') || ['compressor','defrost','ecsPump','ecsElectric','override1','override2','pump1','pump2'].includes(key)) ? (raw==='on'?(['pump1','pump2'].includes(key)?'En marche':'Actif'):raw==='off'?(['pump1','pump2'].includes(key)?'Arrêté':'Inactif'):clean(raw)) : clean(raw);
    return `<div class="detail-row"><span>${html(label)}</span><strong class="${!st||raw==null?'na':''}">${html(value)}</strong></div>`;
  }
  _diagGroup(title,body){return `<section class="diag-group"><h4>${html(title)}</h4>${body}</section>`;}
  _nativeWeeklyPrograms(){
    const programs=[
      {key:'chauffage_c1',base:'501',label:'RDC',title:'Chauffage RDC'},
      {key:'chauffage_c2',base:'521',label:'Étage',title:'Chauffage étage'},
      {key:'ecs',base:'561',label:'ECS',title:'Eau chaude sanitaire'}
    ];
    const selected=programs.find(p=>p.key===this._programTab)||programs[0];
    const source=Object.values(this._hass?.states||{}).find(st=>
      st.entity_id.startsWith('sensor.') &&
      st.attributes?.source==='BSB-LAN JSON /JQ' &&
      String(st.attributes?.parametre_lundi)===selected.base
    );
    const days=source?.attributes?.jours||{};
    const weekdays=[
      ['lundi','Lun'],['mardi','Mar'],['mercredi','Mer'],['jeudi','Jeu'],
      ['vendredi','Ven'],['samedi','Sam'],['dimanche','Dim']
    ];
    const time=value=>{
      if(typeof value!=='string'||!/^\d{2}:\d{2}$/.test(value))return null;
      const [h,m]=value.split(':').map(Number);
      return h<=24&&m<60&&(h<24||m===0)?h*60+m:null;
    };
    const tabs=programs.map(p=>`<button type="button" class="weekly-tab ${p.key===selected.key?'active':''}"
      data-program-tab="${p.key}" aria-pressed="${p.key===selected.key}">${html(p.label)}</button>`).join('');
    const rows=weekdays.map(([day,label])=>{
      const ranges=Array.isArray(days[day])?days[day]:null;
      const bars=(ranges||[]).map(range=>{
        const start=time(range.debut),end=time(range.fin);
        if(start===null||end===null||end<=start)return '';
        return `<i class="weekly-slot" style="left:${(start/1440*100).toFixed(3)}%;width:${((end-start)/1440*100).toFixed(3)}%"></i>`;
      }).join('');
      const labelText=ranges===null?'Non chargé':ranges.length===0?'Aucune plage':
        ranges.map(r=>`${html(r.debut)}–${html(r.fin)}`).join(' · ');
      return `<div class="weekly-row"><span class="weekly-day">${label}</span>
        <div class="weekly-day-body"><div class="weekly-track">${bars}</div>
          <div class="weekly-times">${labelText}</div></div></div>`;
    }).join('');
    const status=source?.state||'Capteur non disponible';
    const date=source?.attributes?.derniere_importation;
    const error=source?.attributes?.erreur_derniere_lecture;
    return this._diagGroup('Programmes horaires natifs · Lecture seule',
      `<div class="weekly-tabs">${tabs}</div>
      <div class="weekly-info">${html(selected.title)} · ${html(status)}
        ${date?`<span> · Importé le ${html(date.replace('T',' '))}</span>`:''}</div>
      <div class="weekly-scale"><span></span><div><span>0h</span><span>6h</span><span>12h</span><span>18h</span><span>24h</span></div></div>
      <div class="weekly-rows">${rows}</div>
      ${error?`<p class="weekly-error">Dernière lecture : ${html(error)}</p>`:''}
      <p class="weekly-note">Horaires lus sur la PAC · actualisation via le bouton « Programmes natifs - Actualiser ».</p>`);
  }
  _render(){
    // États de déploiement persistants malgré le rafraîchissement des entités HA.
    const prevAlarms=this.shadowRoot.querySelector('details[data-panel="alarms"]')?.open ?? false;
    const prevDetails=this.shadowRoot.querySelector('details[data-panel="diagnostics"]')?.open ?? false;
    const mode=this._resolveMode();
    const compressor=this._b('compressor');
    const c1=this._circuit(1),c2=this._circuit(2),ecs=this._ecs();
    // Q3 sélectionne ECS ou le collecteur chauffage, jamais directement C1/C2.
    const v3vRaw=this._v('v3v');
    const v3v=v3vRaw==='ECS'?'ecs':v3vRaw==='Chauffage'?'heat':null;
    const v3vTone=v3v==='ecs'?'heat':v3v==='heat'?(mode==='cool'?'cool':'positive'):'dim';
    const v3vLabel=v3v==='ecs'?'V3V A · ECS':v3v==='heat'?'V3V B · Chauffage':'V3V indisponible';
    const c1Flow=c1.active && v3v!=='ecs';
    const c2Flow=c2.active && v3v!=='ecs';
    const ecsViaPac=ecs.viaPac && v3v!=='heat';
    const defrost=this._b('defrost');
    // Les animations illustrent une activité confirmée, pas la vitesse réelle du ventilateur.
    const exchangerRunning=compressor===true && (mode==='heat'||mode==='cool');
    const fanAnimated=compressor===true && defrost!==true;
    const modeText=mode==='heat'?'Mode chauffage':mode==='cool'?'Mode rafraîchissement':mode==='off'?'Mode arrêt':'Mode inconnu';
    const compressorText=compressor===true?'En marche':compressor===false?'À l’arrêt':'État inconnu';
    const compressionTone=compressor===true?'active':compressor===false?'idle':'unknown';
    const branchTone=x=>x.isHeating?'heat':x.isCooling?'cool':'idle';
    const alertActive=ALERTS.filter(([key])=>this._b(key)===true);
    const summary=this._b('alarmSummary');
    const summaryLearning=this._a('alarmSummary','phase_apprentissage')===true;
    if(alertActive.length===0 && summary===true) alertActive.push(['alarmSummary','Alerte compresseur (synthèse)']);
    const alertCoverage=ALERTS.filter(([key])=>this._b(key)!==null).length;
    const alertUnknown=ALERTS.length-alertCoverage;
    const alertDescription=alertActive.length ?
      `<div class="alert-stack">${alertActive.map(([key,name])=>{
        const context=(ALERT_CONTEXT[key]||[]).flatMap(([caption,attribute,unit])=>{
          const val=this._a(key,attribute);
          if(isMissing(val)) return [];
          const rendered=typeof val==='boolean'?(val?'Oui':'Non'):
            typeof val==='number'?`${decimal.format(val)}${unit?' '+unit:''}`:String(val);
          return [`<div class="alarm-fact"><span>${html(caption)}</span><strong>${html(rendered)}</strong></div>`];
        });
        return `<div class="alert-item"><div class="alert-line"><span class="alert-mark">!</span><span>${html(name)}</span></div>
          ${context.length?`<div class="alarm-context">${context.join('')}</div>`:''}</div>`;
      }).join('')}</div>` :
      `<div class="alert-clear">${icon('heat')}<div><strong>${alertCoverage || summary!==null ?'Aucune alarme active remontée':'Surveillance indisponible'}</strong><span>${alertCoverage || summary!==null ?'Aucun défaut signalé par les capteurs disponibles':'Aucun capteur d’alarme identifié'}</span></div></div>`;
    const alertsMeta=[
      `${alertCoverage}/${ALERTS.length} alertes individuelles disponibles`,
      summaryLearning?'Supervision compresseur en apprentissage':null,
      alertUnknown?'Alertes non disponibles : état non vérifié':null
    ].filter(Boolean).join(' · ');
    const statesCount=Object.values(this._ids||{}).filter(id=>!!id && !!this._hass?.states[id]).length;
    const activeCount=(c1.active?1:0)+(c2.active?1:0)+(ecs.viaPac?1:0);
    const ecsText=ecsViaPac ? 'Chauffe par PAC' : ecs.withElectric?'Appoint électrique' :
      norm(ecs.production).includes('demande')?'Demande en attente':
      norm(ecs.production)==='inactive'?'En attente':'État non confirmé';
    const ecsTone=ecsViaPac?'heat':ecs.withElectric?'electric':'idle';
    const gauge=nvalue(this._v('modulation'));
    const air=temp(this._v('outdoor'));
    const pacDelta= nvalue(this._v('flow'))!==null && nvalue(this._v('returnTemp'))!==null ?
      `${decimal.format(nvalue(this._v('flow'))-nvalue(this._v('returnTemp')))} °C` : '—';
    // Les pastilles affichent exclusivement l'état BSB natif remonté par l'entité.
    // Les programmes horaires et attributs interprétés restent dans les diagnostics.
    const circHtml=c => `<section class="output-card ${branchTone(c)} regime-${c.mode==='heat'?'heat':c.mode==='cool'?'cool':'idle'}" aria-label="Circuit ${c.number} ${c.number===1?'RDC':'étage'}">
      <div class="out-top"><div class="out-ico">${icon(c.isCooling || (c.mode==='cool' && !c.isHeating)?'snow':'radiant')}</div>
        <div class="out-head"><div class="out-title">Circuit ${c.number} <span>· ${c.number===1?'RDC':'Étage'}</span></div>
          <div class="out-status">${html(c.actionText)}</div></div>
        <span class="state-dot ${branchTone(c)}"></span></div>
      <div class="out-values"><div><span>Température ambiante</span><strong>${html(temp(c.current))}</strong></div>
        <div><span>Consigne effective</span><strong>${html(temp(c.target))}</strong></div></div>
      <div class="out-foot">${chip(c.nativePreset?.label ?? (c.off?'OFF':'Régime indisponible'),c.nativePreset?.tone ?? 'dim')}
        ${chip(c.native??'État BSB-LAN indisponible','dim')}
        ${this._config.show_pump_badges!==false && c.pump!==null?chip(c.pump?'Circulateur actif':'Circulateur arrêté',c.pump?'positive':'dim'):''}
        ${c.override===true?chip('Dérogation active','warning'):''}</div>
    </section>`;
    const alarmsClass=alertActive.length?'alerted':'quiet';
    const diagComp=this._diagGroup('Compresseur / fonctionnement',[
      ['État','compressor',''],['Modulation','modulation','%'],['Heures de fonctionnement','compressorHours','h'],
      ['Nombre de démarrages','compressorStarts',''],['Démarrages aujourd’hui','startsToday',''],
      ['Démarrages sur la dernière heure','startsLastHour',''],['Durée moyenne historique d’un cycle','cycleAverage','min'],
      ['Durée du dernier cycle','cycleLast','min'],['Durée du dernier arrêt','stopLast','min'],
      ['Cycles courts sur 6 heures','shortCycles6h',''],['Temps de marche minimum régulateur','minimumRun','min'],
      ['Temps d’arrêt minimum régulateur','minimumOff','min'],
      ['Démarrages régulateur','startsActualRate','dém./h'],['Seuil démarrages régulateur','startsMaxRate','dém./h']
    ].map(([name,key,unit])=>this._detailRow(name,key,unit,0)).join(''));
    const diagPac=this._diagGroup('PAC / circuit hydraulique commun',[
      ['État général','pacState',''],['Température extérieure','outdoor','°C'],
      ['Énergie électrique totale cumulée','energy','kWh'],['Dégivrage DI6','defrost',''],
      ['Horloge PAC','clockTime','']
    ].map(([name,key,unit])=>this._detailRow(name,key,unit,unit==='kWh'?0:1)).join(''));
    const diagCircs=this._diagGroup('Circuits 1 & 2 / programmation',[
      ...[1,2].flatMap(i=>[
        [`C${i} — État actuel`,`circuit${i}State`,''],[`C${i} — Circulateur`,`pump${i}`,''],[`C${i} — Programme actif`,`program${i}`,''],
        [`C${i} — Régime temporaire`,`regime${i}`,''],[`C${i} — Dérogation`,`override${i}`,''],
        [`C${i} — État chauffage`,`heatState${i}`,''],[`C${i} — État rafraîchissement`,`coolState${i}`,''],
        [`C${i} — Départ cible chauffage (non mesuré)`,`heatFlowTarget${i}`,'°C'],
        [`C${i} — Chauffage Confort`,`heatComfort${i}`,'°C'],[`C${i} — Chauffage Éco`,`heatEco${i}`,'°C'],
        [`C${i} — Rafraîchissement Confort`,`coolComfort${i}`,'°C'],[`C${i} — Rafraîchissement Éco`,`coolEco${i}`,'°C']
      ])
    ].map(([name,key,unit])=>this._detailRow(name,key,unit)).join(''));
    const diagWeekly=this._nativeWeeklyPrograms();
    this.shadowRoot.innerHTML=`<style>
      /* En auto, les palettes proviennent des variables du thème Home Assistant. */
      :host {display:block;
        --bg:var(--ha-card-background, var(--card-background-color, #fff));
        --text:var(--primary-text-color, #212c38);--sub:var(--secondary-text-color,#63768b);
        --line:var(--divider-color,#bac9d4);
        --surface:color-mix(in srgb,var(--bg) 91%,var(--text) 9%);
        --surface2:color-mix(in srgb,var(--bg) 95%,var(--text) 5%);
        --panel-line:color-mix(in srgb,var(--line) 75%,var(--text) 25%);
        --soft:color-mix(in srgb,var(--bg) 86%,var(--text) 14%);
        --soft2:color-mix(in srgb,var(--bg) 80%,var(--text) 20%);
        --chip-bg:color-mix(in srgb,var(--bg) 82%,var(--text) 18%);
        --chip-fg:var(--text);--blue:#087db8;--red:#d86542;--green:#07886c;--amber:#ae650d;
        --chip-heat-bg:#fff1e9;--chip-heat-fg:#aa4b1e;--chip-heat-line:#d6a187;
        --chip-cool-bg:#e5f3fb;--chip-cool-fg:#12648b;--chip-cool-line:#7db4d1;
        --chip-warn-bg:#fff3df;--chip-warn-fg:#925e15;--chip-warn-line:#ddb477;
        --chip-good-bg:#e3f5ef;--chip-good-fg:#11684f;--chip-good-line:#81b9a8;
        --warn-panel:#fff2e8;--warn-text:#99431e;--warn-line:#d99872;
        --clear-text:#0b7a5e;--muted:#8ca0b3;
        --fan-bg:#dae6ee;--fan-edge:#91aab9;--fan-inset:#dae6ee;--fan-stroke:#769ab3;
        --pipe:#9eb0be;--icon:#437495;--tank-shadow:#64758a;--summary-chevron:#477e9c}
      :host([data-pac-scheme="dark"]){color-scheme:dark}
      :host([data-pac-scheme="light"]){color-scheme:light}
      /* Option dark : palette d'origine, sans altérer la disposition graphique. */
      :host([data-pac-theme="dark"]){color-scheme:dark;
        --bg:#121b26;--surface:#1a2837;--surface2:#172331;--line:#314355;
        --text:#ecf2f8;--sub:#9fb3c6;--panel-line:#31495d;--soft:#243646;
        --soft2:#314256;--chip-bg:#27384a;--chip-fg:#bfd0dc;
        --blue:#56beff;--red:#ff9c70;--green:#57d7ae;--amber:#ffc16b;
        --chip-heat-bg:#3a2a29;--chip-heat-fg:#ffb692;--chip-heat-line:#9b5940;
        --chip-cool-bg:#1d374b;--chip-cool-fg:#8bd7ff;--chip-cool-line:#2d7296;
        --chip-warn-bg:#3b3023;--chip-warn-fg:#ffd2a3;--chip-warn-line:#94703e;
        --chip-good-bg:#1e3835;--chip-good-fg:#a6efdb;--chip-good-line:#366f62;
        --warn-panel:#382924;--warn-text:#ffd8b8;--warn-line:#bd794f;--clear-text:#a1e4cf;
        --muted:#71899b;--fan-bg:#243646;--fan-edge:#6d8699;
        --fan-inset:#243646;--fan-stroke:#79b8d6;--pipe:#3b4d5c;
        --icon:#a2c4dc;--tank-shadow:#192737;--summary-chevron:#8bb8d0}
      /* Option light : palette claire, même si l'interface HA est sombre. */
      :host([data-pac-theme="light"]){color-scheme:light;
        --bg:#fff;--text:#213448;--sub:#627588;--line:#cfdae4;--surface:#f3f7fa;
        --surface2:#f9fbfd;--panel-line:#bdd0de;--soft:#e2ecf3;--soft2:#d2e2ed;
        --chip-bg:#e7eef5;--chip-fg:#365168}
      ha-card {display:block;container-type:inline-size;overflow:hidden;background:var(--bg);border:1px solid var(--line);border-radius:var(--ha-card-border-radius,22px);
        color:var(--text);font-family:var(--primary-font-family,Roboto,Arial,sans-serif)}
      *{box-sizing:border-box} .wrap{padding:22px 22px 18px}
      .header{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;padding-bottom:17px;
        border-bottom:1px solid var(--line)}
      .eyebrow{font-size:10px;letter-spacing:2px;color:#77a9c9;font-weight:800;text-transform:uppercase}
      h2{margin:6px 0 2px;font-size:clamp(19px,2vw,27px);font-weight:730;letter-spacing:-.35px}
      .sub{color:var(--sub);font-size:12px;line-height:1.5}
      .header-right{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:8px;max-width:380px}
      .chip{display:inline-flex;align-items:center;gap:5px;border-radius:99px;background:var(--chip-bg);
        color:var(--chip-fg);border:1px solid var(--panel-line);padding:4px 9px;font-size:11px;font-weight:600;line-height:1.3}
      .chip.heat{color:var(--chip-heat-fg);border-color:var(--chip-heat-line);background:var(--chip-heat-bg)}
      .chip.cool{color:var(--chip-cool-fg);border-color:var(--chip-cool-line);background:var(--chip-cool-bg)}
      .chip.warning{color:var(--chip-warn-fg);border-color:var(--chip-warn-line);background:var(--chip-warn-bg)}
      .chip.positive{color:var(--chip-good-fg);border-color:var(--chip-good-line);background:var(--chip-good-bg)}
      /* V2.3.1 : identité graphique d'origine inchangée. Distribution géométrique calculée
         depuis la grille V2.3.0 (0.80fr / 52px / 1fr / 84px / 1.88fr) :
         le module PAC perd 44px, récupérés par le raccordement droit (84 -> 128px).
         La largeur du bloc COMP et celle des trois sorties restent inchangées. */
      .schematic{display:grid;grid-template-columns:
          minmax(175px,calc(21.7391304% - 29.565px))
          52px
          minmax(220px,calc(27.1739130% - 80.957px))
          128px
          minmax(350px,calc(51.0869565% - 69.478px));
        grid-template-rows:repeat(3,minmax(130px,auto));gap:12px 0;align-items:stretch;margin:4px 0 20px;min-width:0}
      .machine{grid-column:1;grid-row:1/4;align-self:stretch}
      .inlink{grid-column:2;grid-row:1/4;align-self:stretch}
      .pac{grid-column:3;grid-row:1/4;align-self:stretch}
      .outlink{grid-column:4;grid-row:1/4;align-self:stretch}
      .outs{grid-column:5;grid-row:1/4;display:grid;grid-template-rows:repeat(3,minmax(130px,auto));gap:12px}
      .machine,.pac,.output-card{background:linear-gradient(165deg,var(--surface),var(--surface2));border-radius:17px;border:1px solid var(--panel-line)}
      .machine,.pac{padding:18px 16px;display:flex;flex-direction:column;gap:12px;position:relative;overflow:hidden;min-height:435px}
      .mini-head{text-transform:uppercase;letter-spacing:1.15px;color:var(--sub);font-size:11px;font-weight:800}
      .machine .machine-art{display:flex;justify-content:center;align-items:center;min-height:138px;flex:1}
      .fan-shell{width:min(100%,185px);aspect-ratio:1.16/1;background:var(--fan-bg);border:1px solid var(--fan-edge);border-radius:13px;
        display:flex;align-items:center;justify-content:center;position:relative;box-shadow:inset 0 0 0 6px var(--fan-inset)}
      .fan-shell:after{content:'';position:absolute;right:8px;top:10px;bottom:10px;width:8px;border-radius:3px;
        background:repeating-linear-gradient(to bottom,#6f899f 0 3px,transparent 3px 8px)}
      .fan-svg{width:76%;height:82%;color:var(--fan-stroke);overflow:visible}
      .fan-svg .blades{transform-box:view-box;transform-origin:60px 60px}
      /* Illustration du ventilateur synchronisée à l'état compresseur (8400). */
      .fan-shell.running .blades{animation:spin 5s linear infinite;will-change:transform}
      .fan-shell.running{border-color:var(--green);box-shadow:0 0 0 1px var(--green), inset 0 0 0 6px var(--fan-inset)}
      @keyframes spin{to{transform:rotate(360deg)}}
      .big-value{font-variant-numeric:tabular-nums;font-size:clamp(23px,2.8vw,35px);font-weight:760;line-height:1.12}
      .field-title{font-size:11px;color:var(--sub);margin-bottom:6px}
      .machine-stat{padding-top:11px;border-top:1px solid var(--line)}
      .mod-bar{background:var(--soft2);height:7px;border-radius:10px;overflow:hidden;margin:8px 0 0}
      .mod-bar>i{display:block;height:100%;width:0%;border-radius:inherit;background:linear-gradient(90deg,#61b1d7,#56d6b1)}
      .pac-art{flex:1;min-height:102px;display:flex;align-items:center;gap:12px;margin:4px 0}
      .exchanger{display:flex;justify-content:space-evenly;align-items:center;gap:14px;width:100%}
      .exch-col{display:flex;flex-direction:column;align-items:center;gap:8px;color:var(--blue)}
      .exch-col.hot{color:var(--red)}
      .exch-col svg{width:76px;max-width:100%;height:94px;fill:none;stroke:currentColor;stroke-width:5;stroke-linecap:round;stroke-linejoin:round;
        filter:drop-shadow(0 0 3px currentColor);opacity:.9;transition:opacity .25s ease,filter .25s ease}
      /* Pas d'activité du compresseur : échangeurs visibles, sans animation. */
      .exchanger.standby .exch-col svg{opacity:.33;filter:none}
      /* La pulsation est purement indicative : aucune température frigorifique n'est inventée. */
      .exchanger.running .exch-col svg{animation:exchangerPulse 2.8s ease-in-out infinite}
      /* Animation limitée à l'opacité : évite d'animer les filtres SVG. */
      @keyframes exchangerPulse {0%,100%{opacity:.70}50%{opacity:1}}
      .exch-caption{font-size:10px;color:var(--sub);white-space:nowrap}
      .pac-metrics{display:grid;grid-template-columns:1fr 1fr;gap:10px 12px;border-top:1px solid var(--line);padding-top:13px}
      .pac-metrics>div span{display:block;color:var(--sub);font-size:11px}.pac-metrics>div strong{display:block;font-size:17px;margin-top:5px;font-variant-numeric:tabular-nums}
      .pac-bottom{margin-top:8px;font-size:11px;color:var(--sub);line-height:1.5}
      .linksvg{width:100%;height:100%;display:block;overflow:visible}
      /* Q3 : symbole hydraulique trois voies, lecture seule. */
      .outlink{position:relative}
      .v3v-symbol{position:absolute;left:33%;top:50%;transform:translate(-50%,-50%);
        width:54px;height:54px;pointer-events:none;z-index:2;color:var(--text)}
      .v3v-symbol svg{display:block;width:100%;height:100%;overflow:visible}
      .v3v-symbol .port{fill:none;stroke:var(--pipe);stroke-width:7;stroke-linecap:round}
      .v3v-symbol .body{fill:var(--surface);stroke:var(--panel-line);stroke-width:2}
      .v3v-symbol .route{fill:none;stroke-width:5;stroke-linecap:round;stroke-linejoin:round;
        opacity:0;transition:opacity .4s ease}
      .v3v-symbol .route-heat{stroke:var(--red)}
      .v3v-symbol.cooling .route-heat{stroke:var(--blue)}
      .v3v-symbol .route-ecs{stroke:var(--red)}
      .v3v-symbol.to-heat .route-heat,.v3v-symbol.to-ecs .route-ecs{opacity:1}
      .v3v-symbol .valve-core{fill:var(--text);opacity:.65}
      .v3v-symbol.unknown .body{opacity:.6}
      :host([data-animate-flows="false"]) .v3v-symbol .route{transition:none}
      :host([data-show-links="false"]) .v3v-symbol{display:none}
      .vertical-link{display:none}
      .linksvg path.track{stroke:var(--pipe);stroke-width:9;fill:none;stroke-linejoin:round;stroke-linecap:round}
      .linksvg path.live{stroke-width:4;fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:13 15;animation:flow 1.15s linear infinite}
      .linksvg path.live.heat{stroke:var(--red)}.linksvg path.live.cool{stroke:var(--blue)}.linksvg path.live.electric{stroke:var(--amber)}
      .linksvg path.live.active{stroke:var(--green)}
      @keyframes flow {to{stroke-dashoffset:-28}}
      .output-card{padding:15px 15px 12px;display:flex;flex-direction:column;justify-content:center;gap:10px;min-height:130px;position:relative;border-left:3px solid var(--panel-line)}
      .output-card.heat{border-left-color:var(--red)} .output-card.cool{border-left-color:var(--blue)}
      .output-card.electric{border-left-color:var(--amber)}
      .out-top{display:flex;align-items:center;gap:11px}
      .out-ico{flex:0 0 36px;width:36px;height:36px;color:var(--icon);display:grid;place-items:center}
      .symbol{width:29px;height:29px;display:block}
      .out-head{flex:1;min-width:0}
      .out-title{font-size:14px;font-weight:750}.out-title span{color:var(--sub);font-weight:500}
      .out-status{font-size:11px;color:var(--sub);margin-top:4px}
      .state-dot{width:9px;height:9px;border-radius:50%;background:var(--pipe);flex:0 0 9px}
      .state-dot.heat{background:var(--red);box-shadow:0 0 12px var(--red)}
      .state-dot.cool{background:var(--blue);box-shadow:0 0 12px var(--blue)}
      .out-values{display:grid;grid-template-columns:1fr 1fr;gap:8px 10px}
      .out-values>div span{color:var(--sub);display:block;font-size:10px}
      .out-values>div strong{display:block;margin-top:3px;font-size:20px;font-weight:750;font-variant-numeric:tabular-nums}
      .out-foot{display:flex;gap:6px;flex-wrap:wrap}.out-foot .chip{font-size:10px;padding:3px 8px}
      .tank-mini{width:28px;height:39px;border-radius:9px;border:2px solid #88aec5;
        background:linear-gradient(0deg,#377bc7,#935cbd 48%,#ff8f6a);box-shadow:inset 0 0 6px var(--tank-shadow)}
      .section{border-top:1px solid var(--line);padding:18px 2px 10px}
      .section-title{display:flex;justify-content:space-between;gap:15px;align-items:center;margin:0 0 12px}
      .section-title h3{font-size:15px;margin:0;font-weight:700}
      .alerts{border:1px solid var(--panel-line);border-radius:14px;background:var(--surface);padding:13px 15px}
      .alerts.alerted{border-color:var(--warn-line);background:var(--warn-panel)}
      .alert-clear{display:flex;align-items:center;gap:12px;color:var(--clear-text)}
      .alert-clear .symbol{flex:0 0 26px}.alert-clear div{display:flex;flex-direction:column;gap:4px}
      .alert-clear strong{font-size:13px}.alert-clear span{font-size:11px;color:var(--sub)}
      .alert-stack{display:grid;gap:12px}.alert-line{display:flex;align-items:center;gap:9px;font-size:12px;font-weight:650;color:var(--warn-text)}
      .alarm-context{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:5px 15px;padding:7px 0 1px 31px}
      .alarm-fact{font-size:11px;display:flex;justify-content:space-between;gap:8px}.alarm-fact span{color:var(--sub)}.alarm-fact strong{text-align:right;font-weight:650}
      .alert-mark{background:#b75b42;color:white;width:21px;height:21px;border-radius:50%;display:grid;place-items:center}
      .alert-meta{color:var(--sub);font-size:10px;margin-top:9px;line-height:1.6}
      details{margin-top:15px;border-top:1px solid var(--line);padding-top:14px}
      details.alarm-details{padding:14px 2px 0;margin-top:0}
      .alarm-details>summary .chip{margin-left:auto;white-space:nowrap}
      .alarm-details>.alerts{margin-top:13px}
      .pac-head-status{display:flex;gap:6px;flex-wrap:wrap}
      details>summary{cursor:pointer;list-style:none;font-weight:700;font-size:14px;display:flex;align-items:center;gap:8px;user-select:none}
      details>summary::-webkit-details-marker{display:none}
      details>summary:before{content:'▸';color:var(--summary-chevron);transition:transform .15s}details[open]>summary:before{transform:rotate(90deg)}
      .details-note{color:var(--sub);font-size:11px;margin:11px 0 13px;line-height:1.5}
      .diag-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
      .diag-group{min-width:0;background:var(--surface);padding:13px;border-radius:12px;border:1px solid var(--panel-line)}
      .diag-group h4{margin:0 0 10px;font-size:12px;color:var(--text)}
      .weekly-tabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
      .weekly-tab{border:1px solid var(--panel-line);border-radius:8px;padding:7px 12px;
        background:transparent;color:var(--text);font-size:11px;cursor:pointer}
      .weekly-tab.active{background:var(--soft);border-color:var(--blue);font-weight:700}
      .weekly-info{font-size:11px;color:var(--sub);margin-bottom:10px;line-height:1.5}
      .weekly-scale,.weekly-row{display:grid;grid-template-columns:30px minmax(0,1fr);gap:8px}
      .weekly-scale{margin:0 0 6px}
      .weekly-scale>div{display:flex;justify-content:space-between;font-size:9px;color:var(--sub)}
      .weekly-rows{display:grid;gap:7px}
      .weekly-row{align-items:start}
      .weekly-day{font-size:11px;font-weight:650;padding-top:1px}
      .weekly-day-body{min-width:0}
      .weekly-track{height:11px;border-radius:4px;position:relative;overflow:hidden;
        background:var(--soft)}
      .weekly-slot{position:absolute;top:0;bottom:0;background:var(--blue);border-radius:3px}
      .weekly-times{font-size:10px;color:var(--sub);margin-top:3px;line-height:1.45;overflow-wrap:anywhere}
      .weekly-error{color:var(--warn-text);font-size:11px;overflow-wrap:anywhere}
      .weekly-note{color:var(--sub);font-size:10px;line-height:1.5;margin:12px 0 0}
      .detail-row{border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:10px;justify-content:space-between;padding:6px 0;font-size:11px}
      .detail-row:last-child{border:0}.detail-row span{color:var(--sub);min-width:0}.detail-row strong{text-align:right;font-weight:700;max-width:58%;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}
      .detail-row strong.na{color:var(--muted)}
      /* Width is measured in the actual Lovelace card, not screen pixels. */
      @container (max-width:1100px){
        .wrap{padding:16px}
        .schematic{grid-template-columns:minmax(128px,.85fr) 24px minmax(175px,1fr) 34px minmax(220px,1.6fr);gap:8px 0}
        .machine,.pac{padding:12px 10px;min-width:0}
        .out-values>div strong{font-size:16px}
        .out-title{font-size:12px}
        .output-card{padding:10px;min-width:0}
        .fan-shell{width:min(100%,130px)}
        .pac-metrics>div strong{font-size:14px}
        .big-value{font-size:24px}
      }
      /* Vertical layout only when the horizontal composition is no longer legible. */
      @container (max-width:680px){
        .schematic{display:flex;flex-direction:column;gap:0}
        .machine,.pac{min-height:unset;width:100%}
        .machine{display:grid;grid-template-columns:100px minmax(0,1fr);gap:7px 13px;align-items:center}
        .machine .mini-head{grid-column:1/3}
        .machine .machine-art{min-height:100px;grid-row:2/5}
        .machine .fan-shell{width:94px}
        .machine .machine-stat{padding-top:5px}
        .pac-art{min-height:85px}
        .inlink,.outlink{display:block;flex:0 0 56px;height:56px;align-self:stretch;overflow:hidden}
        .outlink .v3v-symbol{left:50%;top:50%;width:40px;height:40px;transform:translate(-50%,-50%) rotate(90deg)}
        .inlink .horizontal-link,.outlink .horizontal-link{display:none}
        .inlink .vertical-link,.outlink .vertical-link{display:block;height:100%;width:100%;overflow:hidden}
        .outs{display:flex;flex-direction:column;gap:10px;position:relative;padding-left:22px;margin-top:0}
        .outs:before{content:'';position:absolute;left:9px;top:0;bottom:55px;width:7px;border-radius:4px;background:var(--pipe)}
        .output-card{min-height:115px;position:relative;overflow:visible}
        .output-card:before{content:'';position:absolute;left:-23px;top:50%;width:23px;height:7px;margin-top:-3px;background:var(--pipe)}
        .output-card.heat:after,.output-card.cool:after{content:'';position:absolute;left:-23px;top:50%;width:23px;height:4px;margin-top:-2px;background:var(--red);background-image:repeating-linear-gradient(90deg,transparent 0 7px,var(--surface2) 7px 11px);background-size:22px 4px;animation:branchFlow 1.1s linear infinite}
        .output-card.cool:after{background-color:var(--blue)}
        @keyframes branchFlow{to{background-position:22px 0}}
        .diag-grid{grid-template-columns:1fr}
        .out-values{grid-template-columns:repeat(2,minmax(0,1fr))}
      }
      @container (max-width:400px){
        .machine{grid-template-columns:80px minmax(0,1fr)}
        .machine .fan-shell{width:76px}
        .pac-metrics{gap:8px}
        .out-values{grid-template-columns:1fr 1fr}
        .out-values>div strong{font-size:16px}
      }

      /* Présentation épurée facultative : aucune liaison hydraulique illustrative.
         Les trois usages restent séparés ; leurs repères reflètent le mode réel. */
      :host([data-layout-style="clean"]) .schematic {
        grid-template-columns:minmax(0,.95fr) 24px minmax(0,1.12fr) 38px minmax(0,1.5fr);
        grid-template-rows:repeat(3,minmax(130px,auto));
        column-gap:14px;row-gap:12px;
      }
      :host([data-layout-style="clean"]) .machine {grid-column:1;grid-row:1/4}
      :host([data-layout-style="clean"]) .inlink {grid-column:2;grid-row:1/4}
      :host([data-layout-style="clean"]) .pac {grid-column:3;grid-row:1/4}
      :host([data-layout-style="clean"]) .outlink {grid-column:4;grid-row:1/4}
      :host([data-layout-style="clean"]) .outs {grid-column:5;grid-row:1/4;gap:12px;padding:0;margin:0}
      /* Liaison graphique horizontale : équilibre entre finesse et lisibilité. */
      :host([data-layout-style="clean"]) .linksvg path.track {stroke-width:5;opacity:.65}
      :host([data-layout-style="clean"]) .linksvg path.live {stroke-width:3;stroke-dasharray:10 15}
      :host([data-layout-style="clean"][data-show-links="false"]) .inlink,
      :host([data-layout-style="clean"][data-show-links="false"]) .outlink {visibility:hidden}
      :host([data-animate-flows="false"]) .linksvg path.live {animation:none!important;stroke-dasharray:none}
      :host([data-animate-flows="false"]) .exchanger.running .exch-col svg,
      :host([data-animate-flows="false"]) .fan-shell.running .blades {animation:none!important}
      :host([data-layout-style="clean"]) .outs:before,
      :host([data-layout-style="clean"]) .output-card:before,
      :host([data-layout-style="clean"]) .output-card:after {display:none!important;content:none!important}
      :host([data-layout-style="clean"]) .output-card {
        border-left:3px solid var(--panel-line);
        overflow:hidden;
        transition:border-color .25s ease,box-shadow .25s ease;
      }
      :host([data-layout-style="clean"]) .output-card.regime-heat {
        border-left-color:color-mix(in srgb,var(--red) 45%,var(--panel-line));
      }
      :host([data-layout-style="clean"]) .output-card.regime-cool {
        border-left-color:color-mix(in srgb,var(--blue) 45%,var(--panel-line));
      }
      :host([data-layout-style="clean"]) .output-card.heat {
        border-left-color:var(--red);
        box-shadow:inset 3px 0 0 color-mix(in srgb,var(--red) 35%,transparent);
      }
      :host([data-layout-style="clean"]) .output-card.cool {
        border-left-color:var(--blue);
        box-shadow:inset 3px 0 0 color-mix(in srgb,var(--blue) 35%,transparent);
      }
      :host([data-layout-style="clean"]) .output-card.electric {border-left-color:var(--amber)}
      :host([data-layout-style="clean"]) .output-card[aria-label="Eau chaude sanitaire"]:not(.electric) {
        border-left-color:color-mix(in srgb,#9276cf 48%,var(--panel-line));
      }
      :host([data-layout-style="clean"]) .output-card.regime-heat .out-ico {color:var(--red)}
      :host([data-layout-style="clean"]) .output-card.regime-cool .out-ico {color:var(--blue)}
      @container (max-width:900px) {
        :host([data-layout-style="clean"]) .schematic {
          display:flex;flex-direction:column;gap:12px;
        }
        :host([data-layout-style="clean"]) .inlink,
        :host([data-layout-style="clean"]) .outlink {display:none!important}
        :host([data-layout-style="clean"]) .machine,
        :host([data-layout-style="clean"]) .pac {min-height:unset;width:100%}
        :host([data-layout-style="clean"]) .outs {
          display:flex;flex-direction:column;gap:10px;margin:0;padding:0;width:100%;
        }
        :host([data-layout-style="clean"]) .output-card {min-height:116px}
      }

      /* V2.8 : plus compact sans supprimer d'informations ni changer les entités. */
      .wrap{padding:14px 16px 14px}
      .schematic{margin:0 0 12px;grid-template-rows:repeat(3,minmax(108px,auto));row-gap:9px}
      :host([data-layout-style="clean"]) .schematic{
        grid-template-rows:repeat(3,minmax(108px,auto));row-gap:9px}
      .machine,.pac{min-height:354px;padding:13px 14px;gap:9px}
      .machine .machine-art{min-height:104px}
      .fan-shell{width:min(100%,154px)}
      .big-value{font-size:clamp(22px,2.5vw,31px)}
      .machine-stat{padding-top:7px}
      .pac-art{min-height:93px;margin:1px 0}
      .exch-col svg{width:65px;height:78px}
      .exchanger{gap:9px}
      .pac-metrics{gap:8px 11px;padding-top:10px}
      .pac-bottom{margin-top:3px}
      .outs{grid-template-rows:repeat(3,minmax(108px,auto));gap:9px}
      .output-card{min-height:108px;padding:11px 13px 10px;gap:7px}
      .out-top{gap:8px}.out-ico{width:32px;flex-basis:32px;height:32px}
      .out-values>div strong{font-size:18px}
      .section{padding-top:13px}
      details{margin-top:12px;padding-top:12px}
      details.alarm-details{padding-top:10px}
      .diag-group{padding:11px}
      .diag-grid{gap:9px}
      .linksvg path.live{stroke-dasharray:12 14}
      /* Orientations : aucun fichier image, uniquement HTML/CSS et SVG incorporé. */
      :host([data-orientation="landscape"]) .wrap{overflow-x:auto;overscroll-behavior-x:contain}
      :host([data-orientation="landscape"]) .schematic,
      :host([data-orientation="landscape"][data-layout-style="clean"]) .schematic{
        display:grid;grid-template-columns:minmax(160px,.85fr) 32px minmax(190px,1fr) 62px minmax(280px,1.7fr);
        grid-template-rows:repeat(3,minmax(108px,auto));min-width:830px;row-gap:9px;column-gap:0}
      :host([data-orientation="landscape"]) .machine{grid-column:1;grid-row:1/4;display:flex}
      :host([data-orientation="landscape"]) .inlink{grid-column:2;grid-row:1/4;display:block!important;height:auto;flex:auto}
      :host([data-orientation="landscape"]) .pac{grid-column:3;grid-row:1/4;display:flex}
      :host([data-orientation="landscape"]) .outlink{grid-column:4;grid-row:1/4;display:block!important;height:auto;flex:auto}
      :host([data-orientation="landscape"]) .outs{grid-column:5;grid-row:1/4;display:grid;
        grid-template-rows:repeat(3,minmax(108px,auto));gap:9px;padding:0;margin:0}
      :host([data-orientation="landscape"]) .horizontal-link{display:block}
      :host([data-orientation="landscape"]) .vertical-link{display:none}
      :host([data-orientation="landscape"]) .outs:before,
      :host([data-orientation="landscape"]) .output-card:before,
      :host([data-orientation="landscape"]) .output-card:after{display:none!important}
      :host([data-orientation="landscape"][data-show-links="false"]) .inlink,
      :host([data-orientation="landscape"][data-show-links="false"]) .outlink{visibility:hidden}
      :host([data-orientation="landscape"]) .output-card{overflow:hidden}
      /* Portrait manuel, indépendamment de la largeur du dashboard. */
:host([data-orientation="portrait"]) .schematic{display:flex;flex-direction:column;gap:0;min-width:0;grid-template-columns:none;grid-template-rows:none}
:host([data-orientation="portrait"]) .machine, :host([data-orientation="portrait"]) .pac{min-height:0;width:100%;padding:12px 13px}
:host([data-orientation="portrait"]) .machine{display:grid;grid-template-columns:92px minmax(0,1fr);align-items:center;gap:5px 12px}
:host([data-orientation="portrait"]) .machine .mini-head{grid-column:1/-1}
:host([data-orientation="portrait"]) .machine .machine-art{grid-column:1;grid-row:2/5;min-height:90px;align-self:stretch}
:host([data-orientation="portrait"]) .machine .fan-shell{width:82px}
:host([data-orientation="portrait"]) .machine .machine-stat{padding-top:5px}
:host([data-orientation="portrait"]) .big-value{font-size:clamp(20px,5.2vw,27px)}
:host([data-orientation="portrait"]) .pac-art{min-height:85px;margin:1px 0}
:host([data-orientation="portrait"]) .exch-col svg{height:66px;width:54px}
:host([data-orientation="portrait"]) .pac-metrics{gap:6px 10px;padding-top:9px}
:host([data-orientation="portrait"]) .pac-bottom{font-size:10px}
:host([data-orientation="portrait"]) .inlink, :host([data-orientation="portrait"]) .outlink{display:block;grid-column:auto;grid-row:auto;flex:0 0 38px;height:38px;width:100%;align-self:stretch;overflow:hidden}
:host([data-orientation="portrait"]) .horizontal-link{display:none}
:host([data-orientation="portrait"]) .vertical-link{display:block;width:100%;height:100%;overflow:hidden}
:host([data-orientation="portrait"]) .outs{display:flex;flex-direction:column;grid-column:auto;grid-row:auto;gap:8px;padding-left:20px;margin:0;position:relative;min-width:0}
:host([data-orientation="portrait"]) .outs:before{content:'';display:block;position:absolute;left:8px;top:0;bottom:50px;width:5px;border-radius:4px;background:var(--pipe)}
:host([data-orientation="portrait"]) .output-card{position:relative;min-height:105px;padding:10px 12px;overflow:visible}
:host([data-orientation="portrait"]) .output-card:before{content:'';display:block;position:absolute;left:-21px;top:50%;width:21px;height:5px;margin-top:-2px;background:var(--pipe)}
:host([data-orientation="portrait"]) .output-card.heat:after, :host([data-orientation="portrait"]) .output-card.cool:after{content:'';display:block;position:absolute;left:-21px;top:50%;width:21px;height:3px;margin-top:-1px;background-color:var(--red);background-image:repeating-linear-gradient(90deg,transparent 0 7px,var(--surface2) 7px 11px);animation:branchFlow 1.1s linear infinite}
:host([data-orientation="portrait"]) .output-card.cool:after{background-color:var(--blue)}
:host([data-orientation="portrait"]) .diag-grid{grid-template-columns:1fr}
:host([data-orientation="portrait"]) .out-values{grid-template-columns:repeat(2,minmax(0,1fr))}
:host([data-orientation="portrait"]) .output-card .out-values strong{font-size:17px}
:host([data-orientation="portrait"]) .wrap{overflow-x:visible}
:host([data-orientation="portrait"]) .schematic .outs .output-card{width:100%}
:host([data-orientation="portrait"]) .machine .machine-art .fan-shell{max-width:90px}
      /* Auto : suit la largeur réelle de la carte, utile sur mobile/tablette. */
      @container (max-width:800px){
:host([data-orientation="auto"]) .schematic{display:flex;flex-direction:column;gap:0;min-width:0;grid-template-columns:none;grid-template-rows:none}
:host([data-orientation="auto"]) .machine, :host([data-orientation="auto"]) .pac{min-height:0;width:100%;padding:12px 13px}
:host([data-orientation="auto"]) .machine{display:grid;grid-template-columns:92px minmax(0,1fr);align-items:center;gap:5px 12px}
:host([data-orientation="auto"]) .machine .mini-head{grid-column:1/-1}
:host([data-orientation="auto"]) .machine .machine-art{grid-column:1;grid-row:2/5;min-height:90px;align-self:stretch}
:host([data-orientation="auto"]) .machine .fan-shell{width:82px}
:host([data-orientation="auto"]) .machine .machine-stat{padding-top:5px}
:host([data-orientation="auto"]) .big-value{font-size:clamp(20px,5.2vw,27px)}
:host([data-orientation="auto"]) .pac-art{min-height:85px;margin:1px 0}
:host([data-orientation="auto"]) .exch-col svg{height:66px;width:54px}
:host([data-orientation="auto"]) .pac-metrics{gap:6px 10px;padding-top:9px}
:host([data-orientation="auto"]) .pac-bottom{font-size:10px}
:host([data-orientation="auto"]) .inlink, :host([data-orientation="auto"]) .outlink{display:block;grid-column:auto;grid-row:auto;flex:0 0 38px;height:38px;width:100%;align-self:stretch;overflow:hidden}
:host([data-orientation="auto"]) .horizontal-link{display:none}
:host([data-orientation="auto"]) .vertical-link{display:block;width:100%;height:100%;overflow:hidden}
:host([data-orientation="auto"]) .outs{display:flex;flex-direction:column;grid-column:auto;grid-row:auto;gap:8px;padding-left:20px;margin:0;position:relative;min-width:0}
:host([data-orientation="auto"]) .outs:before{content:'';display:block;position:absolute;left:8px;top:0;bottom:50px;width:5px;border-radius:4px;background:var(--pipe)}
:host([data-orientation="auto"]) .output-card{position:relative;min-height:105px;padding:10px 12px;overflow:visible}
:host([data-orientation="auto"]) .output-card:before{content:'';display:block;position:absolute;left:-21px;top:50%;width:21px;height:5px;margin-top:-2px;background:var(--pipe)}
:host([data-orientation="auto"]) .output-card.heat:after, :host([data-orientation="auto"]) .output-card.cool:after{content:'';display:block;position:absolute;left:-21px;top:50%;width:21px;height:3px;margin-top:-1px;background-color:var(--red);background-image:repeating-linear-gradient(90deg,transparent 0 7px,var(--surface2) 7px 11px);animation:branchFlow 1.1s linear infinite}
:host([data-orientation="auto"]) .output-card.cool:after{background-color:var(--blue)}
:host([data-orientation="auto"]) .diag-grid{grid-template-columns:1fr}
:host([data-orientation="auto"]) .out-values{grid-template-columns:repeat(2,minmax(0,1fr))}
:host([data-orientation="auto"]) .output-card .out-values strong{font-size:17px}
:host([data-orientation="auto"]) .wrap{overflow-x:visible}
:host([data-orientation="auto"]) .schematic .outs .output-card{width:100%}
:host([data-orientation="auto"]) .machine .machine-art .fan-shell{max-width:90px}
      }
      /* Clean : ne pas montrer une tuyauterie trompeuse en portrait. */
      :host([data-orientation="portrait"][data-layout-style="clean"]) .outs:before,
      :host([data-orientation="portrait"][data-layout-style="clean"]) .output-card:before,
      :host([data-orientation="portrait"][data-layout-style="clean"]) .output-card:after{display:none!important}
      @container (max-width:800px){
        :host([data-orientation="auto"][data-layout-style="clean"]) .outs:before,
        :host([data-orientation="auto"][data-layout-style="clean"]) .output-card:before,
        :host([data-orientation="auto"][data-layout-style="clean"]) .output-card:after{display:none!important}
      }
      :host([data-orientation="portrait"][data-show-links="false"]) .inlink,
      :host([data-orientation="portrait"][data-show-links="false"]) .outlink{visibility:hidden}
      @container (max-width:800px){
        :host([data-orientation="auto"][data-show-links="false"]) .inlink,
        :host([data-orientation="auto"][data-show-links="false"]) .outlink{visibility:hidden}
      }
      :host([data-animate-flows="false"]) .output-card:after{animation:none!important}
      @media(prefers-reduced-motion:reduce){.output-card:after{animation:none!important}}
      @media(prefers-reduced-motion:reduce){.linksvg path.live,.fan-shell.running .blades,.exchanger.running .exch-col svg{animation:none!important}}

      /* V2.8.2 : portrait mobile sans faux collecteur latéral. Des traits courts
         relient COMP → PAC → groupe de sorties, sans branches traversantes.
         Les cartes conservent leur bordure d'état et leur largeur complète. */
      :host([data-orientation="portrait"]) .outs{
        padding-left:0!important;gap:10px;margin:0;min-width:0}
      :host([data-orientation="portrait"]) .outs:before,
      :host([data-orientation="portrait"]) .output-card:before,
      :host([data-orientation="portrait"]) .output-card:after{display:none!important;content:none!important}
      :host([data-orientation="portrait"]) .output-card{
        width:100%;max-width:100%;box-sizing:border-box;overflow:hidden;min-width:0}
      :host([data-orientation="portrait"]) .inlink,
      :host([data-orientation="portrait"]) .outlink{
        flex-basis:25px;height:25px;min-height:25px}
      @container (max-width:800px){
        :host([data-orientation="auto"]) .outs{
          padding-left:0!important;gap:10px;margin:0;min-width:0}
        :host([data-orientation="auto"]) .outs:before,
        :host([data-orientation="auto"]) .output-card:before,
        :host([data-orientation="auto"]) .output-card:after{
          display:none!important;content:none!important}
        :host([data-orientation="auto"]) .output-card{
          width:100%;max-width:100%;box-sizing:border-box;overflow:hidden;min-width:0}
        :host([data-orientation="auto"]) .inlink,
        :host([data-orientation="auto"]) .outlink{
          flex-basis:25px;height:25px;min-height:25px}
      }

      /* V2.9.0 — style Aérien : fidèle aux dernières maquettes.
         Aucune image/photo, ni donnée supplémentaire ; tous les badges
         natifs et les diagnostics de V1.5.21 restent inchangés. */
      .fan-aerien,.exch-col svg.exch-aerien{display:none}
      :host([data-layout-style="aerien"]){
        --aerien-border:color-mix(in srgb,var(--line) 58%,transparent);
        --aerien-panel:color-mix(in srgb,var(--bg) 96%,var(--blue) 4%);
        --aerien-inner:color-mix(in srgb,var(--bg) 92%,var(--blue) 8%);
        --aerien-tube:color-mix(in srgb,var(--pipe) 74%,var(--bg) 26%);
      }
      :host([data-layout-style="aerien"]) ha-card{
        background:var(--bg);border:0;box-shadow:none}
      :host([data-layout-style="aerien"]) .wrap{padding:12px 14px 14px}
      :host([data-layout-style="aerien"]) .schematic{
        grid-template-columns:minmax(166px,1.06fr) 33px minmax(205px,.94fr) 55px minmax(330px,1.52fr);
        grid-template-rows:repeat(3,minmax(122px,auto));gap:10px 0}
      :host([data-layout-style="aerien"]) .machine,
      :host([data-layout-style="aerien"]) .pac,
      :host([data-layout-style="aerien"]) .output-card{
        background:var(--aerien-panel);border:1px solid var(--aerien-border);
        border-radius:21px;box-shadow:0 3px 13px color-mix(in srgb,var(--text) 5%,transparent)}
      :host([data-layout-style="aerien"]) .machine,
      :host([data-layout-style="aerien"]) .pac{
        min-height:385px;padding:17px 16px;gap:11px}
      :host([data-layout-style="aerien"]) .mini-head{
        text-transform:none;letter-spacing:0;color:var(--text);
        font-size:clamp(13px,1.2vw,17px);font-weight:740;line-height:1.35}
      :host([data-layout-style="aerien"]) .machine .machine-art{
        flex:1;min-height:135px;padding:8px 0}
      :host([data-layout-style="aerien"]) .fan-shell{
        width:min(100%,185px);aspect-ratio:1.125/1;
        border:none;border-radius:0;background:transparent;
        box-shadow:none;overflow:visible}
      :host([data-layout-style="aerien"]) .fan-shell:after{content:none}
      :host([data-layout-style="aerien"]) .fan-shell.running{
        border:0;box-shadow:none}
      :host([data-layout-style="aerien"]) .fan-svg:not(.fan-aerien){display:none}
      :host([data-layout-style="aerien"]) .fan-svg.fan-aerien{
        display:block;width:100%;height:100%;color:var(--fan-stroke);overflow:visible}
      :host([data-layout-style="aerien"]) .fan-aerien .unit-case{
        fill:var(--aerien-inner);stroke:var(--fan-edge);stroke-width:2}
      :host([data-layout-style="aerien"]) .fan-aerien .fan-ring{
        fill:none;stroke:var(--fan-stroke);stroke-width:2.2}
      :host([data-layout-style="aerien"]) .fan-aerien .fan-inner{
        fill:color-mix(in srgb,var(--fan-bg) 70%,var(--bg) 30%);stroke:var(--fan-edge);stroke-width:1}
      :host([data-layout-style="aerien"]) .fan-aerien .fan-hub{
        fill:var(--bg);stroke:var(--fan-stroke);stroke-width:2}
      :host([data-layout-style="aerien"]) .fan-aerien .unit-feet{
        fill:none;stroke:var(--fan-edge);stroke-width:3;stroke-linejoin:round}
      :host([data-layout-style="aerien"]) .fan-aerien .blades{
        transform-box:view-box;transform-origin:90px 77px}
      :host([data-layout-style="aerien"]) .machine-stat{
        padding-top:9px;border-top:1px solid var(--aerien-border)}
      :host([data-layout-style="aerien"]) .mod-bar{
        height:9px;background:var(--soft2)}
      :host([data-layout-style="aerien"]) .mod-bar>i{
        background:linear-gradient(90deg,#23bfb0,#36d5a6);
        transition:width .6s ease-out}
      :host([data-layout-style="aerien"]) .pac-art{min-height:130px;gap:8px}
      :host([data-layout-style="aerien"]) .exchanger{gap:12px}
      :host([data-layout-style="aerien"]) .exch-col svg:not(.exch-aerien){display:none}
      :host([data-layout-style="aerien"]) .exch-col svg.exch-aerien{
        display:block;width:69px;max-width:100%;height:92px;
        fill:none;stroke:currentColor;stroke-width:4.5;
        filter:none;opacity:.94}
      :host([data-layout-style="aerien"]) .exch-col .exch-aerien .exch-frame{
        fill:var(--aerien-inner);stroke:currentColor;
        stroke-width:1.8;stroke-opacity:.62}
      :host([data-layout-style="aerien"]) .exch-col .exch-aerien .exch-tube{
        fill:none;stroke:currentColor;stroke-width:4.7;
        stroke-linejoin:round;stroke-linecap:round}
      :host([data-layout-style="aerien"]) .exch-caption{font-size:11px}
      :host([data-layout-style="aerien"]) .pac-metrics{
        border:1px solid var(--aerien-border);border-radius:13px;
        background:var(--aerien-inner);padding:12px;gap:11px}
      :host([data-layout-style="aerien"]) .pac-bottom{
        font-size:10px;line-height:1.35}
      :host([data-layout-style="aerien"]) .outs{
        grid-template-rows:repeat(3,minmax(122px,auto));gap:10px}
      :host([data-layout-style="aerien"]) .output-card{
        min-height:122px;padding:12px 14px;gap:8px;border-left:1px solid var(--aerien-border)}
      :host([data-layout-style="aerien"]) .out-title{
        font-size:14px;font-weight:730}
      :host([data-layout-style="aerien"]) .out-values>div strong{font-size:19px}
      :host([data-layout-style="aerien"]) .out-foot .chip{
        border:0;background:var(--aerien-inner);
        font-size:10px;max-width:100%;white-space:normal;overflow-wrap:anywhere}
      :host([data-layout-style="aerien"]) .state-dot.heat,
      :host([data-layout-style="aerien"]) .state-dot.cool{
        box-shadow:none;animation:aerienSignal 2.8s ease-in-out infinite}
      :host([data-layout-style="aerien"]) .state-dot.electric{
        background:var(--amber);animation:aerienSignal 2.8s ease-in-out infinite}
      @keyframes aerienSignal{
        0%,100%{opacity:1}50%{opacity:.52}
      }
      /* Aérien v2.9.2 : tuyauterie renforcée (sans modifier les autres thèmes). */
      :host([data-layout-style="aerien"]) .linksvg path.track{
        stroke:var(--aerien-tube);stroke-width:8;opacity:.9}
      :host([data-layout-style="aerien"]) .linksvg path.live{
        stroke-width:4;stroke-dasharray:8 15;
        animation:flow 2.25s linear infinite}
      :host([data-layout-style="aerien"]) .v3v-symbol .port{stroke-width:9}
      :host([data-layout-style="aerien"]) .v3v-symbol .route{stroke-width:6}
      :host([data-layout-style="aerien"]) details{
        border:1px solid var(--aerien-border);border-radius:15px;
        padding:12px 15px;margin-top:9px;background:var(--aerien-panel)}
      :host([data-layout-style="aerien"]) details.alarm-details{
        padding:12px 15px}
      :host([data-layout-style="aerien"]) .diag-group,
      :host([data-layout-style="aerien"]) .alerts{
        background:var(--aerien-inner);border-color:var(--aerien-border)}
      /* Paysage imposé : conserver une largeur suffisante pour les trois badges. */
      :host([data-layout-style="aerien"][data-orientation="landscape"]) .schematic{
        display:grid;grid-template-columns:minmax(175px,1.06fr) 32px minmax(210px,.94fr) 58px minmax(360px,1.52fr);
        min-width:900px;grid-template-rows:repeat(3,minmax(122px,auto))}
      /* Auto : les largeurs sont déterminées par la largeur du conteneur Lovelace. */
      @container (min-width:801px) and (max-width:1100px){
        :host([data-layout-style="aerien"][data-orientation="auto"]) .schematic{
          grid-template-columns:minmax(130px,.9fr) 22px minmax(165px,1fr) 28px minmax(240px,1.5fr)}
        :host([data-layout-style="aerien"]) .machine,
        :host([data-layout-style="aerien"]) .pac{padding:12px 10px}
      }
      /* Le symbole reste lisible en portrait Aérien, sans branche fictive. */
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .outlink{
        display:block;flex:0 0 56px;height:56px;align-self:stretch;overflow:hidden}
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .outlink .horizontal-link{display:none}
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .outlink .vertical-link{display:block}
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .outlink .v3v-symbol{
        left:50%;top:50%;width:40px;height:40px;transform:translate(-50%,-50%) rotate(90deg)}
      @container (max-width:800px){
        :host([data-layout-style="aerien"][data-orientation="auto"]) .outlink{
          display:block;flex:0 0 56px;height:56px;align-self:stretch;overflow:hidden}
        :host([data-layout-style="aerien"][data-orientation="auto"]) .outlink .horizontal-link{display:none}
        :host([data-layout-style="aerien"][data-orientation="auto"]) .outlink .vertical-link{display:block}
        :host([data-layout-style="aerien"][data-orientation="auto"]) .outlink .v3v-symbol{
          left:50%;top:50%;width:40px;height:40px;transform:translate(-50%,-50%) rotate(90deg)}
      }
      /* Portrait forcé ou automatique : aucun faux collecteur sur les cartes. */
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .schematic{
        display:flex;flex-direction:column;gap:0;min-width:0}
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .machine,
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .pac{
        min-height:0;padding:13px}
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .outs{
        display:flex;flex-direction:column;gap:10px;padding:0;margin:0}
      :host([data-layout-style="aerien"][data-orientation="portrait"]) .output-card{
        min-height:106px;overflow:hidden}
      @container (max-width:800px){
        :host([data-layout-style="aerien"][data-orientation="auto"]) .schematic{
          display:flex;flex-direction:column;gap:0;min-width:0}
        :host([data-layout-style="aerien"][data-orientation="auto"]) .machine,
        :host([data-layout-style="aerien"][data-orientation="auto"]) .pac{
          min-height:0;padding:13px}
        :host([data-layout-style="aerien"][data-orientation="auto"]) .outs{
          display:flex;flex-direction:column;gap:10px;padding:0;margin:0}
        :host([data-layout-style="aerien"][data-orientation="auto"]) .output-card{
          min-height:106px;overflow:hidden}
      }
      :host([data-layout-style="aerien"]) .output-card:before,
      :host([data-layout-style="aerien"]) .output-card:after,
      :host([data-layout-style="aerien"]) .outs:before{
        content:none!important;display:none!important}
      :host([data-animate-flows="false"]) .state-dot.heat,
      :host([data-animate-flows="false"]) .state-dot.cool,
      :host([data-animate-flows="false"]) .state-dot.electric{
        animation:none!important}
      @media(prefers-reduced-motion:reduce){
        :host([data-layout-style="aerien"]) .state-dot,
        :host([data-layout-style="aerien"]) .mod-bar>i{animation:none!important;transition:none!important}
      }
    </style>
    <ha-card><div class="wrap">
      <!-- Bandeau supprimé ; mode saisonnier présenté dans le module PAC. -->
      <div class="schematic" aria-label="Unité extérieure compresseur, module PAC et trois usages RDC, étage, ECS">
        <section class="machine"><div class="mini-head">Unité extérieure / COMP</div>
          <div class="machine-art"><div class="fan-shell ${fanAnimated?'running':''}" aria-hidden="true"><svg class="fan-svg" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="51" stroke="var(--fan-stroke)" stroke-width="2" fill="var(--soft)"/>
            <g class="blades" fill="var(--fan-stroke)" stroke="var(--panel-line)" stroke-width="1.2">
              <ellipse cx="60" cy="35" rx="14" ry="27"/>
              <ellipse cx="60" cy="35" rx="14" ry="27" transform="rotate(90 60 60)"/>
              <ellipse cx="60" cy="35" rx="14" ry="27" transform="rotate(180 60 60)"/>
              <ellipse cx="60" cy="35" rx="14" ry="27" transform="rotate(270 60 60)"/>
            </g><circle cx="60" cy="60" r="11" fill="var(--soft2)" stroke="var(--fan-stroke)" stroke-width="2"/></svg>
            <svg class="fan-svg fan-aerien" viewBox="0 0 180 160" role="presentation" aria-hidden="true">
              <rect class="unit-case" x="24" y="12" width="132" height="133" rx="12"/>
              <circle class="fan-ring" cx="90" cy="77" r="53"/>
              <circle class="fan-inner" cx="90" cy="77" r="48"/>
              <g class="blades" fill="var(--fan-stroke)">
                <path d="M90 77 C77 59 73 36 88 31 C108 27 111 52 90 77Z"/>
                <path d="M90 77 C77 59 73 36 88 31 C108 27 111 52 90 77Z" transform="rotate(90 90 77)"/>
                <path d="M90 77 C77 59 73 36 88 31 C108 27 111 52 90 77Z" transform="rotate(180 90 77)"/>
                <path d="M90 77 C77 59 73 36 88 31 C108 27 111 52 90 77Z" transform="rotate(270 90 77)"/>
              </g>
              <circle class="fan-hub" cx="90" cy="77" r="9"/>
              <path class="unit-feet" d="M37 145V150H55V145 M126 145V150H144V145"/>
            </svg></div></div>
          <div><div class="field-title">Air extérieur</div><div class="big-value">${html(air)}</div></div>
          <div class="machine-stat"><div class="field-title">Compresseur</div><div>${chip(compressorText,compressionTone==='active'?'positive':'dim')}</div></div>
          <div class="machine-stat"><div class="field-title">Modulation du compresseur</div><div class="big-value">${html(formatted(gauge,'%'))}</div>
            <div class="mod-bar"><i style="width:${gauge!==null?Math.max(0,Math.min(100,gauge)):0}%"></i></div></div>
          ${defrost===true?`<div>${chip('Dégivrage actif','cool')}</div>`:''}
        </section>
        <div class="inlink" aria-hidden="true"><svg class="linksvg horizontal-link" viewBox="0 0 100 440" preserveAspectRatio="none"><path class="track" d="M0 220 H100"/>
          ${compressor===true?'<path class="live active" d="M0 220 H100"/>':''}</svg><svg class="linksvg vertical-link" viewBox="0 0 100 100" preserveAspectRatio="none"><path class="track" d="M50 0 V100"/>${compressor===true?'<path class="live active" d="M50 0 V100"/>':''}</svg></div>
        <section class="pac"><div class="mini-head">PAC · Module hydraulique</div>
          <div class="pac-head-status">${chip(modeText,mode==='heat'?'heat':mode==='cool'?'cool':'dim')}
          ${chip(clean(this._v('pacState')||'État PAC indisponible',36),compressor===true?'positive':'dim')}
          ${chip(v3vLabel,v3vTone)}</div>
          <div class="pac-art"><div class="exchanger ${exchangerRunning?'running':'standby'}" aria-label="Représentation symbolique des échanges thermiques, animation lorsque le compresseur fonctionne">
            <div class="exch-col ${mode==='cool'?'hot':''}"><svg viewBox="0 0 78 100" aria-hidden="true"><path d="M5 6H64Q74 6 74 16V22Q74 31 64 31H15Q5 31 5 41V46Q5 54 15 54H64Q74 54 74 64V69Q74 77 64 77H15Q5 77 5 88V95"/></svg><svg class="exch-aerien" viewBox="0 0 78 100" aria-hidden="true">
              <rect class="exch-frame" x="7" y="4" width="64" height="92" rx="10"/>
              <path class="exch-tube" d="M17 20H56Q63 20 63 27Q63 34 56 34H24Q16 34 16 42Q16 49 24 49H55Q63 49 63 57Q63 64 55 64H24Q16 64 16 72Q16 79 24 79H61"/>
            </svg><span class="exch-caption">${mode==='cool'?'Échange chaud':mode==='heat'?'Échange froid':'Côté extérieur'}</span></div>
            <div class="exch-col ${mode==='cool'?'':'hot'}"><svg viewBox="0 0 78 100" aria-hidden="true"><path d="M5 6H64Q74 6 74 16V22Q74 31 64 31H15Q5 31 5 41V46Q5 54 15 54H64Q74 54 74 64V69Q74 77 64 77H15Q5 77 5 88V95"/></svg><svg class="exch-aerien" viewBox="0 0 78 100" aria-hidden="true">
              <rect class="exch-frame" x="7" y="4" width="64" height="92" rx="10"/>
              <path class="exch-tube" d="M17 20H56Q63 20 63 27Q63 34 56 34H24Q16 34 16 42Q16 49 24 49H55Q63 49 63 57Q63 64 55 64H24Q16 64 16 72Q16 79 24 79H61"/>
            </svg><span class="exch-caption">${mode==='cool'?'Échange froid':mode==='heat'?'Échange chaud':'Côté intérieur'}</span></div>
          </div></div>
          <div class="pac-metrics">
            <div><span>Départ PAC</span><strong>${html(temp(this._v('flow')))}</strong></div>
            <div><span>Retour PAC</span><strong>${html(temp(this._v('returnTemp')))}</strong></div>
            <div><span>Consigne départ</span><strong>${html(temp(this._v('targetFlow')))}</strong></div>
            <div><span>ΔT départ − retour</span><strong>${html(pacDelta)}</strong></div>
          </div><div class="pac-bottom">Températures communes aux circuits · pas de mesure séparée RDC / étage</div>
        </section>
        <div class="outlink" aria-hidden="true"><svg class="linksvg horizontal-link" viewBox="0 0 100 440" preserveAspectRatio="none">
          <path class="track" d="M0 220H33V72H100 M33 220H100 M33 220V368H100"/>
          ${c1Flow?`<path class="live ${branchTone(c1)}" d="M0 220H33V72H100"/>`:''}
          ${c2Flow?`<path class="live ${branchTone(c2)}" d="M0 220H33H100"/>`:''}
          ${ecsViaPac?'<path class="live heat" d="M0 220H33V368H100"/>':''}</svg>
          <div class="v3v-symbol ${v3v==='ecs'?'to-ecs':v3v==='heat'?'to-heat':'unknown'} ${mode==='cool'?'cooling':''}"
            role="img" aria-label="${html(v3vLabel)}" title="${html(v3vLabel)}">
            <svg viewBox="0 0 60 60" aria-hidden="true">
              <path class="port" d="M3 30H30 M30 3V57"/>
              <circle class="body" cx="30" cy="30" r="18"/>
              <path class="route route-heat" d="M14 30H30V13"/>
              <path class="route route-ecs" d="M14 30H30V47"/>
              <circle class="valve-core" cx="30" cy="30" r="3"/>
            </svg>
          </div><svg class="linksvg vertical-link" viewBox="0 0 100 100" preserveAspectRatio="none"><path class="track" d="M50 0 V100"/>${(c1Flow||c2Flow||ecsViaPac)?'<path class="live active" d="M50 0 V100"/>':''}</svg></div>
        <div class="outs">${circHtml(c1)}${circHtml(c2)}
          <section class="output-card ${ecsTone}" aria-label="Eau chaude sanitaire">
            <div class="out-top"><div class="tank-mini" aria-hidden="true"></div><div class="out-head">
              <div class="out-title">ECS <span>· Ballon</span></div><div class="out-status">${html(ecsText)}</div></div>
              <span class="state-dot ${ecsTone}"></span></div>
            <div class="out-values"><div><span>Température ballon</span><strong>${html(temp(ecs.tempBallon))}</strong></div>
              <div><span>Consigne affichée</span><strong>${html(temp(ecs.target))}</strong></div></div>
            <div class="out-foot">${chip(v3v?v3vLabel:ecs.pump===true?'Sortie Q3 active':ecs.pump===false?'Sortie Q3 inactive':'Sortie Q3 inconnue',v3v?v3vTone:ecs.pump===true?'positive':'dim')}
              ${ecs.withElectric?chip('Appoint électrique actif','warning'):''}</div>
          </section>
        </div>
      </div>
      <details data-panel="alarms" class="alarm-details" ${prevAlarms?'open':''}>
        <summary><span>Alarmes et surveillance</span>
          ${chip(`${alertActive.length} alarme${alertActive.length!==1?'s':''} active${alertActive.length!==1?'s':''}`,alertActive.length?'warning':'dim')}</summary>
        <div class="alerts ${alarmsClass}">${alertDescription}<div class="alert-meta">${html(alertsMeta)}</div></div>
      </details>
      ${this._config.show_diagnostics!==false?`<details data-panel="diagnostics" ${prevDetails?'open':''}>
        <summary>Diagnostics et capteurs complémentaires · ${statesCount} entités reconnues</summary>
        <p class="details-note">Lecture seule. « — » signifie : entité absente, désactivée, inconnue ou non publiée par BSB-LAN. Les températures de départ cibles des circuits ne sont pas des mesures.</p>
        <div class="diag-grid">${diagComp}${diagPac}${diagCircs}${diagWeekly}</div>
      </details>`:''}

    </div></ha-card>`;
    this.shadowRoot.querySelectorAll('[data-program-tab]').forEach(button=>{
      button.addEventListener('click',()=>{
        this._programTab=button.dataset.programTab;
        this._render();
      });
    });
  }
}
/**
 * Éditeur visuel natif Lovelace. Aucune commande BSB-LAN : cet élément ne
 * manipule que la configuration locale du rendu du synoptique.
 */
class PacSynoptiqueCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:'open'});
    this.shadowRoot.addEventListener('change', event => {
      if (!this._config) return;
      const element=event.target;
      if (element?.id==='pac-theme-choice') {
        const theme=element.value;
        if (['auto','light','dark'].includes(theme)) this._changed('theme_mode',theme);
      } else if (element?.id==='pac-orientation-choice') {
        if (['auto','landscape','portrait'].includes(element.value)) this._changed('layout_orientation',element.value);
      } else if (element?.id==='pac-layout-choice') {
        this._changed('layout_style',element.value);
      } else if (element?.id==='pac-show-links') {
        this._changed('show_links',Boolean(element.checked));
      } else if (element?.id==='pac-animate-flows') {
        this._changed('animate_flows',Boolean(element.checked));
      } else if (element?.id==='pac-show-pump-badges') {
        this._changed('show_pump_badges',Boolean(element.checked));
      } else if (element?.id==='pac-show-diagnostics') {
        this._changed('show_diagnostics',Boolean(element.checked));
      }
    });
  }
  setConfig(config) {
    if (!config || typeof config !== 'object' || Array.isArray(config)) {
      throw new Error('Configuration de carte incorrecte');
    }
    this._config={...config};
    this._render();
  }
  set hass(hass) {this._hass=hass;}
  _changed(key,value) {
    // Conserve les paramètres additionnels/associations d'entités et la
    // largeur, même s'ils ne sont pas modifiés dans l'éditeur visuel.
    const config={...this._config,[key]:value};
    this._config=config;
    this.dispatchEvent(new CustomEvent('config-changed',{
      detail:{config},bubbles:true,composed:true
    }));
  }
  _render() {
    const config=this._config||{};
    const theme=['auto','light','dark'].includes(config.theme_mode)?config.theme_mode:'auto';
    const selected=value=>theme===value?' selected':'';
    const checked=config.show_diagnostics!==false?' checked':'';
    const checkedLinks=config.show_links!==false?' checked':'';
    const checkedMotion=config.animate_flows!==false?' checked':'';
    const checkedPumps=config.show_pump_badges!==false?' checked':'';
    const selectedLayout=(config.layout_style||'classic');
    const selectedOrientation=['auto','landscape','portrait'].includes(config.layout_orientation)?config.layout_orientation:'auto';
    this.shadowRoot.innerHTML=`
      <style>
        :host{display:block;color:var(--primary-text-color,#243443);
          font-family:var(--primary-font-family,Roboto,Arial,sans-serif);
          font-size:14px}
        *{box-sizing:border-box}
        .editor{display:grid;gap:20px;padding:16px 0 8px}
        .field{display:grid;gap:9px}
        label{font-size:14px;font-weight:600;line-height:1.35}
        select{display:block;min-height:48px;width:100%;font:inherit;
          color:var(--primary-text-color,#243443);
          background:var(--card-background-color,var(--ha-card-background,#fff));
          border:1px solid var(--divider-color,#8da0b0);border-radius:10px;
          padding:10px 12px;cursor:pointer}
        select:focus-visible,input:focus-visible{outline:2px solid
          var(--primary-color,#03a9f4);outline-offset:3px}
        .toggle{display:flex;align-items:center;gap:12px;cursor:pointer}
        input[type=checkbox]{width:19px;height:19px;accent-color:var(--primary-color,#03a9f4);
          flex:none;cursor:pointer}
        .hint{color:var(--secondary-text-color,#65788b);line-height:1.45;font-size:12px}
        .notice{border-top:1px solid var(--divider-color,#abb7c0);padding-top:12px}
      </style>
      <div class="editor">
        <div class="field">
          <label for="pac-theme-choice">Apparence du synoptique</label>
          <select id="pac-theme-choice" aria-label="Apparence du synoptique">
            <option value="auto"${selected('auto')}>Automatique (thème Home Assistant)</option>
            <option value="light"${selected('light')}>Clair</option>
            <option value="dark"${selected('dark')}>Sombre</option>
          </select>
          <div class="hint">Automatique suit le thème actuellement utilisé dans Home Assistant.</div>
        </div>
        <div class="field">
          <label for="pac-orientation-choice">Orientation de la carte</label>
          <select id="pac-orientation-choice">
            <option value="auto"${selectedOrientation==='auto'?' selected':''}>Automatique — selon la largeur disponible</option>
            <option value="landscape"${selectedOrientation==='landscape'?' selected':''}>Paysage — horizontal</option>
            <option value="portrait"${selectedOrientation==='portrait'?' selected':''}>Portrait — vertical (mobile)</option>
          </select>
          <div class="hint">Le mode Paysage reste horizontal sur mobile, avec défilement si nécessaire.</div>
        </div>
        <div class="field">
          <label for="pac-layout-choice">Présentation des circuits</label>
          <select id="pac-layout-choice">
            <option value="clean"${selectedLayout==='clean'?' selected':''}>Épurée — traits horizontaux discrets, sans liaisons en portrait</option>
            <option value="classic"${selectedLayout==='classic'?' selected':''}>Classique — tuyauterie schématique</option>
            <option value="aerien"${selectedLayout==='aerien'?' selected':''}>Aérien — dessin simplifié et cartes légères</option>
          </select>
          <div class="hint">Aérien : ventilateur de face et échangeurs assortis, raccordements fins. Classique et Épurée restent disponibles. Les liaisons ne sont pas un schéma hydraulique certifié.</div>
        </div>
        <div class="field">
          <label class="toggle" for="pac-show-links">
            <input type="checkbox" id="pac-show-links"${checkedLinks}>
            Afficher les raccordements en disposition horizontale
          </label>
          <label class="toggle" for="pac-animate-flows">
            <input type="checkbox" id="pac-animate-flows"${checkedMotion}>
            Animer les activités (ventilateur, échangeurs et traits)
          </label>
          <label class="toggle" for="pac-show-pump-badges">
            <input type="checkbox" id="pac-show-pump-badges"${checkedPumps}>
            Afficher l'état des circulateurs sous les circuits
          </label>
        </div>
        <div class="field">
          <label class="toggle" for="pac-show-diagnostics">
            <input type="checkbox" id="pac-show-diagnostics"${checked}>
            Afficher les diagnostics complémentaires
          </label>
          <div class="hint">Les alarmes et leur compteur restent toujours visibles et repliables.</div>
        </div>
        <div class="hint notice">Carte de supervision uniquement · aucune commande envoyée à la PAC.
          La largeur se règle dans l'onglet Disposition du tableau de bord.</div>
      </div>`;
  }
}
if(!customElements.get(EDITOR_TAG)) customElements.define(EDITOR_TAG,PacSynoptiqueCardEditor);

if(!customElements.get(TAG)) customElements.define(TAG,PacSynoptiqueCard);
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type===TAG)) window.customCards.push({
  type:TAG,name:'PAC Synoptique — Atlantic Alféa (lecture seule)',
  description:'Synoptique BSB-LAN lecture seule : COMP, PAC, RDC, étage, ECS, diagnostics et alarmes.',preview:false
});
})();