"use strict";
const assert=require("assert");
const fs=require("fs"),vm=require("vm"),path=require("path");
const code=fs.readFileSync(
  path.join(__dirname,"..","custom_components","atlantic_alfea_controller",
    "www","pac-synoptique-card.js"),"utf8"
);
class FakeEvent {
  constructor(type,init){this.type=type;Object.assign(this,init);}
}
class FakeElement {
  constructor() {
    this.dispatched=[];
    this.listeners={};
    this.dataset={};
  }
  attachShadow(){
    this.shadowRoot={
      innerHTML:"",
      listeners:{},
      addEventListener:(name,fn)=>{this.shadowRoot.listeners[name]=fn;},
      querySelector:()=>null
    };
    return this.shadowRoot;
  }
  dispatchEvent(e){this.dispatched.push(e);return true;}
}
const custom={};
const document={createElement:tag=>{assert(custom[tag],"Missing element: "+tag);return new custom[tag]();}};
const globals={
  HTMLElement:FakeElement,CustomEvent:FakeEvent,document,
  customElements:{get:k=>custom[k],define:(k,C)=>{custom[k]=C;}},
  window:{customCards:[],matchMedia:()=>({matches:false})},
  Date,JSON,Object,Intl,Number,String,Array,Math,Set,Boolean
};
vm.runInNewContext(code,globals);
const Card=custom["pac-synoptique-card"];
const Editor=custom["pac-synoptique-card-editor"];
assert(Card&&Editor,"Visual editor registration missing");
assert.strictEqual(Card.getStubConfig().theme_mode,"auto");
assert(!("type" in Card.getStubConfig()),"Stub config should not contain type");
let editor=Card.getConfigElement();
assert(editor instanceof Editor,"getConfigElement must return the editor");
const userConfig={
  type:"custom:pac-synoptique-card",
  title:"Atlantic",
  theme_mode:"dark",
  show_diagnostics:false,
  grid_options:{columns:"full",rows:"auto"},
  entities:{compressor:"binary_sensor.my_compressor"}
};
editor.setConfig(userConfig);
assert(editor.shadowRoot.innerHTML.includes('value="dark" selected'),"Selected dark mode missing");
assert(editor.shadowRoot.innerHTML.includes("Automatique (thème Home Assistant)"));
assert(editor.shadowRoot.innerHTML.includes("Afficher les diagnostics complémentaires"));
const change=editor.shadowRoot.listeners.change;
assert.equal(typeof change,"function");
// Simuler une interaction utilisateur dans la liste déroulante :
change({target:{id:"pac-theme-choice",value:"light"}});
let event=editor.dispatched.at(-1);
assert.equal(event.type,"config-changed");
assert.equal(event.bubbles,true);
assert.equal(event.composed,true);
assert.equal(event.detail.config.theme_mode,"light");
assert.equal(event.detail.config.show_diagnostics,false);
assert.equal(event.detail.config.entities.compressor,userConfig.entities.compressor);
assert.equal(event.detail.config.grid_options.columns,"full");
change({target:{id:"pac-show-diagnostics",checked:true}});
event=editor.dispatched.at(-1);
assert.equal(event.detail.config.show_diagnostics,true);
assert.equal(event.detail.config.theme_mode,"light");
change({target:{id:"pac-theme-choice",value:"auto"}});
assert.equal(editor.dispatched.at(-1).detail.config.theme_mode,"auto");
change({target:{id:"pac-theme-choice",value:"invalid"}});
assert.equal(editor.dispatched.length,3,"Unknown theme should be ignored");
editor.setConfig({type:"custom:pac-synoptique-card"});
assert(editor.shadowRoot.innerHTML.includes('value="auto" selected'));
assert(editor.shadowRoot.innerHTML.includes('type="checkbox" id="pac-show-diagnostics" checked'));
assert(!code.includes("hass.callService("),"card must not operate PAC");
console.log("PASS: Lovelace editor, UI events, defaults, and data preservation");
