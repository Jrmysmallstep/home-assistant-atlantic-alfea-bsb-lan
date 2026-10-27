"use strict";
const assert=require("assert");
const fs=require("fs"),vm=require("vm"),path=require("path");
const src=fs.readFileSync(path.join(__dirname,"..","custom_components","atlantic_alfea_controller","www","pac-synoptique-card.js"),"utf8");
class EventStub{
 constructor(type,opt){this.type=type;Object.assign(this,opt);}
}
class ElementStub {
 constructor(){this.dataset={};this.events=[];}
 attachShadow(){
  this.shadowRoot={innerHTML:"",listeners:{},addEventListener:(n,cb)=>{this.shadowRoot.listeners[n]=cb;},querySelector:()=>null};
  return this.shadowRoot;
 }
 dispatchEvent(e){this.events.push(e);return true;}
}
const regs={};
const ctx={
 HTMLElement:ElementStub,CustomEvent:EventStub,
 customElements:{get:n=>regs[n],define:(n,T)=>{regs[n]=T;}},
 document:{createElement:n=>new regs[n]()},
 window:{customCards:[],matchMedia:()=>({matches:false})},
 Date,JSON,Object,Intl,Number,String,Array,Math,Set,Boolean
};
vm.runInNewContext(src,ctx);
const Card=regs["pac-synoptique-card"],Editor=regs["pac-synoptique-card-editor"];
assert(Card&&Editor,"card and editor must register");
const originalMap=src.match(/const FIELDS = \{([\s\S]*?)\n\};/);
assert(originalMap,"field mapping missing");
const mapped=(originalMap[1].match(/^\s+[A-Za-z_][\w]*\s*:/gm)||[]);
assert(mapped.length>=65,"existing mappings must remain");
assert(src.includes("faultHistory:"),"fault history mapping missing");
assert(src.includes("ALERTS.filter"),"alarm monitoring unchanged");
assert(!/<img\b/i.test(src),"external images prohibited");
assert(!/<image\b/i.test(src),"external SVG image prohibited");
assert(!/https?:\/\/[^\s]/.test(src),"asset URL prohibited");
assert(src.includes(".fan-shell.running .blades{animation:spin"),"fan animation retained");
assert(src.includes(".exchanger.running .exch-col svg{animation:exchangerPulse"),"exchanger animation retained");
assert(src.includes(".linksvg path.live{stroke-width"),"flow animation retained");
assert(src.includes("prefers-reduced-motion"),"reduce-motion respected");
for(const orientation of ["auto","landscape","portrait"]){
 const card=new Card();
 card.setConfig({theme_mode:"dark",layout_orientation:orientation,show_diagnostics:true});
 card.hass={states:{},themes:{darkMode:true,theme:"test"}};
 assert.equal(card.dataset.orientation,orientation);
 assert(card.shadowRoot.innerHTML.includes('data-orientation="portrait"'),"portrait rules missing");
 assert(card.shadowRoot.innerHTML.includes('data-orientation="landscape"'),"landscape rules missing");
 assert(card.shadowRoot.innerHTML.includes('max-width:800px'),"responsive auto layout missing");
 assert(card.shadowRoot.innerHTML.includes("Alarmes et surveillance"),"alarms missing");
}
const card=new Card();
card.setConfig({});
card.hass={states:{},themes:{darkMode:false,theme:"day"}};
assert.equal(card.dataset.orientation,"auto","default auto");
assert.throws(()=>card.setConfig({layout_orientation:"diagonal"}),/layout_orientation/);
const editor=Card.getConfigElement();
editor.setConfig({type:"custom:pac-synoptique-card",theme_mode:"light",
 layout_style:"clean",show_diagnostics:true,entities:{compressor:"binary_sensor.my_comp"},layout_orientation:"portrait"});
assert(editor.shadowRoot.innerHTML.includes('value="portrait" selected'));
const fn=editor.shadowRoot.listeners.change;
fn({target:{id:"pac-orientation-choice",value:"landscape"}});
const config=editor.events.at(-1).detail.config;
assert.equal(config.layout_orientation,"landscape");
assert.equal(config.theme_mode,"light");
assert.equal(config.layout_style,"clean");
assert.equal(config.entities.compressor,"binary_sensor.my_comp");
fn({target:{id:"pac-orientation-choice",value:"auto"}});
assert.equal(editor.events.at(-1).detail.config.layout_orientation,"auto");
const before=editor.events.length;
fn({target:{id:"pac-orientation-choice",value:"invalid"}});
assert.equal(editor.events.length,before);
assert(!src.includes("hass.callService("),"card must be read-only");
console.log("PASS: CSS-only compact landscape/portrait/auto, 65 entities, editor, animations, themes, read-only");
