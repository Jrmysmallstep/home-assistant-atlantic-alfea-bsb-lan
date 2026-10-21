"use strict";
const fs=require("fs"),vm=require("vm"),path=require("path");
const source=fs.readFileSync(path.join(__dirname,"..","custom_components","atlantic_alfea_controller","www","pac-synoptique-card.js"),"utf8");
class E {
  constructor(){this.dataset={};this.shadowRoot={innerHTML:"",querySelector:()=>null};}
  attachShadow(){return this.shadowRoot;}
}
const custom={};
const context={HTMLElement:E,customElements:{get:k=>custom[k],define:(k,v)=>custom[k]=v},
 window:{customCards:[],matchMedia:()=>({matches:false})},Date,JSON,Object,Intl,Number,String,Array,Math,Set};
vm.runInNewContext(source,context);
const Card=custom["pac-synoptique-card"];
if(!Card)throw Error("Carte non enregistrée");
for(const mode of ["auto","light","dark"]){
 const card=new Card();card.setConfig({theme_mode:mode,show_diagnostics:true});
 card.hass={states:{},themes:{darkMode:false,theme:"Jour"}};
 if(card.dataset.pacTheme!==mode || !card.shadowRoot.innerHTML.includes("Alarmes et surveillance"))throw Error("Mode incorrect "+mode);
 const css=card.shadowRoot.innerHTML;
 for(const item of ["--ha-card-background","--primary-text-color",'data-pac-theme="dark"','data-pac-theme="light"']){
  if(!css.includes(item))throw Error("CSS absent "+item);
 }
 card.hass={states:{},themes:{darkMode:true,theme:"Nuit"}};
 if(card.dataset.pacScheme!==(mode==="auto"?"dark":mode))throw Error("Basculement invalide "+mode);
 console.log("PASS",mode);
}
try{new Card().setConfig({theme_mode:"invalid"});throw Error("Mode invalide accepté");}
catch(err){if(!err.message.includes("theme_mode"))throw err;}
if(source.includes("hass.callService("))throw Error("Lecture seule non respectée");
if(!source.includes("programmedRegime = raw =>") || !source.includes("Programme actif"))throw Error("Programme Confort/Éco non préservé dans les diagnostics");
if(!source.includes("Circulateur en marche") || !source.includes("Circulateur arrêté"))throw Error("États circulateurs absents du synoptique");
