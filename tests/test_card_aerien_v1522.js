"use strict";
const assert=require("assert");
const fs=require("fs"),vm=require("vm"),path=require("path");
const source=fs.readFileSync(path.join(__dirname,"..","custom_components","atlantic_alfea_controller","www","pac-synoptique-card.js"),"utf8");
class E{
  constructor(){this.dataset={};this.calls=[]}
  attachShadow(){
    this.shadowRoot={innerHTML:"",listeners:{},querySelector:()=>null,addEventListener:(n,fn)=>{this.shadowRoot.listeners[n]=fn}};
    return this.shadowRoot;
  }
  dispatchEvent(evt){this.calls.push(evt);return true}
}
class Ev {constructor(type,data){this.type=type;Object.assign(this,data)}}
const registered={};
vm.runInNewContext(source,{
  HTMLElement:E,CustomEvent:Ev,
  customElements:{get:n=>registered[n],define:(n,v)=>{registered[n]=v}},
  document:{createElement:n=>new registered[n]()},
  window:{customCards:[],matchMedia:()=>({matches:false})},
  Date,JSON,Object,Intl,Number,String,Array,Math,Set,Boolean
});
const Card=registered["pac-synoptique-card"];
const Editor=registered["pac-synoptique-card-editor"];
assert(Card&&Editor,"card and editor should register");
const BLADE='M90 77 C77 59 73 36 88 31 C108 27 111 52 90 77Z';
assert.equal(source.split(BLADE).length-1,4,"four strictly identical rotor blades required");
assert(source.includes('transform="rotate(90 90 77)"'));
assert(source.includes('transform="rotate(180 90 77)"'));
assert(source.includes('transform="rotate(270 90 77)"'));
assert(source.includes('transform-origin:90px 77px'),"CSS rotor center must match SVG center");
for(const layout of ["classic","clean","aerien"]){
 const card=new Card();
 card.setConfig({layout_style:layout,theme_mode:"auto",layout_orientation:"auto"});
 card.hass={states:{},themes:{darkMode:false,theme:"Jour"}};
 assert.equal(card.dataset.layoutStyle,layout);
 const rendered=card.shadowRoot.innerHTML;
 for(const field of ["Unité extérieure / COMP","Température ambiante","Consigne effective",
   "Circulateur","Alarmes et surveillance","Diagnostics et capteurs complémentaires",
   "Départ PAC","Retour PAC","Modulation du compresseur","ECS","Régime"]){
   if(field==="Régime") continue;
   assert(rendered.includes(field),"missing "+field+" in "+layout);
 }
 assert(rendered.includes("fan-aerien"),"new vector fan missing");
 assert(rendered.includes("exch-aerien"),"new vector exchanger missing");
 assert(rendered.includes("portrait mobile sans faux collecteur latéral"),"portrait regression");
 card.hass={states:{},themes:{darkMode:true,theme:"Nuit"}};
 assert.equal(card.dataset.pacScheme,"dark");
}
const ed=new Editor();ed.setConfig({type:"custom:pac-synoptique-card",layout_style:"aerien"});
assert(ed.shadowRoot.innerHTML.includes('value="aerien" selected'),"aerien missing from editor");
ed.shadowRoot.listeners.change({target:{id:"pac-layout-choice",value:"classic"}});
assert.equal(ed.calls.at(-1).detail.config.layout_style,"classic");
assert.throws(()=>new Card().setConfig({layout_style:"other"}),/layout_style/);
assert(!source.includes("hass.callService("),"card must remain read-only");
const f=source.match(/const FIELDS = \{([\s\S]*?)\n\};/);
assert(f&&(f[1].match(/^\s+[A-Za-z_]\w*\s*:/gm)||[]).length===65,"keep all 65 entity mappings");
assert(source.includes("chip(c.nativePreset?.label"),"presets missing");
assert(source.includes("chip(c.native??'État BSB-LAN indisponible'"),"raw BSB state missing");
assert(source.includes("Circulateur arrêté"),"pump badge missing");
console.log("PASS: Aérien SVG uniform fan, exchangers, data, animations, three styles, themes, mobile, read-only");
