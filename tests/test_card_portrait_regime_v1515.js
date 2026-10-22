"use strict";
const assert=require("assert");
const fs=require("fs"),vm=require("vm"),path=require("path");
const source=fs.readFileSync(path.join(__dirname,"..","custom_components","atlantic_alfea_controller","www","pac-synoptique-card.js"),"utf8");
class ElementStub{
  constructor(){this.dataset={};this.events=[]}
  attachShadow(){
    this.shadowRoot={innerHTML:"",addEventListener:()=>{},querySelector:()=>null};
    return this.shadowRoot;
  }
  dispatchEvent(){return true;}
}
const registered={};
vm.runInNewContext(source,{
  HTMLElement:ElementStub,
  customElements:{get:k=>registered[k],define:(k,v)=>registered[k]=v},
  document:{createElement:k=>new registered[k]()},
  window:{customCards:[],matchMedia:()=>({matches:false})},
  Intl,Date,JSON,Object,String,Number,Array,Math,Set,Boolean
});
assert(registered["pac-synoptique-card"]);
for(const orientation of ["auto","portrait","landscape"]){
  const instance=new registered["pac-synoptique-card"]();
  instance.setConfig({layout_orientation:orientation});
  instance.hass={states:{},themes:{darkMode:true,theme:"test"}};
  const html=instance.shadowRoot.innerHTML;
  assert(html.includes("Régime : "),"comfort/eco label must be rendered dynamically");
  assert(html.includes('10112 / 10122'),"native schedule display mapping missing");
  assert(html.includes("portrait mobile sans faux collecteur latéral"),"mobile style marker missing");
  assert(html.includes('data-orientation="portrait"]) .outs:before'),"portrait piping override absent");
  assert(html.includes('data-orientation="auto"]) .outs:before'),"responsive piping override absent");
  assert(html.includes('data-orientation="landscape"]) .schematic'),"landscape rules removed");
}
assert(source.includes("programmedRegime(c.program)"),"native schedule not used");
assert(!source.includes("chip(c.native??'État BSB-LAN indisponible'"),"raw BSB state still shown in circuit");
assert(!source.includes("hass.callService("),"must stay read only");
const count=(source.match(/const FIELDS = \{([\s\S]*?)\n\};/)||[])[1];
assert(count && (count.match(/^\s+[A-Za-z_]\w*\s*:/gm)||[]).length===65,"entity mapping changed");
console.log("PASS: portrait auto/manual, raw BSB moved to diagnostics, native programme shown, landscape retained");
